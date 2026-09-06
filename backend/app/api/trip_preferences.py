from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.database.database import get_db
from app.models.user import User
from app.schemas.trip_preference import (
    PreferenceCompletionStatus,
    TripPreferenceCreate,
    TripPreferenceResponse,
    TripPreferenceUpdate,
)
from app.services.trip_preference_service import (
    delete_preference,
    get_all_trip_preferences,
    get_completion_status,
    get_my_preference,
    submit_preference,
    update_preference,
)


router = APIRouter(
    prefix="/trips/{trip_id}/preferences",
    tags=["Trip Preferences"],
)


@router.post(
    "",
    response_model=TripPreferenceResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_preference(
    trip_id: UUID,
    preference_data: TripPreferenceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return submit_preference(
            db=db,
            trip_id=trip_id,
            user_id=current_user.id,
            preference_data=preference_data,
        )

    except ValueError as exc:
        message = str(exc)

        if "already submitted" in message:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=message,
            ) from exc

        if "Trip not found" in message:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=message,
            ) from exc

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message,
        ) from exc

    except PermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc


@router.patch(
    "",
    response_model=TripPreferenceResponse,
)
def update_my_preference(
    trip_id: UUID,
    update_data: TripPreferenceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return update_preference(
            db=db,
            trip_id=trip_id,
            user_id=current_user.id,
            update_data=update_data,
        )

    except ValueError as exc:
        message = str(exc)

        if (
            "Trip not found" in message
            or "No preference submission found" in message
        ):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=message,
            ) from exc

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message,
        ) from exc

    except PermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc


@router.get(
    "/me",
    response_model=TripPreferenceResponse,
)
def get_my_preference_endpoint(
    trip_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        preference = get_my_preference(
            db=db,
            trip_id=trip_id,
            user_id=current_user.id,
        )

        if preference is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No preference submission found",
            )

        return preference

    except ValueError as exc:
        message = str(exc)

        if "Trip not found" in message:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=message,
            ) from exc

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message,
        ) from exc

    except PermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc


@router.get(
    "",
    response_model=list[TripPreferenceResponse],
)
def get_all_preferences(
    trip_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return get_all_trip_preferences(
            db=db,
            trip_id=trip_id,
            user_id=current_user.id,
        )

    except ValueError as exc:
        message = str(exc)

        if "Trip not found" in message:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=message,
            ) from exc

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message,
        ) from exc

    except PermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc


@router.delete(
    "",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_my_preference(
    trip_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        delete_preference(
            db=db,
            trip_id=trip_id,
            user_id=current_user.id,
        )

        return Response(
            status_code=status.HTTP_204_NO_CONTENT
        )

    except ValueError as exc:
        message = str(exc)

        if (
            "Trip not found" in message
            or "No preference submission found" in message
        ):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=message,
            ) from exc

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message,
        ) from exc

    except PermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc


@router.get(
    "/status",
    response_model=PreferenceCompletionStatus,
)
def get_preference_completion_status(
    trip_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return get_completion_status(
            db=db,
            trip_id=trip_id,
            user_id=current_user.id,
        )

    except ValueError as exc:
        message = str(exc)

        if "Trip not found" in message:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=message,
            ) from exc

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message,
        ) from exc

    except PermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc