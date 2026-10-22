from sqlalchemy import Column, Float, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB

from app.models.base import BaseModel


class Destination(BaseModel):
    __tablename__ = "destinations"

    __table_args__ = (
        UniqueConstraint(
            "provider_name",
            "external_place_id",
            name="uq_destination_provider_place",
        ),
    )

    name = Column(String(100), nullable=False)
    country = Column(String(100), nullable=True)
    region = Column(String(100), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)

    external_place_id = Column(String(255), nullable=True)
    provider_name = Column(String(50), nullable=True)

    # These are recommendation details; they can be filled in later.
    climate = Column(String(20), nullable=True)
    cost_tier = Column(String(20), nullable=True)
    suitable_travel_styles = Column(JSONB, nullable=True)
    suitable_activities = Column(JSONB, nullable=True)
    suitable_traveler_types = Column(JSONB, nullable=True)

    description = Column(Text, nullable=True)