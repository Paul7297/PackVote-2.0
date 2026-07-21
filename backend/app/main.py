from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database.database import get_db

app = FastAPI(title="PackVote API")

@app.get("/")
def root():
    return {"message": "PackVote API is running"}

@app.get("/health/db")
def db_health(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    return {"database": "connected"}