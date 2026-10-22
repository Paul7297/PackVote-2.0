from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.trip_vote import TripVote


def get_vote(
    db: Session,
    trip_id: UUID,
    user_id: UUID,
) -> TripVote | None:
    """
    Find the current vote of a user for a specific trip.
    """
    return (
        db.query(TripVote)
        .filter(
            TripVote.trip_id == trip_id,
            TripVote.user_id == user_id,
        )
        .first()
    )


def create_vote_row(
    db: Session,
    vote: TripVote,
) -> TripVote:
    """
    Add a new vote to the session.
    Does not commit.
    """
    db.add(vote)
    return vote


def get_votes_for_trip(
    db: Session,
    trip_id: UUID,
) -> list[TripVote]:
    """
    Return all votes for a trip.
    """
    return (
        db.query(TripVote)
        .filter(TripVote.trip_id == trip_id)
        .all()
    )


def get_vote_counts_for_trip(
    db: Session,
    trip_id: UUID,
) -> list[tuple[UUID, int]]:
    """
    Return vote counts grouped by trip destination.
    """
    rows = (
        db.query(
            TripVote.trip_destination_id,
            func.count(TripVote.id),
        )
        .filter(
            TripVote.trip_id == trip_id,
        )
        .group_by(
            TripVote.trip_destination_id,
        )
        .all()
    )

    return [
        (destination_id, count)
        for destination_id, count in rows
    ]


def update_vote_row(
    db: Session,
    vote: TripVote,
) -> TripVote:
    """
    Add changes to an existing vote.
    Does not commit.
    """
    db.add(vote)
    return vote


def delete_vote_row(
    db: Session,
    vote: TripVote,
) -> None:
    """
    Delete a vote from the session.
    Does not commit.
    """
    db.delete(vote)