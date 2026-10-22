from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.crud.destination import get_destination_by_id
from app.database.database import get_db
from app.models.user import User
from app.schemas.destination import DestinationResponse
from app.schemas.place import PlaceSearchResult
from app.services.destination_service import list_destinations
from app.services.place_service import search_places

router = APIRouter(
    prefix="/destinations",
    tags=["Destinations"],
)


@router.get(
    "",
    response_model=list[DestinationResponse],
    status_code=status.HTTP_200_OK,
)
def get_destinations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Return all destinations from the catalog.

    Authentication is required.
    """
    return list_destinations(db)


@router.get(
    "/search",
    response_model=list[PlaceSearchResult],
    status_code=status.HTTP_200_OK,
)
def search_destination_places(
    query: str = Query(..., min_length=2, max_length=100),
    limit: int = Query(5, ge=1, le=10),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Resolve a user-entered destination name using a real geocoding provider.
    This is the first step before creating a destination catalog entry.
    """
    try:
        return search_places(query=query, limit=limit)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc


@router.get(
    "/{destination_id}",
    response_model=DestinationResponse,
    status_code=status.HTTP_200_OK,
)
def get_destination(
    destination_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Return a single destination by ID.

    Authentication is required.
    """
    destination = get_destination_by_id(db, destination_id)

    if destination is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Destination not found",
        )

    return destination