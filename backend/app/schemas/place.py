from pydantic import BaseModel, ConfigDict


class PlaceSearchResult(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    external_place_id: str | None = None
    name: str
    country: str | None = None
    region: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    display_name: str
