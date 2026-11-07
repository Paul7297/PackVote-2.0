
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.constants import MemberStatus
from app.core.deps import get_current_user
from app.crud.trip import get_trip_by_id, get_trip_member
from app.database.database import get_db
from app.models.user import User
from app.schemas.recommendation import RecommendationItem
from app.services.recommendation_service import recommend_destinations

from app.models.destination import Destination
from app.services.weather_service import get_destination_weather
from app.core.constants import CandidateSource
from app.schemas.trip_destination import TripDestinationCreate, TripDestinationResponse
from app.services.trip_destination_service import add_candidate


router = APIRouter(
    prefix="/trips/{trip_id}/recommendations",
    tags=["Trip Recommendations"],
)


@router.get(
    "",
    response_model=list[RecommendationItem],
)
def get_recommendations(
    trip_id: UUID,
    origin_city: str = "delhi",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return ranked destinations for a joined trip member."""

    trip = get_trip_by_id(db, trip_id)

    if trip is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trip not found",
        )

    member = get_trip_member(db, trip_id, current_user.id)

    if member is None or member.status != MemberStatus.JOINED.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You must be a joined member of this trip",
        )

    try:
        return recommend_destinations(db, trip_id, origin_city=origin_city)

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.get("/{destination_id}/weather")
def get_recommendation_weather(
    trip_id: UUID,
    destination_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return weather forecast information for a trip destination."""

    trip = get_trip_by_id(db, trip_id)

    if trip is None:
        raise HTTPException(
            status_code=404,
            detail="Trip not found",
        )

    member = get_trip_member(db, trip_id, current_user.id)

    if member is None or member.status != MemberStatus.JOINED.value:
        raise HTTPException(
            status_code=403,
            detail="You must be a joined member of this trip",
        )

    destination = (
        db.query(Destination)
        .filter(Destination.id == destination_id)
        .first()
    )

    if destination is None:
        raise HTTPException(
            status_code=404,
            detail="Destination not found",
        )

    try:
        return get_destination_weather(trip, destination)
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc
    except RuntimeError as exc:
        raise HTTPException(
            status_code=502,
            detail=str(exc),
        ) from exc


@router.post(
    "/{destination_id}/promote",
    response_model=TripDestinationResponse,
    status_code=status.HTTP_201_CREATED,
)
def promote_recommendation_candidate(
    trip_id: UUID,
    destination_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Promote an ML recommended destination into a trip candidate with source=ml.
    Only the trip organizer can promote candidates.
    """
    try:
        candidate_data = TripDestinationCreate(
            destination_id=destination_id,
            source=CandidateSource.ML,
        )
        return add_candidate(
            db=db,
            trip_id=trip_id,
            user_id=current_user.id,
            candidate_data=candidate_data,
        )
    except PermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
