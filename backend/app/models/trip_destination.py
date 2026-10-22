from sqlalchemy import Column, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID

from app.core.constants import CandidateSource, DestinationStatus
from app.models.base import BaseModel



class TripDestination(BaseModel):
    __tablename__ = "trip_destinations"

    __table_args__ = (
        UniqueConstraint(
            "trip_id",
            "destination_id",
            name="uq_trip_destination",
        ),
    )

    trip_id = Column(
        UUID(as_uuid=True),
        ForeignKey("trips.id"),
        nullable=False,
        index=True,
    )

    destination_id = Column(
        UUID(as_uuid=True),
        ForeignKey("destinations.id"),
        nullable=False,
        index=True,
    )

    added_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True,
        index=True,
    )

    source = Column(
        String(20),
        nullable=False,
        default=CandidateSource.MANUAL.value,
    )

    status = Column(
        String(20),
        nullable=False,
        default=DestinationStatus.PROPOSED.value,
    )