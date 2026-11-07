from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.constants import MemberStatus
from app.core.deps import get_current_user
from app.crud.trip import get_trip_by_id, get_trip_member
from app.database.database import get_db
from app.models.destination import Destination
from app.models.trip_member import TripMember
from app.models.trip_preference import TripPreference
from app.models.user import User
from app.services.cost_estimation_service import estimate_trip_cost


router = APIRouter(
    prefix="/trips",
    tags=["Cost Estimates"],
)


@router.get("/{trip_id}/destinations/{destination_id}/cost-estimate")
def get_cost_estimate(
    trip_id: UUID,
    destination_id: UUID,
    origin_city: str = "delhi",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Return a rule-based cost estimate for a destination within a trip.

    The caller must be a joined member of the trip.
    """

    # -- Trip lookup ----------------------------------------------------------
    trip = get_trip_by_id(db, trip_id)
    if trip is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trip not found",
        )

    # -- Membership check -----------------------------------------------------
    member = get_trip_member(db, trip_id, current_user.id)
    if member is None or member.status != MemberStatus.JOINED.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You must be a joined member of this trip",
        )

    # -- Destination lookup ---------------------------------------------------
    destination = (
        db.query(Destination)
        .filter(Destination.id == destination_id)
        .first()
    )
    if destination is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Destination not found",
        )

    # -- Preferences for this trip --------------------------------------------
    preferences = (
        db.query(TripPreference)
        .filter(TripPreference.trip_id == trip_id)
        .all()
    )

    # -- Joined member count --------------------------------------------------
    member_count = (
        db.query(TripMember)
        .filter(
            TripMember.trip_id == trip_id,
            TripMember.status == MemberStatus.JOINED.value,
        )
        .count()
    )

    # -- Estimate -------------------------------------------------------------
    return estimate_trip_cost(trip, destination, preferences, member_count, origin_city=origin_city)
