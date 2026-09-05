from uuid import UUID

from sqlalchemy.orm import Session

from app.models.trip import Trip
from app.models.trip_member import TripMember
from app.schemas.trip import TripCreate, TripUpdate
from app.core.constants import MemberRole, MemberStatus

from app.crud.trip import (
    create_trip_row,
    create_trip_member_row,
    get_trip_by_id,
    get_trips_for_user,
    get_trip_member,
    get_trip_members,
    delete_trip_row,
    delete_trip_member_row,
)


def create_trip(
    db: Session,
    trip_data: TripCreate,
    organizer_id: UUID,
) -> Trip:
    """
    Create a Trip and its organizer TripMember
    in a single atomic transaction.
    """

    try:
        trip = Trip(
            name=trip_data.name,
            organizer_id=organizer_id,
            description=trip_data.description,
            budget_min=trip_data.budget_min,
            budget_max=trip_data.budget_max,
            start_date=trip_data.start_date,
            end_date=trip_data.end_date,
        )

        create_trip_row(db, trip)

        # Assign trip.id without committing
        db.flush()

        member = TripMember(
            trip_id=trip.id,
            user_id=organizer_id,
            role=MemberRole.ORGANIZER.value,
            status=MemberStatus.JOINED.value,
        )

        create_trip_member_row(db, member)

        db.commit()
        db.refresh(trip)

        return trip

    except Exception:
        db.rollback()
        raise


def get_user_trips(
    db: Session,
    user_id: UUID,
) -> list[Trip]:
    return get_trips_for_user(db, user_id)


def get_trip_or_404(
    db: Session,
    trip_id: UUID,
) -> Trip:
    trip = get_trip_by_id(db, trip_id)

    if trip is None:
        raise ValueError("Trip not found")

    return trip


def ensure_trip_member(
    db: Session,
    trip_id: UUID,
    user_id: UUID,
) -> TripMember:
    """
    Ensure that the user is an ACTIVE (joined) member of the trip.
    A row existing is not enough — invited/declined/left members
    must not pass this check.
    """

    member = get_trip_member(
        db,
        trip_id,
        user_id,
    )

    if member is None or member.status != MemberStatus.JOINED.value:
        raise PermissionError(
            "You are not an active member of this trip"
        )

    return member


def update_trip(
    db: Session,
    trip: Trip,
    update_data: TripUpdate,
) -> Trip:
    """
    Update only fields provided by the user.
    """

    try:
        update_fields = update_data.model_dump(
            exclude_unset=True
        )

        for field, value in update_fields.items():
            setattr(trip, field, value)

        db.commit()
        db.refresh(trip)

        return trip

    except Exception:
        db.rollback()
        raise


def delete_trip(
    db: Session,
    trip: Trip,
) -> None:
    """
    Delete a trip and all its TripMember rows in one
    atomic transaction.

    db.flush() forces the member deletes to be sent to
    Postgres before the trip delete is issued. Without it,
    SQLAlchemy has no relationship() between Trip and
    TripMember to infer the correct delete order, and may
    send the trip DELETE first — causing a foreign key
    violation even though the Python code deletes members
    first.
    """

    try:
        members = get_trip_members(db, trip.id)

        for member in members:
            db.delete(member)

        db.flush()

        db.delete(trip)
        db.commit()

    except Exception:
        db.rollback()
        raise