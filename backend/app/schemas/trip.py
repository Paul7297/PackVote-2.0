from datetime import date, datetime
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field, model_validator
from app.core.constants import TripStatus, MemberRole, MemberStatus, TravelerType


class TripCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    description: str | None = None
    budget_min: int | None = Field(default=None, ge=0)
    budget_max: int | None = Field(default=None, ge=0)
    start_date: date | None = None
    end_date: date | None = None
    traveler_type: TravelerType | None = None

    @model_validator(mode="after")
    def validate_trip(self):
        if (
            self.budget_min is not None
            and self.budget_max is not None
            and self.budget_max < self.budget_min
        ):
            raise ValueError("budget_max must be greater than or equal to budget_min")
        if (
            self.start_date is not None
            and self.end_date is not None
            and self.end_date < self.start_date
        ):
            raise ValueError("end_date must be greater than or equal to start_date")
        return self


class TripUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=100)
    description: str | None = None
    budget_min: int | None = Field(default=None, ge=0)
    budget_max: int | None = Field(default=None, ge=0)
    start_date: date | None = None
    end_date: date | None = None
    status: TripStatus | None = None
    traveler_type: TravelerType | None = None

    @model_validator(mode="after")
    def validate_trip(self):
        if (
            self.budget_min is not None
            and self.budget_max is not None
            and self.budget_max < self.budget_min
        ):
            raise ValueError("budget_max must be greater than or equal to budget_min")
        if (
            self.start_date is not None
            and self.end_date is not None
            and self.end_date < self.start_date
        ):
            raise ValueError("end_date must be greater than or equal to start_date")
        return self


class TripResponse(BaseModel):
    id: UUID
    name: str
    organizer_id: UUID
    description: str | None = None
    budget_min: int | None = None
    budget_max: int | None = None
    start_date: date | None = None
    end_date: date | None = None
    status: TripStatus
    traveler_type: TravelerType | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TripMemberResponse(BaseModel):
    id: UUID
    trip_id: UUID
    user_id: UUID
    role: MemberRole
    status: MemberStatus
    created_at: datetime

    class Config:
        from_attributes = True


class TripInviteRequest(BaseModel):
    email: EmailStr


class TripRespondRequest(BaseModel):
    accept: bool