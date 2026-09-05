from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.trip import TripCreate, TripUpdate, TripResponse
from app.services.trip_service import (
    create_trip,
    get_user_trips,
    get_trip_or_404,
    ensure_trip_member,
    update_trip,
    delete_trip,
)

router = APIRouter(
    prefix="/trips",
    tags=["Trips"],
)


@router.post(
    "",
    response_model=TripResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_trip_endpoint(
    trip_data: TripCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return create_trip(
        db,
        trip_data,
        current_user.id,
    )


@router.get(
    "",
    response_model=list[TripResponse],
)
def list_my_trips(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return get_user_trips(
        db,
        current_user.id,
    )


@router.get(
    "/{trip_id}",
    response_model=TripResponse,
)
def get_trip(
    trip_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        trip = get_trip_or_404(db, trip_id)

        ensure_trip_member(
            db,
            trip_id,
            current_user.id,
        )

        return trip

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )

    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )


@router.put(
    "/{trip_id}",
    response_model=TripResponse,
)
def update_trip_endpoint(
    trip_id: UUID,
    update_data: TripUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        trip = get_trip_or_404(db, trip_id)

        if trip.organizer_id != current_user.id:
            raise PermissionError(
                "Only the organizer can update this trip"
            )

        return update_trip(
            db,
            trip,
            update_data,
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )

    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )


@router.delete(
    "/{trip_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_trip_endpoint(
    trip_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        trip = get_trip_or_404(db, trip_id)

        if trip.organizer_id != current_user.id:
            raise PermissionError(
                "Only the organizer can delete this trip"
            )

        delete_trip(
            db,
            trip,
        )

        return None

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )

    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )