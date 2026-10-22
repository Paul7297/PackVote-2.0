import json
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from app.core.config import settings
from app.schemas.place import PlaceSearchResult


def _build_place_result(item: dict) -> PlaceSearchResult:
    name = (
        item.get("name")
        or item.get("city")
        or item.get("town")
        or item.get("village")
        or item.get("county")
        or item.get("formatted")
        or "Unknown place"
    )

    region = (
        item.get("state")
        or item.get("county")
        or item.get("city")
        or item.get("town")
        or item.get("village")
    )

    return PlaceSearchResult(
        external_place_id=item.get("place_id"),
        name=name,
        country=item.get("country"),
        region=region,
        latitude=item.get("lat"),
        longitude=item.get("lon"),
        display_name=item.get("formatted") or name,
    )


def search_places(query: str, limit: int = 5) -> list[PlaceSearchResult]:
    candidate = query.strip()
    if not candidate:
        return []

    if not settings.geoapify_api_key:
        raise ValueError("Geoapify API key is not configured")

    params = urlencode(
        {
            "text": candidate,
            "format": "json",
            "limit": max(1, min(limit, 10)),
            "apiKey": settings.geoapify_api_key,
        }
    )
    request = Request(
        f"https://api.geoapify.com/v1/geocode/search?{params}",
        headers={"Accept": "application/json"},
    )

    try:
        with urlopen(request, timeout=10) as response:
            data = json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise ValueError("Geoapify destination search failed") from exc

    results = data.get("results", [])
    return [_build_place_result(item) for item in results]


def get_place_by_id(external_place_id: str) -> PlaceSearchResult:
    place_id = external_place_id.strip()
    if not place_id:
        raise ValueError("Place ID is required")

    if not settings.geoapify_api_key:
        raise ValueError("Geoapify API key is not configured")

    params = urlencode(
        {
            "id": place_id,
            "apiKey": settings.geoapify_api_key,
        }
    )
    request = Request(
        f"https://api.geoapify.com/v2/place-details?{params}",
        headers={"Accept": "application/json"},
    )

    try:
        with urlopen(request, timeout=10) as response:
            data = json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise ValueError("Geoapify could not verify the selected place") from exc

    features = data.get("features", [])
    if not features:
        raise ValueError("Selected place was not found")

    return _build_place_result(features[0].get("properties", {}))