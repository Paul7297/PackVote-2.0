
"""Retrieve historical weather and forecasts for PackVote trips."""

import json
from datetime import date, datetime, timedelta
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo


FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
HISTORICAL_URL = "https://archive-api.open-meteo.com/v1/archive"

DAILY_VARIABLES = (
    "weather_code,temperature_2m_max,temperature_2m_min,"
    "precipitation_sum,wind_speed_10m_max"
)

WEATHER_CODES = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    71: "Slight snow",
    73: "Moderate snow",
    75: "Heavy snow",
    80: "Rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    95: "Thunderstorm",
    96: "Thunderstorm with hail",
    99: "Thunderstorm with heavy hail",
}


def _fetch_json(url: str, params: dict, source: str) -> dict:
    """Request JSON from a weather provider."""
    request = Request(
        f"{url}?{urlencode(params)}",
        headers={"User-Agent": "PackVote-Educational-Project/1.0"},
    )

    try:
        with urlopen(request, timeout=15) as response:
            return json.loads(response.read().decode("utf-8"))
    except (
        HTTPError,
        URLError,
        TimeoutError,
        json.JSONDecodeError,
    ) as exc:
        raise RuntimeError(
            f"{source} is temporarily unavailable."
        ) from exc


def _records_from_payload(
    payload: dict,
    data_type: str,
    source: str,
) -> list[dict]:
    """Normalize daily weather records from either API."""
    daily = payload.get("daily") or {}
    dates = daily.get("time") or []
    records = []

    def value_at(field: str, index: int):
        values = daily.get(field) or []
        return values[index] if index < len(values) else None

    for index, weather_date in enumerate(dates):
        code = value_at("weather_code", index)

        records.append({
            "date": weather_date,
            "data_type": data_type,
            "source": source,
            "weather_code": code,
            "description": WEATHER_CODES.get(
                code,
                "Weather condition unavailable"
                if code is None
                else f"Weather code {code}",
            ),
            "temperature_max_c": value_at(
                "temperature_2m_max", index
            ),
            "temperature_min_c": value_at(
                "temperature_2m_min", index
            ),
            "precipitation_mm": value_at(
                "precipitation_sum", index
            ),
            "maximum_wind_speed_kmh": value_at(
                "wind_speed_10m_max", index
            ),
        })

    return records


def _fetch_forecast(
    latitude: float,
    longitude: float,
) -> tuple[dict, list[dict]]:
    """Get the currently available forecast window."""
    payload = _fetch_json(
        FORECAST_URL,
        {
            "latitude": latitude,
            "longitude": longitude,
            "daily": DAILY_VARIABLES,
            "forecast_days": 16,
            "timezone": "auto",
        },
        "Open-Meteo Forecast API",
    )

    records = _records_from_payload(
        payload,
        "forecast",
        "Open-Meteo Forecast API",
    )
    return payload, records


def _fetch_history(
    latitude: float,
    longitude: float,
    start_date: date,
    end_date: date,
) -> list[dict]:
    """Get historical reanalysis data for a past date range."""
    payload = _fetch_json(
        HISTORICAL_URL,
        {
            "latitude": latitude,
            "longitude": longitude,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "daily": DAILY_VARIABLES,
            "timezone": "auto",
        },
        "Open-Meteo Historical Weather API",
    )

    return _records_from_payload(
        payload,
        "historical_reanalysis",
        "Open-Meteo Historical Weather API (reanalysis)",
    )


def get_destination_weather(trip, destination) -> dict:
    """Return weather data appropriate to a trip's dates."""

    if destination.latitude is None or destination.longitude is None:
        raise ValueError(
            "Destination coordinates are required for weather lookup"
        )

    trip_start = trip.start_date
    trip_end = trip.end_date
    trip_dates_set = bool(trip_start and trip_end)

    if trip_dates_set and trip_end < trip_start:
        raise ValueError(
            "Trip end date cannot precede its start date"
        )

    # PackVote currently uses India-local date semantics for trips.
    today = datetime.now(ZoneInfo("Asia/Kolkata")).date()

    days = []
    missing_dates = []

    if not trip_dates_set:
        # No planned dates: show a general forecast, not a trip-specific one.
        _, forecast_records = _fetch_forecast(
            destination.latitude,
            destination.longitude,
        )
        days = forecast_records[:7]
        message = (
            "Trip dates are not set. Showing a general seven-day forecast."
        )

    else:
        requested_dates = {
            (trip_start + timedelta(days=offset)).isoformat()
            for offset in range((trip_end - trip_start).days + 1)
        }

        # Past days use the Historical Weather API.
        historical_end = min(
            trip_end,
            today - timedelta(days=1),
        )

        if trip_start <= historical_end:
            historical_records = _fetch_history(
                destination.latitude,
                destination.longitude,
                trip_start,
                historical_end,
            )
            days.extend(
                record
                for record in historical_records
                if record["date"] in requested_dates
            )

        # Today and future days use the Forecast API.
        forecast_start = max(trip_start, today)

        if forecast_start <= trip_end:
            _, forecast_records = _fetch_forecast(
                destination.latitude,
                destination.longitude,
            )
            days.extend(
                record
                for record in forecast_records
                if (
                    forecast_start.isoformat()
                    <= record["date"]
                    <= trip_end.isoformat()
                )
            )

        days.sort(key=lambda record: record["date"])

        available_dates = {record["date"] for record in days}
        missing_dates = sorted(requested_dates - available_dates)

        has_history = any(
            record["data_type"] == "historical_reanalysis"
            for record in days
        )
        has_forecast = any(
            record["data_type"] == "forecast"
            for record in days
        )

        if not missing_dates:
            if has_history and has_forecast:
                message = (
                    "Weather data is available for all trip dates. "
                    "Past dates use historical reanalysis; current and "
                    "future dates use forecasts."
                )
            elif has_history:
                message = (
                    "Historical reanalysis is available for all trip dates. "
                    "These are reconstructed historical estimates, not "
                    "exact station observations or forecasts."
                )
            else:
                message = (
                    "Forecast data is available for all trip dates."
                )
        elif days:
            message = (
                "Weather data is available for only part of the trip. "
                "Some dates are outside the available historical or "
                "forecast data."
            )
        else:
            message = (
                "No weather data is available for the selected dates. "
                "Try seasonal climate information for these dates."
            )

    sources = sorted({record["source"] for record in days})

    return {
        "destination_id": str(destination.id),
        "destination_name": destination.name,
        "source": sources,
        "attribution": "Weather data by Open-Meteo (CC BY 4.0)",
        "timezone": (
            "Asia/Kolkata"
            if not trip_dates_set
            else "Destination-local dates"
        ),
        "trip_dates_set": trip_dates_set,
        "weather_data_available": bool(days),
        "forecast_available": any(
            record["data_type"] == "forecast" for record in days
        ),
        "historical_data_available": any(
            record["data_type"] == "historical_reanalysis"
            for record in days
        ),
        "covers_full_trip": (
            trip_dates_set and not missing_dates
        ),
        "missing_weather_dates": missing_dates,
        "days": days,
        "message": message,
    }
