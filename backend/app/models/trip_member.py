from sqlalchemy import Column, String, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import BaseModel
from app.core.constants import MemberRole, MemberStatus


class TripMember(BaseModel):
    __tablename__ = "trip_members"
    __table_args__ = (
        UniqueConstraint("trip_id", "user_id", name="uq_trip_member"),
    )

    trip_id = Column(UUID(as_uuid=True), ForeignKey("trips.id"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)

    role = Column(String(20), nullable=False, default=MemberRole.MEMBER.value)
    status = Column(String(20), nullable=False, default=MemberStatus.INVITED.value)