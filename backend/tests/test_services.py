from types import SimpleNamespace
from uuid import uuid4

from app.core.constants import CostTier, DestinationClimate
from app.ml.content_recommender import explain_destination, score_destinations
from app.services.ai_assistant_service import (
    compare_destinations,
    explain_destination as ai_explain,
    generate_trip_summary,
)
from app.services.cost_estimation_service import estimate_trip_cost
from app.services.weather_service import WEATHER_CODES, _records_from_payload


def test_content_recommender_scoring():
    dest_id_1 = uuid4()
    dest_id_2 = uuid4()

    dest1 = SimpleNamespace(
        id=dest_id_1,
        suitable_travel_styles=["adventure", "nature"],
        suitable_activities=["trekking", "camping"],
        climate="cold",
        cost_tier="budget",
        suitable_traveler_types=["friends"],
    )
    dest2 = SimpleNamespace(
        id=dest_id_2,
        suitable_travel_styles=["relaxation", "beach"],
        suitable_activities=["swimming", "spa_wellness"],
        climate="tropical",
        cost_tier="luxury",
        suitable_traveler_types=["couple"],
    )

    pref1 = SimpleNamespace(
        travel_style=["adventure", "nature"],
        preferred_activities=["trekking"],
        climate_preference="cold",
        accommodation_pref="budget",
    )

    scores = score_destinations([pref1], [dest1, dest2], traveler_type="friends")
    assert dest_id_1 in scores
    assert dest_id_2 in scores
    assert scores[dest_id_1] > scores[dest_id_2]

    reasons = explain_destination([pref1], dest1, traveler_type="friends")
    assert len(reasons) > 0
    assert any("match" in r.lower() or "traveler type" in r.lower() for r in reasons)


def test_cost_estimation_service():
    trip = SimpleNamespace(start_date=None, end_date=None)
    destination = SimpleNamespace(
        name="Manali",
        cost_tier="budget",
        climate="cold",
    )
    pref = SimpleNamespace(
        food_pref="veg",
        preferred_activities=["trekking", "sightseeing"],
    )

    result = estimate_trip_cost(trip, destination, [pref], member_count=4)

    assert result["currency"] == "INR"
    assert result["member_count"] == 4
    assert result["trip_nights"] == 3
    assert result["destination_name"] == "Manali"
    assert result["cost_tier_used"] == "budget"
    assert "components" in result
    assert result["components"]["hotel"]["rooms"] == 2
    assert result["total_group_cost"] > 0
    assert result["per_person_cost"] > 0
    assert len(result["assumptions"]) > 0


def test_ai_assistant_without_key():
    dest = SimpleNamespace(
        name="Udaipur",
        country="India",
        climate="warm",
        cost_tier="luxury",
        suitable_activities=["historical_places", "local_food"],
        description="City of lakes",
    )

    resp = ai_explain(dest, 78.5, ["Culture match"], "Sunny, 28C", "50000 INR", 3, "All like cultural")
    assert "error" in resp or "content" in resp

    compare_resp = compare_destinations(
        dest, dest, {"a": 70, "b": 60}, "Sunny", "Cloudy", "40000 INR", "35000 INR"
    )
    assert "error" in compare_resp or "content" in compare_resp

    summary_resp = generate_trip_summary("Goa Trip", ["Goa"], "Goa", {}, "Sunny", "100000 INR", 4, "Beach lovers")
    assert "error" in summary_resp or "content" in summary_resp


def test_weather_payload_parsing():
    sample_payload = {
        "daily": {
            "time": ["2026-11-05", "2026-11-06"],
            "weather_code": [0, 61],
            "temperature_2m_max": [25.0, 22.5],
            "temperature_2m_min": [15.0, 14.0],
            "precipitation_sum": [0.0, 3.5],
            "wind_speed_10m_max": [10.2, 14.0],
        }
    }

    records = _records_from_payload(sample_payload, "forecast", "Open-Meteo Test")
    assert len(records) == 2
    assert records[0]["date"] == "2026-11-05"
    assert records[0]["description"] == WEATHER_CODES[0]
    assert records[1]["description"] == WEATHER_CODES[61]
    assert records[0]["temperature_max_c"] == 25.0
