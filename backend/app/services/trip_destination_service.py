from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.constants import (
    CandidateSource,
    DestinationStatus,
    MemberStatus,
    TripStatus,
)
from app.crud.destination import (
    create_destination_row,
    get_destination_by_external_identity,
    get_destination_by_id,
)
from app.crud.trip import get_trip_by_id, get_trip_member
from app.crud.trip_destination import (
    create_trip_destination_row,
    get_candidates_for_trip,
    get_trip_destination,
    get_trip_destination_by_id,
    update_trip_destination_row,
)
from app.models.trip_destination import TripDestination
from app.schemas.trip_destination import TripDestinationCreate


from app.models.destination import Destination
from app.schemas.place import PlaceSearchResult

from app.services.place_service import get_place_by_id


def add_candidate(
    db: Session,
    trip_id: UUID,
    user_id: UUID,
    candidate_data: TripDestinationCreate,
) -> TripDestination:
    """
    Add a destination from the catalog as a candidate for a trip.

    Only the organizer can manually add candidates.
    """

    trip = get_trip_by_id(db, trip_id)

    if trip is None:
        raise ValueError("Trip not found")

    if trip.organizer_id != user_id:
        raise PermissionError(
            "Only the organizer can add destination candidates"
        )

    destination = get_destination_by_id(
        db,
        candidate_data.destination_id,
    )

    if destination is None:
        raise ValueError("Destination not found in catalog")

    existing = get_trip_destination(
        db,
        trip_id,
        candidate_data.destination_id,
    )

    if existing is not None:
        raise ValueError(
            "This destination has already been added as a candidate for this trip"
        )

    trip_destination = TripDestination(
        trip_id=trip_id,
        destination_id=candidate_data.destination_id,
        added_by=user_id,
        source=candidate_data.source.value if hasattr(candidate_data.source, "value") else candidate_data.source,
        status=DestinationStatus.PROPOSED.value,
    )

    try:
        create_trip_destination_row(db, trip_destination)
        db.commit()
        db.refresh(trip_destination)

        return trip_destination

    except IntegrityError as exc:
        db.rollback()

        if getattr(exc.orig, "diag", None) is not None:
            constraint_name = exc.orig.diag.constraint_name

            if constraint_name == "uq_trip_destination":
                raise ValueError(
                    "This destination has already been added as a candidate "
                    "for this trip"
                ) from exc

        raise

    except Exception:
        db.rollback()
        raise

def add_confirmed_place_candidate(
    db: Session,
    trip_id: UUID,
    user_id: UUID,
    external_place_id: str,
) -> TripDestination:
    """Verify a Geoapify place, then create or reuse and link it."""

    trip = get_trip_by_id(db, trip_id)
    if trip is None:
        raise ValueError("Trip not found")

    if trip.organizer_id != user_id:
        raise PermissionError(
            "Only the organizer can add destination candidates"
        )

    # Get authoritative place details from Geoapify, not from client fields.
    place = get_place_by_id(external_place_id)
    if not place.external_place_id:
        raise ValueError("Geoapify result is missing its place ID")

    provider_name = "geoapify"
    destination = get_destination_by_external_identity(
        db,
        provider_name=provider_name,
        external_place_id=place.external_place_id,
    )

    try:
        if destination is None:
            destination = Destination(
                name=place.name,
                country=place.country,
                region=place.region,
                latitude=place.latitude,
                longitude=place.longitude,
                external_place_id=place.external_place_id,
                provider_name=provider_name,
            )
            create_destination_row(db, destination)
            db.flush()  # Assign the destination ID before querying its trip link.

        existing = get_trip_destination(db, trip_id, destination.id)
        if existing is not None:
            raise ValueError(
                "This destination has already been added as a candidate for this trip"
            )

        trip_destination = TripDestination(
            trip_id=trip_id,
            destination_id=destination.id,
            added_by=user_id,
            source=CandidateSource.MANUAL.value,
            status=DestinationStatus.PROPOSED.value,
        )
        create_trip_destination_row(db, trip_destination)
        db.commit()
        db.refresh(trip_destination)
        return trip_destination

    except Exception:
        db.rollback()
        raise

def list_candidates(
    db: Session,
    trip_id: UUID,
    user_id: UUID,
) -> list[TripDestination]:
    """
    List all destination candidates for a trip.

    Any joined trip member can view the candidate list.
    """

    trip = get_trip_by_id(db, trip_id)

    if trip is None:
        raise ValueError("Trip not found")

    member = get_trip_member(
        db,
        trip_id,
        user_id,
    )

    if (
        member is None
        or member.status != MemberStatus.JOINED.value
    ):
        raise PermissionError(
            "You must be an active member of this trip to view candidates"
        )

    return get_candidates_for_trip(db, trip_id)


def finalize_candidate(
    db: Session,
    trip_id: UUID,
    trip_destination_id: UUID,
    user_id: UUID,
) -> TripDestination:
    """
    Mark one proposed candidate as the finalized destination.

    Only the organizer may finalize a candidate.
    """

    trip = get_trip_by_id(db, trip_id)

    if trip is None:
        raise ValueError("Trip not found")

    if trip.organizer_id != user_id:
        raise PermissionError(
            "Only the organizer can finalize a destination"
        )

    candidate = get_trip_destination_by_id(
        db,
        trip_destination_id,
    )

    if (
        candidate is None
        or candidate.trip_id != trip_id
    ):
        raise ValueError("Candidate not found for this trip")

    if candidate.status == DestinationStatus.REJECTED.value:
        raise ValueError("A rejected candidate cannot be finalized")

    if candidate.status == DestinationStatus.FINALIZED.value:
        return candidate

    existing_finalized = [
        item
        for item in get_candidates_for_trip(db, trip_id)
        if (
            item.id != candidate.id
            and item.status == DestinationStatus.FINALIZED.value
        )
    ]

    if existing_finalized:
        raise ValueError(
            "This trip already has a finalized destination"
        )

    candidate.status = DestinationStatus.FINALIZED.value
    trip.status = TripStatus.FINALIZED.value

    try:
        update_trip_destination_row(db, candidate)

        # Mark other proposed candidates as rejected so the decision is finalized
        for item in get_candidates_for_trip(db, trip_id):
            if item.id != candidate.id and item.status == DestinationStatus.PROPOSED.value:
                item.status = DestinationStatus.REJECTED.value
                update_trip_destination_row(db, item)

        db.commit()
        db.refresh(candidate)

        return candidate

    except Exception:
        db.rollback()
        raise


def reject_candidate(
    db: Session,
    trip_id: UUID,
    trip_destination_id: UUID,
    user_id: UUID,
) -> TripDestination:
    """
    Mark a proposed candidate as rejected.

    Only the organizer may reject a candidate.
    """

    trip = get_trip_by_id(db, trip_id)

    if trip is None:
        raise ValueError("Trip not found")

    if trip.organizer_id != user_id:
        raise PermissionError(
            "Only the organizer can reject a destination"
        )

    candidate = get_trip_destination_by_id(
        db,
        trip_destination_id,
    )

    if (
        candidate is None
        or candidate.trip_id != trip_id
    ):
        raise ValueError("Candidate not found for this trip")

    if candidate.status == DestinationStatus.FINALIZED.value:
        raise ValueError(
            "A finalized destination cannot be rejected"
        )

    if candidate.status == DestinationStatus.REJECTED.value:
        return candidate

    candidate.status = DestinationStatus.REJECTED.value

    try:
        update_trip_destination_row(db, candidate)
        db.commit()
        db.refresh(candidate)

        return candidate

    except Exception:
        db.rollback()
        raise
