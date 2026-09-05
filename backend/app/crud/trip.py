from uuid import UUID

from sqlalchemy.orm import Session

from app.models.trip import Trip
from app.models.trip_member import TripMember
from app.core.constants import MemberStatus
from app.models.user import User


def create_trip_row(db: Session, trip: Trip) -> Trip:
    """Add a Trip row to the session. Does not commit."""
    db.add(trip)
    return trip


def create_trip_member_row(
    db: Session,
    member: TripMember,
) -> TripMember:
    """Add a TripMember row to the session. Does not commit."""
    db.add(member)
    return member


def get_trip_by_id(
    db: Session,
    trip_id: UUID,
) -> Trip | None:
    return (
        db.query(Trip)
        .filter(Trip.id == trip_id)
        .first()
    )


def get_trips_for_user(
    db: Session,
    user_id: UUID,
) -> list[Trip]:
    """Return trips where the user is an ACTIVE (joined) member."""
    return (
        db.query(Trip)
        .join(TripMember, TripMember.trip_id == Trip.id)
        .filter(
            TripMember.user_id == user_id,
            TripMember.status == MemberStatus.JOINED.value,
        )
        .all()
    )


def get_pending_invites_for_user(
    db: Session,
    user_id: UUID,
) -> list[Trip]:
    """Return trips where the user has a pending (invited) membership."""
    return (
        db.query(Trip)
        .join(TripMember, TripMember.trip_id == Trip.id)
        .filter(
            TripMember.user_id == user_id,
            TripMember.status == MemberStatus.INVITED.value,
        )
        .all()
    )


def get_trip_member(
    db: Session,
    trip_id: UUID,
    user_id: UUID,
) -> TripMember | None:
    return (
        db.query(TripMember)
        .filter(
            TripMember.trip_id == trip_id,
            TripMember.user_id == user_id,
        )
        .first()
    )


def get_trip_members(
    db: Session,
    trip_id: UUID,
) -> list[TripMember]:
    return (
        db.query(TripMember)
        .filter(TripMember.trip_id == trip_id)
        .all()
    )


def get_user_by_email_for_invite(
    db: Session,
    email: str,
) -> User | None:
    return (
        db.query(User)
        .filter(User.email == email)
        .first()
    )


def update_trip_row(
    db: Session,
    trip: Trip,
) -> Trip:
    """Commit and refresh an updated Trip."""
    db.commit()
    db.refresh(trip)
    return trip


def delete_trip_row(
    db: Session,
    trip: Trip,
) -> None:
    """Delete a Trip row. Does not commit."""
    db.delete(trip)


def delete_trip_member_row(
    db: Session,
    member: TripMember,
) -> None:
    """Delete a TripMember row. Does not commit."""
    db.delete(member)