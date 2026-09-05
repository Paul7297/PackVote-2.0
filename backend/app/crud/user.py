from sqlalchemy.orm import Session
from app.models.user import User


def get_user_by_email(db: Session, email: str):
    """Return a user by email."""
    return db.query(User).filter(User.email == email).first()


def get_user_by_id(db: Session, user_id):
    """Return a user by ID."""
    return db.query(User).filter(User.id == user_id).first()


def create_user(db: Session, user: User):
    """Create a new user."""
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def update_user(db: Session, user: User):
    """Update an existing user."""
    db.commit()
    db.refresh(user)
    return user


def delete_user(db: Session, user: User):
    """Delete a user."""
    db.delete(user)
    db.commit()