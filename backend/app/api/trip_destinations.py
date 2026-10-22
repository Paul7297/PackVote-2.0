from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.database.database import get_db
from app.models.user import User
from app.schemas.trip_destination import (
    ConfirmPlaceRequest,
    TripDestinationCreate,
    TripDestinationResponse,
)
from app.services.trip_destination_service import (
    add_candidate,
    add_confirmed_place_candidate,
    finalize_candidate,
    list_candidates,
    reject_candidate,
)

router = APIRouter(
    prefix="/trips/{trip_id}/destinations",
    tags=["Trip Destinations"],
)

@router.post(
    "/confirm",
    response_model=TripDestinationResponse,
    status_code=status.HTTP_201_CREATED,
)
def confirm_trip_destination(
    trip_id: UUID,
    body: ConfirmPlaceRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return add_confirmed_place_candidate(
            db=db,
            trip_id=trip_id,
            user_id=current_user.id,
            external_place_id=body.external_place_id,
        )
    except PermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc
    except ValueError as exc:
        message = str(exc)
        code = (
            status.HTTP_404_NOT_FOUND
            if message == "Trip not found"
            else status.HTTP_400_BAD_REQUEST
        )
        raise HTTPException(
            status_code=code,
            detail=message,
        ) from exc

@router.post(
    "",
    response_model=TripDestinationResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_trip_destination(
    trip_id: UUID,
    candidate_data: TripDestinationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Add a destination from the catalog as a candidate for a trip.
    Only the trip organizer can add candidates.
    """
    try:
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


@router.get(
    "",
    response_model=list[TripDestinationResponse],
    status_code=status.HTTP_200_OK,
)
def get_trip_destinations(
    trip_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List all destination candidates for a trip.
    Any joined trip member can view candidates.
    """
    try:
        return list_candidates(
            db=db,
            trip_id=trip_id,
            user_id=current_user.id,
        )

    except PermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.post(
    "/{trip_destination_id}/finalize",
    response_model=TripDestinationResponse,
    status_code=status.HTTP_200_OK,
)
def finalize_trip_destination(
    trip_id: UUID,
    trip_destination_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Finalize a destination candidate.
    Only the trip organizer can finalize a candidate.
    """
    try:
        return finalize_candidate(
            db=db,
            trip_id=trip_id,
            trip_destination_id=trip_destination_id,
            user_id=current_user.id,
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


@router.post(
    "/{trip_destination_id}/reject",
    response_model=TripDestinationResponse,
    status_code=status.HTTP_200_OK,
)
def reject_trip_destination(
    trip_id: UUID,
    trip_destination_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Reject a destination candidate.
    Only the trip organizer can reject a candidate.
    """
    try:
        return reject_candidate(
            db=db,
            trip_id=trip_id,
            trip_destination_id=trip_destination_id,
            user_id=current_user.id,
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
