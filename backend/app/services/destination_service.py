from uuid import UUID

from sqlalchemy.orm import Session

from app.models.destination import Destination
from app.schemas.destination import DestinationCreate, DestinationUpdate

from app.crud.destination import (
    create_destination_row,
    get_destination_by_id,
    get_all_destinations,
    get_destination_by_identity,
    count_trip_destinations_for_destination,
    update_destination_row,
    delete_destination_row,
)


def create_destination(
    db: Session,
    destination_data: DestinationCreate,
) -> Destination:
    """
    Create a new catalog destination.

    Prevents duplicate entries with the same
    name, country, and region.
    """
    existing = get_destination_by_identity(
        db,
        name=destination_data.name,
        country=destination_data.country,
        region=destination_data.region,
    )

    if existing is not None:
        raise ValueError(
            "A destination with this name, country, and region already exists"
        )

    destination = Destination(
        **destination_data.model_dump(mode="json")
    )

    try:
        create_destination_row(db, destination)
        db.commit()
        db.refresh(destination)
        return destination

    except Exception:
        db.rollback()
        raise


def get_destination(
    db: Session,
    destination_id: UUID,
) -> Destination:
    destination = get_destination_by_id(db, destination_id)

    if destination is None:
        raise ValueError("Destination not found")

    return destination


def list_destinations(
    db: Session,
) -> list[Destination]:
    return get_all_destinations(db)


def update_destination(
    db: Session,
    destination_id: UUID,
    update_data: DestinationUpdate,
) -> Destination:
    destination = get_destination_by_id(db, destination_id)

    if destination is None:
        raise ValueError("Destination not found")

    update_fields = update_data.model_dump(
        mode="json",
        exclude_unset=True,
    )

    # Check for duplicate identity when identity fields are changed.
    identity_fields = {"name", "country", "region"}

    if identity_fields.intersection(update_fields):
        new_name = update_fields.get("name", destination.name)
        new_country = update_fields.get("country", destination.country)
        new_region = update_fields.get("region", destination.region)

        existing = get_destination_by_identity(
            db,
            name=new_name,
            country=new_country,
            region=new_region,
        )

        if existing is not None and existing.id != destination.id:
            raise ValueError(
                "A destination with this name, country, and region already exists"
            )

    for field, value in update_fields.items():
        setattr(destination, field, value)

    try:
        update_destination_row(db, destination)
        db.commit()
        db.refresh(destination)
        return destination

    except Exception:
        db.rollback()
        raise


def delete_destination(
    db: Session,
    destination_id: UUID,
) -> None:
    destination = get_destination_by_id(db, destination_id)

    if destination is None:
        raise ValueError("Destination not found")

    usage_count = count_trip_destinations_for_destination(
        db,
        destination_id,
    )

    if usage_count > 0:
        raise ValueError(
            f"Cannot delete: this destination is used as a candidate "
            f"in {usage_count} trip(s)"
        )

    try:
        delete_destination_row(db, destination)
        db.commit()

    except Exception:
        db.rollback()
        raise