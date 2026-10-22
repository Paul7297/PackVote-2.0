from sqlalchemy import Column, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID

from app.models.base import BaseModel


class TripVote(BaseModel):
    __tablename__ = "trip_votes"

    __table_args__ = (
        UniqueConstraint(
            "trip_id",
            "user_id",
            name="uq_trip_vote",
        ),
    )

    trip_id = Column(
        UUID(as_uuid=True),
        ForeignKey("trips.id"),
        nullable=False,
        index=True,
    )

    trip_destination_id = Column(
        UUID(as_uuid=True),
        ForeignKey("trip_destinations.id"),
        nullable=False,
        index=True,
    )

    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )