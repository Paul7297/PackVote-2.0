from uuid import UUID


from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.constants import CandidateSource, DestinationStatus, MemberStatus
from app.crud.destination import (
    create_destination_row,
    get_destination_by_external_identity,
)
from app.crud.trip import get_trip_by_id, get_trip_member
from app.crud.trip_destination import (
    create_trip_destination_row,
    get_trip_destination,
)
from app.models.destination import Destination
from app.models.trip_destination import TripDestination
from app.models.trip_destination_suggestion import TripDestinationSuggestion
from app.services.place_service import get_place_by_id


class DestinationConflict(Exception):
    pass


def _get_member_trip(db: Session, trip_id: UUID, user_id: UUID):
    trip = get_trip_by_id(db, trip_id)
    if trip is None:
        raise ValueError("Trip not found")
    member = get_trip_member(db, trip_id, user_id)
    if member is None or member.status != MemberStatus.JOINED.value:
        raise PermissionError("You must be a joined member of this trip")
    return trip


def search_trip_destinations(
    db: Session,
    trip_id: UUID,
    user_id: UUID,
    query: str,
):
    _get_member_trip(db, trip_id, user_id)
    from app.services.place_service import search_places

    return search_places(query=query, limit=10)


def suggest_trip_destination(
    db: Session,
    trip_id: UUID,
    user_id: UUID,
    external_place_id: str,
) -> TripDestinationSuggestion:
    _get_member_trip(db, trip_id, user_id)
    place = get_place_by_id(external_place_id)

    if not (place.external_place_id or "").strip():
        raise ValueError("Geoapify returned a place without a valid place ID")
    if place.latitude is None or place.longitude is None:
        raise ValueError("Geoapify returned incomplete destination details")

    suggestion = TripDestinationSuggestion(
        trip_id=trip_id,
        suggested_by=user_id,
        external_place_id=place.external_place_id,
        name=place.name,
        country=place.country,
        region=place.region,
        latitude=place.latitude,
        longitude=place.longitude,
        status="pending",
    )
    try:
        db.add(suggestion)
        db.commit()
        db.refresh(suggestion)
        return suggestion
    except IntegrityError as exc:
        db.rollback()
        if "uq_trip_destination_suggestion_place" in str(exc) or (
            "UNIQUE constraint failed: trip_destination_suggestions.trip_id"
            in str(exc)
        ):
            raise DestinationConflict(
                "This destination has already been suggested for this trip"
            ) from exc
        raise
    except Exception:
        db.rollback()
        raise


def list_trip_destination_suggestions(
    db: Session,
    trip_id: UUID,
    user_id: UUID,
) -> list[TripDestinationSuggestion]:
    _get_member_trip(db, trip_id, user_id)
    return (
        db.query(TripDestinationSuggestion)
        .filter(TripDestinationSuggestion.trip_id == trip_id)
        .order_by(TripDestinationSuggestion.created_at.desc())
        .all()
    )


def review_trip_destination_suggestion(
    db: Session,
    trip_id: UUID,
    user_id: UUID,
    suggestion_id: UUID,
    decision: str,
) -> TripDestinationSuggestion:
    trip = get_trip_by_id(db, trip_id)
    if trip is None:
        raise ValueError("Trip not found")
    if trip.organizer_id != user_id:
        raise PermissionError("Only the trip organizer can review suggestions")
    suggestion = (
        db.query(TripDestinationSuggestion)
        .filter(
            TripDestinationSuggestion.id == suggestion_id,
            TripDestinationSuggestion.trip_id == trip_id,
        )
        .with_for_update()
        .first()
    )
    if suggestion is None:
        raise ValueError("Destination suggestion not found")
    if suggestion.status != "pending":
        raise DestinationConflict("This destination suggestion was already reviewed")

    try:
        if decision == "approved":
            place = get_place_by_id(suggestion.external_place_id)

            if not (place.external_place_id or "").strip():
                raise ValueError("Geoapify returned a place without a valid place ID")
            destination = get_destination_by_external_identity(
                db,
                provider_name="geoapify",
                external_place_id=place.external_place_id,
            )
            if destination is None:
                destination = Destination(
                    name=place.name,
                    country=place.country,
                    region=place.region,
                    latitude=place.latitude,
                    longitude=place.longitude,
                    external_place_id=place.external_place_id,
                    provider_name="geoapify",
                )
                create_destination_row(db, destination)
                db.flush()
            if get_trip_destination(db, trip_id, destination.id) is not None:
                raise DestinationConflict(
                    "This destination is already a candidate for the trip"
                )
            candidate = TripDestination(
                trip_id=trip_id,
                destination_id=destination.id,
                added_by=suggestion.suggested_by,
                source=CandidateSource.MANUAL.value,
                status=DestinationStatus.PROPOSED.value,
            )
            create_trip_destination_row(db, candidate)
            db.flush()
            suggestion.trip_destination_id = candidate.id
        suggestion.status = decision
        db.commit()
        db.refresh(suggestion)
        return suggestion
    except Exception:
        db.rollback()
        raise
