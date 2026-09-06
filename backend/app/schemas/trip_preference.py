from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict

from app.core.constants import (
    BudgetRange,
    ClimatePreference,
    AccommodationPref,
    TransportPref,
    FoodPref,
    TravelPriority,
    TravelStyle,
    Activity,
)


class TripPreferenceCreate(BaseModel):
    budget_range: BudgetRange

    travel_style: list[TravelStyle] = Field(
        ...,
        min_length=1,
        max_length=6,
    )

    preferred_activities: list[Activity] = Field(
        ...,
        min_length=1,
        max_length=12,
    )

    climate_preference: ClimatePreference
    accommodation_pref: AccommodationPref
    transport_pref: TransportPref
    food_pref: FoodPref
    travel_priority: TravelPriority

    notes: str | None = Field(
        default=None,
        max_length=1000,
    )


class TripPreferenceUpdate(BaseModel):
    budget_range: BudgetRange | None = None

    travel_style: list[TravelStyle] | None = Field(
        default=None,
        min_length=1,
        max_length=6,
    )

    preferred_activities: list[Activity] | None = Field(
        default=None,
        min_length=1,
        max_length=12,
    )

    climate_preference: ClimatePreference | None = None
    accommodation_pref: AccommodationPref | None = None
    transport_pref: TransportPref | None = None
    food_pref: FoodPref | None = None
    travel_priority: TravelPriority | None = None

    notes: str | None = Field(
        default=None,
        max_length=1000,
    )


class TripPreferenceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    trip_id: UUID
    user_id: UUID

    budget_range: BudgetRange
    travel_style: list[TravelStyle]
    preferred_activities: list[Activity]
    climate_preference: ClimatePreference
    accommodation_pref: AccommodationPref
    transport_pref: TransportPref
    food_pref: FoodPref
    travel_priority: TravelPriority

    notes: str | None

    created_at: datetime
    updated_at: datetime


class PreferenceCompletionStatus(BaseModel):
    submitted: int
    total: int
    complete: bool