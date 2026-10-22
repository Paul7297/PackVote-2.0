from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class TripDestinationSuggestionCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    external_place_id: str = Field(..., min_length=1, max_length=255)


class TripDestinationSuggestionReview(BaseModel):
    status: str = Field(..., pattern="^(approved|rejected)$")


class TripDestinationSuggestionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    trip_id: UUID
    suggested_by: UUID
    external_place_id: str
    name: str
    country: str | None
    region: str | None
    latitude: float
    longitude: float
    status: str
    trip_destination_id: UUID | None
    created_at: datetime
