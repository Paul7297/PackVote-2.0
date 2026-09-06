from uuid import UUID

from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.constants import MemberRole, MemberStatus
from app.models.trip_member import TripMember
from app.models.trip_preference import TripPreference
from app.schemas.trip_preference import (
    TripPreferenceCreate,
    TripPreferenceUpdate,
)

from app.crud.trip import get_trip_by_id, get_trip_member
from app.crud.trip_preference import (
    create_preference_row,
    delete_preference_row,
    get_preference,
    get_preferences_for_trip,
    update_preference_row,
)


def submit_preference(
    db: Session,
    trip_id: UUID,
    user_id: UUID,
    preference_data: TripPreferenceCreate,
) -> TripPreference:
    """
    Submit the current user's survey response.

    Only joined members may submit.
    A member can submit only one response per trip.
    """

    trip = get_trip_by_id(db, trip_id)

    if trip is None:
        raise ValueError("Trip not found")

    member = get_trip_member(db, trip_id, user_id)

    if (
        member is None
        or member.status != MemberStatus.JOINED.value
    ):
        raise PermissionError(
            "You must be an active member of this trip "
            "to submit preferences"
        )

    existing = get_preference(db, trip_id, user_id)

    if existing is not None:
        raise ValueError(
            "You have already submitted preferences for this trip"
        )

    preference = TripPreference(
        trip_id=trip_id,
        user_id=user_id,
        budget_range=preference_data.budget_range.value,
        travel_style=[
            style.value
            for style in preference_data.travel_style
        ],
        preferred_activities=[
            activity.value
            for activity in preference_data.preferred_activities
        ],
        climate_preference=(
            preference_data.climate_preference.value
        ),
        accommodation_pref=(
            preference_data.accommodation_pref.value
        ),
        transport_pref=(
            preference_data.transport_pref.value
        ),
        food_pref=preference_data.food_pref.value,
        travel_priority=(
            preference_data.travel_priority.value
        ),
        notes=preference_data.notes,
    )

    try:
        create_preference_row(db, preference)

        db.commit()
        db.refresh(preference)

        return preference

    except IntegrityError as exc:
        db.rollback()

        constraint_name = getattr(
            getattr(exc, "orig", None),
            "diag",
            None,
        )
        constraint_name = getattr(
            constraint_name,
            "constraint_name",
            None,
        )

        if constraint_name == "uq_trip_preference":
            raise ValueError(
                "You have already submitted preferences "
                "for this trip"
            ) from exc

        raise

    except Exception:
        db.rollback()
        raise


def update_preference(
    db: Session,
    trip_id: UUID,
    user_id: UUID,
    update_data: TripPreferenceUpdate,
) -> TripPreference:
    """
    Partially update the current user's survey response.

    Only joined members may update their own response.
    The preference must already exist.
    """

    trip = get_trip_by_id(db, trip_id)

    if trip is None:
        raise ValueError("Trip not found")

    member = get_trip_member(db, trip_id, user_id)

    if (
        member is None
        or member.status != MemberStatus.JOINED.value
    ):
        raise PermissionError(
            "You must be an active member of this trip "
            "to update preferences"
        )

    existing = get_preference(db, trip_id, user_id)

    if existing is None:
        raise ValueError(
            "No preference submission found. "
            "Submit preferences first."
        )

    update_fields = update_data.model_dump(
        mode="python",
        exclude_unset=True,
    )

    enum_fields = {
        "budget_range",
        "climate_preference",
        "accommodation_pref",
        "transport_pref",
        "food_pref",
        "travel_priority",
    }

    list_enum_fields = {
        "travel_style",
        "preferred_activities",
    }

    effective_updates = {}

    for field, value in update_fields.items():
        if value is None and field != "notes":
            continue

        if field in enum_fields:
            value = value.value
        elif field in list_enum_fields:
            value = [item.value for item in value]

        effective_updates[field] = value

    if not effective_updates:
        return existing

    for field, value in effective_updates.items():
        setattr(existing, field, value)

    try:
        update_preference_row(db, existing)

        db.commit()
        db.refresh(existing)

        return existing

    except Exception:
        db.rollback()
        raise


def delete_preference(
    db: Session,
    trip_id: UUID,
    user_id: UUID,
) -> None:
    """
    Withdraw the current user's survey response.

    Only joined members may delete their own response.
    Deleting the row means the survey is no longer submitted.
    """

    trip = get_trip_by_id(db, trip_id)

    if trip is None:
        raise ValueError("Trip not found")

    member = get_trip_member(db, trip_id, user_id)

    if (
        member is None
        or member.status != MemberStatus.JOINED.value
    ):
        raise PermissionError(
            "You must be an active member of this trip "
            "to delete preferences"
        )

    existing = get_preference(db, trip_id, user_id)

    if existing is None:
        raise ValueError("No preference submission found")

    try:
        delete_preference_row(db, existing)

        db.commit()

    except Exception:
        db.rollback()
        raise


def get_my_preference(
    db: Session,
    trip_id: UUID,
    user_id: UUID,
) -> TripPreference | None:
    """
    Return the current user's preference for a trip.

    Only joined members may access the preference.
    """

    trip = get_trip_by_id(db, trip_id)

    if trip is None:
        raise ValueError("Trip not found")

    member = get_trip_member(db, trip_id, user_id)

    if (
        member is None
        or member.status != MemberStatus.JOINED.value
    ):
        raise PermissionError(
            "You must be an active member of this trip "
            "to view preferences"
        )

    return get_preference(db, trip_id, user_id)


def get_all_trip_preferences(
    db: Session,
    trip_id: UUID,
    user_id: UUID,
) -> list[TripPreference]:
    """
    Return all submitted preferences for a trip.

    Only the trip organizer may view individual responses.
    """

    trip = get_trip_by_id(db, trip_id)

    if trip is None:
        raise ValueError("Trip not found")

    member = get_trip_member(db, trip_id, user_id)

    if (
        member is None
        or member.status != MemberStatus.JOINED.value
        or member.role != MemberRole.ORGANIZER.value
    ):
        raise PermissionError(
            "Only the trip organizer may view member preferences"
        )

    return get_preferences_for_trip(db, trip_id)


def get_completion_status(
    db: Session,
    trip_id: UUID,
    user_id: UUID,
) -> dict:
    """
    Return survey completion information for a trip.

    Only joined members may view completion status.
    """

    trip = get_trip_by_id(db, trip_id)

    if trip is None:
        raise ValueError("Trip not found")

    member = get_trip_member(db, trip_id, user_id)

    if (
        member is None
        or member.status != MemberStatus.JOINED.value
    ):
        raise PermissionError(
            "You must be an active member of this trip "
            "to view completion status"
        )

    total_count = (
        db.query(func.count(TripMember.id))
        .filter(
            TripMember.trip_id == trip_id,
            TripMember.status == MemberStatus.JOINED.value,
        )
        .scalar()
        or 0
    )

    submitted_count = (
        db.query(TripPreference)
        .join(
            TripMember,
            TripMember.user_id == TripPreference.user_id,
        )
        .filter(
            TripPreference.trip_id == trip_id,
            TripMember.trip_id == trip_id,
            TripMember.status == MemberStatus.JOINED.value,
        )
        .count()
    )

    return {
        "submitted": submitted_count,
        "total": total_count,
        "complete": (
            submitted_count >= total_count
            and total_count > 0
        ),
    }