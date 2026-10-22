from uuid import UUID
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.trip_destination import TripDestination


def create_trip_destination_row(
    db: Session,
    trip_destination: TripDestination,
) -> TripDestination:
    """Add a TripDestination row to the session. Does not commit."""
    db.add(trip_destination)
    return trip_destination


def get_trip_destination_by_id(
    db: Session,
    trip_destination_id: UUID,
) -> TripDestination | None:
    return (
        db.query(TripDestination)
        .filter(TripDestination.id == trip_destination_id)
        .first()
    )


def get_trip_destination(
    db: Session,
    trip_id: UUID,
    destination_id: UUID,
) -> TripDestination | None:
    return (
        db.query(TripDestination)
        .filter(
            TripDestination.trip_id == trip_id,
            TripDestination.destination_id == destination_id,
        )
        .first()
    )


def get_candidates_for_trip(
    db: Session,
    trip_id: UUID,
) -> list[TripDestination]:
    return (
        db.query(TripDestination)
        .filter(TripDestination.trip_id == trip_id)
        .all()
    )


def count_trip_destinations_for_destination(
    db: Session,
    destination_id: UUID,
) -> int:
    return (
        db.query(func.count(TripDestination.id))
        .filter(TripDestination.destination_id == destination_id)
        .scalar()
        or 0
    )


def update_trip_destination_row(
    db: Session,
    trip_destination: TripDestination,
) -> TripDestination:
    """Add changes to the session. Does not commit."""
    db.add(trip_destination)
    return trip_destination


def delete_trip_destination_row(
    db: Session,
    trip_destination: TripDestination,
) -> None:
    """Delete a TripDestination row. Does not commit."""
    db.delete(trip_destination)