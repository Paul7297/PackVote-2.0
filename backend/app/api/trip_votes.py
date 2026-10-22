from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.database.database import get_db
from app.models.user import User
from app.schemas.trip_vote import (
    TripVoteCreate,
    TripVoteResponse,
    TripVoteResults,
)
from app.services.trip_vote_service import (
    cast_vote,
    get_my_vote,
    get_trip_vote_results,
)


router = APIRouter(
    prefix="/trips/{trip_id}/votes",
    tags=["Trip Votes"],
)


@router.post(
    "",
    response_model=TripVoteResponse,
    status_code=status.HTTP_200_OK,
)
def cast_or_change_vote(
    trip_id: UUID,
    vote_data: TripVoteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Cast a new vote or change the user's existing vote.

    Voting is allowed only while the trip is in VOTING status.
    """

    try:
        return cast_vote(
            db=db,
            trip_id=trip_id,
            user_id=current_user.id,
            trip_destination_id=vote_data.trip_destination_id,
        )

    except PermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc

    except ValueError as exc:
        message = str(exc)

        if message in {
            "Trip not found",
            "Candidate not found for this trip",
        }:
            code = status.HTTP_404_NOT_FOUND

        elif message == "Voting is not open for this trip":
            code = status.HTTP_409_CONFLICT

        else:
            code = status.HTTP_400_BAD_REQUEST

        raise HTTPException(
            status_code=code,
            detail=message,
        ) from exc


@router.get(
    "/me",
    response_model=TripVoteResponse,
    status_code=status.HTTP_200_OK,
)
def get_my_vote_endpoint(
    trip_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Return the current user's vote for the trip.
    """

    try:
        vote = get_my_vote(
            db=db,
            trip_id=trip_id,
            user_id=current_user.id,
        )

        if vote is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="You have not voted in this trip",
            )

        return vote

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


@router.get(
    "/results",
    response_model=TripVoteResults,
    status_code=status.HTTP_200_OK,
)
def get_vote_results(
    trip_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Return voting results for the trip.
    Any joined member can view the results.
    """

    try:
        return get_trip_vote_results(
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