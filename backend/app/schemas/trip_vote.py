from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class TripVoteCreate(BaseModel):
    """
    Request body for casting or changing a vote.
    """
    trip_destination_id: UUID


class TripVoteResponse(BaseModel):
    """
    Return the current vote of a trip member.
    """
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    trip_id: UUID
    trip_destination_id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime


class TripVoteCount(BaseModel):
    """
    Vote count for one destination candidate.
    """
    trip_destination_id: UUID
    vote_count: int
    vote_percentage: float = 0.0


class TripVoteResults(BaseModel):
    """
    Voting results for a trip.
    """
    trip_id: UUID
    total_votes: int
    results: list[TripVoteCount]
    winner_trip_destination_id: UUID | None = None
    is_tie: bool = False
    tie_trip_destination_ids: list[UUID] = []
    participation_count: int = 0
    total_eligible_members: int = 0