from uuid import UUID

from sqlalchemy.orm import Session

from app.models.trip import Trip
from app.models.trip_member import TripMember
from app.schemas.trip import TripCreate, TripUpdate, TripInviteRequest
from app.core.constants import MemberRole, MemberStatus

from app.crud.trip import (
    create_trip_row,
    create_trip_member_row,
    get_trip_by_id,
    get_trips_for_user,
    get_pending_invites_for_user,
    get_trip_member,
    get_trip_members as get_trip_members_crud,
    get_user_by_email_for_invite,
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

def get_trip_members(
    db: Session,
    trip_id: UUID,
) -> list[TripMember]:
    return get_trip_members_crud(db, trip_id)

def get_user_trips(
    db: Session,
    user_id: UUID,
) -> list[Trip]:
    return get_trips_for_user(db, user_id)


def get_user_invites(
    db: Session,
    user_id: UUID,
) -> list[Trip]:
    return get_pending_invites_for_user(db, user_id)


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

    member = get_trip_member(db, trip_id, user_id)

    if member is None or member.status != MemberStatus.JOINED.value:
        raise PermissionError("You are not an active member of this trip")

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
        update_fields = update_data.model_dump(exclude_unset=True)

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


def invite_member(
    db: Session,
    trip: Trip,
    invite_data: TripInviteRequest,
    inviter_id: UUID,
) -> TripMember:
    if trip.organizer_id != inviter_id:
        raise PermissionError(
            "Only the organizer can invite members"
        )

    invitee = get_user_by_email_for_invite(
        db,
        str(invite_data.email).lower().strip(),
    )

    if invitee is None:
        raise ValueError(
            "No user found with that email"
        )

    existing = get_trip_member(
        db,
        trip.id,
        invitee.id,
    )

    if existing is not None:
        if existing.status in (
            MemberStatus.INVITED.value,
            MemberStatus.JOINED.value,
        ):
            raise ValueError(
                "This user is already invited or a member of this trip"
            )

        existing.status = MemberStatus.INVITED.value
        existing.role = MemberRole.MEMBER.value

        try:
            db.commit()
            db.refresh(existing)
            return existing
        except Exception:
            db.rollback()
            raise

    member = TripMember(
        trip_id=trip.id,
        user_id=invitee.id,
        role=MemberRole.MEMBER.value,
        status=MemberStatus.INVITED.value,
    )

    create_trip_member_row(db, member)

    try:
        db.commit()
        db.refresh(member)
        return member
    except Exception:
        db.rollback()
        raise


def respond_to_invite(
    db: Session,
    trip_id: UUID,
    user_id: UUID,
    accept: bool,
) -> TripMember:
    member = get_trip_member(db, trip_id, user_id)

    if member is None or member.status != MemberStatus.INVITED.value:
        raise ValueError("No pending invite found for this trip")

    member.status = MemberStatus.JOINED.value if accept else MemberStatus.DECLINED.value

    try:
        db.commit()
        db.refresh(member)
        return member
    except Exception:
        db.rollback()
        raise


def leave_trip(
    db: Session,
    trip: Trip,
    user_id: UUID,
) -> TripMember:
    if trip.organizer_id == user_id:
        raise ValueError("The organizer cannot leave their own trip")

    member = get_trip_member(db, trip.id, user_id)

    if member is None or member.status != MemberStatus.JOINED.value:
        raise ValueError("You are not an active member of this trip")

    member.status = MemberStatus.LEFT.value

    try:
        db.commit()
        db.refresh(member)
        return member
    except Exception:
        db.rollback()
        raise