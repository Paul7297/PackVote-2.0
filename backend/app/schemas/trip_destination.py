from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.core.constants import CandidateSource, DestinationStatus


class TripDestinationCreate(BaseModel):
    destination_id: UUID


class ConfirmPlaceRequest(BaseModel):
    external_place_id: str = Field(..., min_length=1, max_length=255)


class TripDestinationUpdate(BaseModel):
    status: DestinationStatus


class TripDestinationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    trip_id: UUID
    destination_id: UUID
    added_by: UUID | None
    source: CandidateSource
    status: DestinationStatus
    created_at: datetime
    updated_at: datetime