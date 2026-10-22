from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.destination import Destination
from app.models.trip_destination import TripDestination


def create_destination_row(
    db: Session,
    destination: Destination,
) -> Destination:
    """Add a Destination row to the session. Does not commit."""
    db.add(destination)
    return destination


def get_destination_by_id(
    db: Session,
    destination_id: UUID,
) -> Destination | None:
    return (
        db.query(Destination)
        .filter(Destination.id == destination_id)
        .first()
    )


def get_all_destinations(
    db: Session,
) -> list[Destination]:
    return db.query(Destination).all()


def get_destination_by_identity(
    db: Session,
    name: str,
    country: str | None,
    region: str | None,
) -> Destination | None:
    return (
        db.query(Destination)
        .filter(
            Destination.name == name,
            Destination.country == country,
            Destination.region == region,
        )
        .first()
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


def update_destination_row(
    db: Session,
    destination: Destination,
) -> Destination:
    """Add changes to the session. Does not commit."""
    db.add(destination)
    return destination


def delete_destination_row(
    db: Session,
    destination: Destination,
) -> None:
    """Delete a Destination row. Does not commit."""
    db.delete(destination)

def get_destination_by_external_identity(
    db: Session,
    provider_name: str,
    external_place_id: str,
) -> Destination | None:
    return (
        db.query(Destination)
        .filter(
            Destination.provider_name == provider_name,
            Destination.external_place_id == external_place_id,
        )
        .first()
    )
