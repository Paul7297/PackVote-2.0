from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.core.constants import (
    Activity,
    CostTier,
    DestinationClimate,
    TravelStyle,
    TravelerType,
)


class DestinationCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    country: str | None = Field(default=None, max_length=100)
    region: str | None = Field(default=None, max_length=100)

    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)

    external_place_id: str | None = Field(default=None, max_length=255)
    provider_name: str | None = Field(default=None, max_length=50)

    climate: DestinationClimate | None = None
    cost_tier: CostTier | None = None
    suitable_travel_styles: list[TravelStyle] | None = Field(
        default=None,
        min_length=1,
        max_length=6,
    )
    suitable_activities: list[Activity] | None = Field(
        default=None,
        min_length=1,
        max_length=12,
    )
    suitable_traveler_types: list[TravelerType] | None = Field(
        default=None,
        min_length=1,
        max_length=4,
    )

    description: str | None = Field(default=None, max_length=1000)


class DestinationUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=100)
    country: str | None = Field(default=None, max_length=100)
    region: str | None = Field(default=None, max_length=100)

    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)

    external_place_id: str | None = Field(default=None, max_length=255)
    provider_name: str | None = Field(default=None, max_length=50)

    climate: DestinationClimate | None = None
    cost_tier: CostTier | None = None
    suitable_travel_styles: list[TravelStyle] | None = Field(
        default=None,
        min_length=1,
        max_length=6,
    )
    suitable_activities: list[Activity] | None = Field(
        default=None,
        min_length=1,
        max_length=12,
    )
    suitable_traveler_types: list[TravelerType] | None = Field(
        default=None,
        min_length=1,
        max_length=4,
    )

    description: str | None = Field(default=None, max_length=1000)


class DestinationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    country: str | None
    region: str | None
    latitude: float | None
    longitude: float | None
    external_place_id: str | None
    provider_name: str | None
    climate: DestinationClimate | None
    cost_tier: CostTier | None
    suitable_travel_styles: list[TravelStyle] | None
    suitable_activities: list[Activity] | None
    suitable_traveler_types: list[TravelerType] | None
    description: str | None
    created_at: datetime
    updated_at: datetime