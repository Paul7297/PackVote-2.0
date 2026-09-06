from uuid import UUID

from sqlalchemy.orm import Session

from app.models.trip_preference import TripPreference


def create_preference_row(
    db: Session,
    preference: TripPreference,
) -> TripPreference:
    """Add a TripPreference row to the session without committing."""
    db.add(preference)
    return preference


def get_preference(
    db: Session,
    trip_id: UUID,
    user_id: UUID,
) -> TripPreference | None:
    return (
        db.query(TripPreference)
        .filter(
            TripPreference.trip_id == trip_id,
            TripPreference.user_id == user_id,
        )
        .first()
    )


def get_preferences_for_trip(
    db: Session,
    trip_id: UUID,
) -> list[TripPreference]:
    return (
        db.query(TripPreference)
        .filter(TripPreference.trip_id == trip_id)
        .all()
    )


def count_preferences_for_trip(
    db: Session,
    trip_id: UUID,
) -> int:
    return (
        db.query(TripPreference)
        .filter(TripPreference.trip_id == trip_id)
        .count()
    )


def update_preference_row(
    db: Session,
    preference: TripPreference,
) -> TripPreference:
    """Add an existing TripPreference object to the session."""
    db.add(preference)
    return preference


def delete_preference_row(
    db: Session,
    preference: TripPreference,
) -> None:
    """Mark an existing TripPreference row for deletion."""
    db.delete(preference)