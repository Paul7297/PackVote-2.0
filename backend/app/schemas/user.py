from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserRegister(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=100)
    phone_number: str | None = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    full_name: str
    email: EmailStr
    phone_number: str | None = None
    profile_image: str | None = None
    is_verified: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(..., min_length=1)


class TokenData(BaseModel):
    email: str | None = None

class UserUpdate(BaseModel):
    full_name: str | None = Field(None, min_length=2, max_length=100)
    phone_number: str | None = None
    profile_image: str | None = None


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str = Field(..., min_length=8, max_length=100)