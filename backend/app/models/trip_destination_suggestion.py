from sqlalchemy import Column, Float, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID

from app.models.base import BaseModel


class TripDestinationSuggestion(BaseModel):
    __tablename__ = "trip_destination_suggestions"
    __table_args__ = (
        UniqueConstraint(
            "trip_id",
            "external_place_id",
            name="uq_trip_destination_suggestion_place",
        ),
    )

    trip_id = Column(
        UUID(as_uuid=True),
        ForeignKey("trips.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    suggested_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )
    external_place_id = Column(String(255), nullable=False)
    name = Column(String(100), nullable=False)
    country = Column(String(100), nullable=True)
    region = Column(String(100), nullable=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    status = Column(String(20), nullable=False, default="pending", index=True)
    trip_destination_id = Column(
        UUID(as_uuid=True),
        ForeignKey("trip_destinations.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
