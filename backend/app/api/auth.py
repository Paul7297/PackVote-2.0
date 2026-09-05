from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from app.core.deps import get_current_user
from app.core.limiter import limiter
from app.models.user import User




from app.database.database import get_db
from app.schemas.user import (
    UserRegister,
    UserLogin,
    UserResponse,
    Token,
    RefreshTokenRequest,
)
from app.services.auth_service import (
    register_user,
    login_user,
    refresh_user_tokens,
)

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
@limiter.limit("10/minute")
def register(
    request: Request,
    user: UserRegister,
    db: Session = Depends(get_db),
):
    try:
        return register_user(db, user)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post(
    "/login",
    response_model=Token,
)
@limiter.limit("5/minute")
def login(
    request: Request,
    user: UserLogin,
    db: Session = Depends(get_db),
):
    try:
        return login_user(
            db,
            user.email,
            user.password,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )


@router.post("/refresh", response_model=Token)
@limiter.limit("10/minute")
def refresh(
    request: Request,
    body: RefreshTokenRequest,
    db: Session = Depends(get_db),
):
    try:
        return refresh_user_tokens(db, body.refresh_token)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user
