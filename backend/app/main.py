from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.api import auth
from app.core.config import get_cors_origins
from app.core.limiter import limiter
from app.database.database import get_db

app = FastAPI(title="PackVote API")

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)


@app.get("/")
def root():
    return {"message": "PackVote API is running"}


@app.get("/health/db")
def db_health(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    return {"database": "connected"}

from app.api import auth, users

app.include_router(auth.router)
app.include_router(users.router)

from app.api import auth, users, trips

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(trips.router)