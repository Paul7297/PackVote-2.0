from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.user import UserResponse, UserUpdate, ChangePasswordRequest
from app.services.auth_service import update_user_profile, change_user_password

router = APIRouter(prefix="/users", tags=["Users"])


@router.put("/me", response_model=UserResponse)
def update_profile(
    update_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return update_user_profile(db, current_user, update_data)


@router.post("/change-password", status_code=status.HTTP_204_NO_CONTENT)
def change_password(
    body: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        change_user_password(db, current_user, body.old_password, body.new_password)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))