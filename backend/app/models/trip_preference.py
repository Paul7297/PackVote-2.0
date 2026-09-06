from sqlalchemy import Column, String, Text, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.models.base import BaseModel


class TripPreference(BaseModel):
    __tablename__ = "trip_preferences"

    __table_args__ = (
        UniqueConstraint(
            "trip_id",
            "user_id",
            name="uq_trip_preference",
        ),
    )

    trip_id = Column(
        UUID(as_uuid=True),
        ForeignKey("trips.id"),
        nullable=False,
        index=True,
    )

    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    budget_range = Column(
        String(20),
        nullable=False,
    )

    travel_style = Column(
        JSONB,
        nullable=False,
        default=list,
    )

    preferred_activities = Column(
        JSONB,
        nullable=False,
        default=list,
    )

    climate_preference = Column(
        String(20),
        nullable=False,
    )

    accommodation_pref = Column(
        String(20),
        nullable=False,
    )

    transport_pref = Column(
        String(20),
        nullable=False,
    )

    food_pref = Column(
        String(20),
        nullable=False,
    )

    travel_priority = Column(
        String(20),
        nullable=False,
    )

    notes = Column(
        Text,
        nullable=True,
    )