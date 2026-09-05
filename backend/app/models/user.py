from sqlalchemy import Column, String, Boolean

from app.models.base import BaseModel


class User(BaseModel):
    __tablename__ = "users"

    full_name = Column(String(100), nullable=False)

    email = Column(
        String(255),
        unique=True,
        nullable=False,
        index=True
    )

    password_hash = Column(
        String(255),
        nullable=False
    )

    phone_number = Column(
        String(20),
        nullable=True
    )

    profile_image = Column(
        String(500),
        nullable=True
    )

    is_verified = Column(
        Boolean,
        default=False,
        nullable=False
    )

    is_active = Column(
        Boolean,
        default=True,
        nullable=False
    )