from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.constants import (
    DestinationStatus,
    MemberStatus,
    TripStatus,
)
from app.crud.trip import get_trip_by_id, get_trip_member
from app.crud.trip_destination import (
    get_candidates_for_trip,
    get_trip_destination_by_id,
)
from app.crud.trip_vote import (
    create_vote_row,
    get_vote,
    get_vote_counts_for_trip,
    update_vote_row,
)
from app.models.trip_vote import TripVote
from app.schemas.trip_vote import TripVoteResults


def cast_vote(
    db: Session,
    trip_id: UUID,
    user_id: UUID,
    trip_destination_id: UUID,
) -> TripVote:
    """
    Cast a new vote or change the user's existing vote.

    Rules:
    - Trip must exist.
    - User must be a joined member.
    - Trip must be in voting status.
    - Candidate must belong to the trip.
    - Candidate must be proposed.
    - One vote per user per trip.
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
            "You must be a joined member of this trip to vote"
        )

    if trip.status != TripStatus.VOTING.value:
        raise ValueError(
            "Voting is not open for this trip"
        )

    candidate = get_trip_destination_by_id(
        db,
        trip_destination_id,
    )

    if (
        candidate is None
        or candidate.trip_id != trip_id
    ):
        raise ValueError(
            "Candidate not found for this trip"
        )

    if candidate.status != DestinationStatus.PROPOSED.value:
        raise ValueError(
            "You can only vote for proposed destinations"
        )

    try:
        vote = get_vote(
            db,
            trip_id,
            user_id,
        )

        if vote is None:
            vote = TripVote(
                trip_id=trip_id,
                trip_destination_id=trip_destination_id,
                user_id=user_id,
            )

            create_vote_row(db, vote)

        else:
            # Changing a vote updates the existing row.
            vote.trip_destination_id = trip_destination_id
            update_vote_row(db, vote)

        db.commit()
        db.refresh(vote)

        return vote

    except IntegrityError as exc:
        db.rollback()

        constraint_name = getattr(
            getattr(exc.orig, "diag", None),
            "constraint_name",
            None,
        )

        if constraint_name == "uq_trip_vote":
            raise ValueError(
                "You already have a vote for this trip"
            ) from exc

        raise

    except Exception:
        db.rollback()
        raise


def get_my_vote(
    db: Session,
    trip_id: UUID,
    user_id: UUID,
) -> TripVote | None:
    """
    Return the current user's vote for a trip.

    A user must be a joined member of the trip.
    """

    trip = get_trip_by_id(
        db,
        trip_id,
    )

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
            "You must be a joined member of this trip"
        )

    return get_vote(
        db,
        trip_id,
        user_id,
    )


def get_trip_vote_results(
    db: Session,
    trip_id: UUID,
    user_id: UUID,
) -> TripVoteResults:
    """
    Return vote totals for active/proposed candidates.

    Any joined trip member can view the results.
    """

    trip = get_trip_by_id(
        db,
        trip_id,
    )

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
            "You must be a joined member of this trip"
        )

    counts = dict(
        get_vote_counts_for_trip(
            db,
            trip_id,
        )
    )

    candidates = get_candidates_for_trip(
        db,
        trip_id,
    )

    # Rejected candidates should not appear in active voting results.
    active_candidates = [
        candidate
        for candidate in candidates
        if candidate.status != DestinationStatus.REJECTED.value
    ]

    results = [
        {
            "trip_destination_id": candidate.id,
            "vote_count": counts.get(candidate.id, 0),
        }
        for candidate in active_candidates
    ]

    total_votes = sum(
        result["vote_count"]
        for result in results
    )

    return TripVoteResults(
        trip_id=trip_id,
        total_votes=total_votes,
        results=results,
    )