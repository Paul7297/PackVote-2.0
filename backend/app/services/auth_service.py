from sqlalchemy.orm import Session

from app.crud.user import (
    get_user_by_email,
    create_user,
)
from app.models.user import User
from app.schemas.user import UserRegister
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
)

from app.crud.user import get_user_by_email, create_user, update_user
from app.schemas.user import UserRegister, UserUpdate


def register_user(db: Session, user_data: UserRegister):
    """
    Register a new user.
    """
    existing_user = get_user_by_email(db, user_data.email)

    if existing_user:
        raise ValueError("Email already registered")

    user = User(
        full_name=user_data.full_name,
        email=user_data.email,
        password_hash=hash_password(user_data.password),
        phone_number=user_data.phone_number,
    )

    return create_user(db, user)


def login_user(db: Session, email: str, password: str):
    """
    Authenticate user and return JWT tokens.
    """
    user = get_user_by_email(db, email)

    if not user:
        raise ValueError("Invalid email or password")

    if not verify_password(password, user.password_hash):
        raise ValueError("Invalid email or password")

    if not user.is_active:
        raise ValueError("Invalid email or password")

    token_data = {"sub": str(user.id), "email": user.email}
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


def refresh_user_tokens(db: Session, refresh_token: str):
    payload = decode_refresh_token(refresh_token)
    if payload is None:
        raise ValueError("Invalid refresh token")

    email = payload.get("email")
    if not email:
        raise ValueError("Invalid refresh token")

    user = get_user_by_email(db, email)
    if user is None or not user.is_active:
        raise ValueError("Invalid refresh token")

    token_data = {"sub": str(user.id), "email": user.email}
    access_token = create_access_token(token_data)
    new_refresh_token = create_refresh_token(token_data)

    return {
        "access_token": access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
    }
    
def update_user_profile(db: Session, user: User, update_data: "UserUpdate") -> User:
    """Update allowed profile fields for the given user."""
    if update_data.full_name is not None:
        user.full_name = update_data.full_name
    if update_data.phone_number is not None:
        user.phone_number = update_data.phone_number
    if update_data.profile_image is not None:
        user.profile_image = update_data.profile_image

    return update_user(db, user)


def change_user_password(db: Session, user: User, old_password: str, new_password: str) -> User:
    """Verify the old password, then set a new hashed password."""
    if not verify_password(old_password, user.password_hash):
        raise ValueError("Current password is incorrect")

    user.password_hash = hash_password(new_password)
    return update_user(db, user)
