from sqlalchemy import Column, String, Text, Integer, Date, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import BaseModel
from app.core.constants import TripStatus


class Trip(BaseModel):
    __tablename__ = "trips"

    name = Column(String(100), nullable=False)
    organizer_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    description = Column(Text, nullable=True)

    budget_min = Column(Integer, nullable=True)
    budget_max = Column(Integer, nullable=True)

    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)

    status = Column(String(20), nullable=False, default=TripStatus.PLANNING.value)