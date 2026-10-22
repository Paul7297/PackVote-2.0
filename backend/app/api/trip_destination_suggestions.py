from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.database.database import get_db
from app.models.user import User
from app.schemas.trip_destination_suggestion import (
    TripDestinationSuggestionCreate,
    TripDestinationSuggestionResponse,
    TripDestinationSuggestionReview,
)
from app.services.trip_destination_suggestion_service import (
    DestinationConflict,
    list_trip_destination_suggestions,
    review_trip_destination_suggestion,
    search_trip_destinations,
    suggest_trip_destination,
)
from app.services.place_service import get_place_by_id

router = APIRouter(
    prefix="/trips/{trip_id}/destinations",
    tags=["Destination Suggestions"],
)


def _raise(exc: Exception):
    if isinstance(exc, PermissionError):
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    if isinstance(exc, DestinationConflict):
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    if isinstance(exc, ValueError):
        code = 404 if str(exc) in {"Trip not found", "Destination suggestion not found"} else 400
        raise HTTPException(status_code=code, detail=str(exc)) from exc
    raise exc


@router.get("/search")
def search_destinations(
    trip_id: UUID,
    q: str = Query(..., min_length=2, max_length=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return [
            place.model_dump()
            for place in search_trip_destinations(
                db, trip_id, current_user.id, q.strip()
            )
        ]
    except PermissionError as exc:
        _raise(exc)
    except ValueError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.post(
    "/suggestions",
    response_model=TripDestinationSuggestionResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_suggestion(
    trip_id: UUID,
    body: TripDestinationSuggestionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return suggest_trip_destination(
            db, trip_id, current_user.id, body.external_place_id
        )
    except (PermissionError, ValueError, DestinationConflict) as exc:
        _raise(exc)


@router.get(
    "/suggestions",
    response_model=list[TripDestinationSuggestionResponse],
)
def get_suggestions(
    trip_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return list_trip_destination_suggestions(db, trip_id, current_user.id)
    except (PermissionError, ValueError) as exc:
        _raise(exc)


@router.patch(
    "/suggestions/{suggestion_id}/review",
    response_model=TripDestinationSuggestionResponse,
)
def review_suggestion(
    trip_id: UUID,
    suggestion_id: UUID,
    body: TripDestinationSuggestionReview,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return review_trip_destination_suggestion(
            db,
            trip_id,
            current_user.id,
            suggestion_id,
            body.status,
        )
    except (PermissionError, ValueError, DestinationConflict) as exc:
        _raise(exc)
