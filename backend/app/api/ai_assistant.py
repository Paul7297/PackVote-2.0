"""AI assistant router for PackVote.

Exposes: POST /trips/{trip_id}/ai/{action}

Supported actions:
  - explain  — Explain a single destination using ML evidence + Gemini
  - compare  — Compare two destinations side-by-side using Gemini
  - summary  — Generate a full trip planning summary using Gemini
"""

from collections import Counter
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.constants import MemberStatus
from app.core.deps import get_current_user
from app.crud.trip import get_trip_by_id, get_trip_member
from app.database.database import get_db
from app.ml.content_recommender import (
    explain_destination as ml_explain,
    score_destinations,
)
from app.models.destination import Destination
from app.models.trip_destination import TripDestination
from app.models.trip_preference import TripPreference
from app.models.trip_vote import TripVote
from app.models.user import User
from app.services import ai_assistant_service
from app.services.cost_estimation_service import estimate_trip_cost
from app.services.weather_service import get_destination_weather


router = APIRouter(
    prefix="/trips/{trip_id}/ai",
    tags=["AI Assistant"],
)


# ---------------------------------------------------------------------------
# Request body schema
# ---------------------------------------------------------------------------


class AiRequest(BaseModel):
    destination_id: Optional[UUID] = None        # for explain
    destination_id_b: Optional[UUID] = None      # for compare (second destination)
    weather_summary: Optional[str] = None        # caller provides pre-fetched summary
    cost_summary: Optional[str] = None           # caller provides pre-fetched summary
    cost_summary_b: Optional[str] = None         # for compare
    weather_summary_b: Optional[str] = None      # for compare
    origin_city: Optional[str] = "delhi"         # departure city hub


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _build_preferences_summary(preferences: list) -> str:
    """Return a human-readable summary of aggregated group preferences."""
    if not preferences:
        return "No preferences recorded."

    total = len(preferences)

    # Aggregate travel styles
    style_counter: Counter = Counter()
    activity_counter: Counter = Counter()

    for pref in preferences:
        if isinstance(pref.travel_style, list):
            style_counter.update(pref.travel_style)
        if isinstance(pref.preferred_activities, list):
            activity_counter.update(pref.preferred_activities)

    parts = []

    if style_counter:
        top_styles = [
            f"{count} of {total} members prefer {style}"
            for style, count in style_counter.most_common(3)
        ]
        parts.append("; ".join(top_styles))

    if activity_counter:
        top_activities = [
            f"{count} prefer {activity}"
            for activity, count in activity_counter.most_common(3)
        ]
        parts.append("Top activities: " + ", ".join(top_activities))

    return ". ".join(parts) if parts else "No preference details available."


def _resolve_cost_summary(
    trip,
    destination,
    preferences: list,
    member_count: int,
    origin_city: str,
    provided: str | None,
) -> str:
    """Return caller's summary or compute full cost breakdown from origin."""
    if provided and provided.strip():
        return provided.strip()
    try:
        data = estimate_trip_cost(trip, destination, preferences, member_count, origin_city=origin_city)
        origin_name = data.get("origin_city", origin_city).title()
        transit = data.get("transit_details", {})
        flight_cost = transit.get("flight", {}).get("per_person_round_trip", 0)
        train_cost = transit.get("train", {}).get("per_person", 0)
        car_cost = transit.get("car", {}).get("per_person", 0)
        return (
            f"Estimated ₹{data['per_person_cost']:,.0f} per person from {origin_name} "
            f"({data['trip_nights']} nights). "
            f"Flight: ~₹{flight_cost:,}, Train 3AC: ~₹{train_cost:,}, "
            f"Road/Petrol: ~₹{car_cost:,}/person."
        )
    except Exception:
        return f"{destination.cost_tier or 'Mid'}-tier estimated pricing."


def _resolve_weather_summary(trip, destination, provided: str | None) -> str:
    """Return caller's summary or fetch live Open-Meteo forecast."""
    if provided and provided.strip():
        return provided.strip()
    try:
        w = get_destination_weather(trip, destination)
        if w.get("days"):
            d0 = w["days"][0]
            avg_max = sum(d["temperature_max_c"] for d in w["days"] if d.get("temperature_max_c") is not None) / max(1, len(w["days"]))
            return f"{d0.get('description', 'Pleasant weather')}, approx {avg_max:.0f}°C average high"
        return w.get("message") or f"{destination.climate or 'Moderate'} climate"
    except Exception:
        return f"{destination.climate or 'Moderate'} climate"


def _require_joined_member(
    db: Session,
    trip_id: UUID,
    user: User,
) -> None:
    """Raise 404/403 if the trip is missing or the user is not a joined member."""
    trip = get_trip_by_id(db, trip_id)
    if trip is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trip not found",
        )

    member = get_trip_member(db, trip_id, user.id)
    if member is None or member.status != MemberStatus.JOINED.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You must be a joined member of this trip",
        )

    return trip


def _get_destination_or_404(db: Session, destination_id: UUID) -> Destination:
    dest = (
        db.query(Destination)
        .filter(Destination.id == destination_id)
        .first()
    )
    if dest is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Destination not found",
        )
    return dest


# ---------------------------------------------------------------------------
# Route handler
# ---------------------------------------------------------------------------


@router.post("/{action}")
def ai_action(
    trip_id: UUID,
    action: str,
    body: AiRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Invoke a Gemini AI action for the given trip.

    Actions:
      - ``explain``  — explain a single destination (requires destination_id)
      - ``compare``  — compare two destinations (requires destination_id +
                       destination_id_b)
      - ``summary``  — generate a full trip planning summary
    """

    # -- Auth ----------------------------------------------------------------
    trip = _require_joined_member(db, trip_id, current_user)

    # -- Load common data ----------------------------------------------------
    preferences = (
        db.query(TripPreference)
        .filter(TripPreference.trip_id == trip_id)
        .all()
    )
    member_count = len(preferences)
    preferences_summary = _build_preferences_summary(preferences)

    # -----------------------------------------------------------------------
    # Action: explain
    # -----------------------------------------------------------------------
    if action == "explain":
        if body.destination_id is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="destination_id is required for the 'explain' action",
            )

        destination = _get_destination_or_404(db, body.destination_id)

        # ML score and feature-match reasons
        ml_score: float | None = None
        reasons: list[str] = []
        if preferences:
            scores = score_destinations(
                preferences=preferences,
                destinations=[destination],
                traveler_type=trip.traveler_type,
            )
            ml_score = scores.get(destination.id)
            reasons = ml_explain(
                preferences=preferences,
                destination=destination,
                traveler_type=trip.traveler_type,
            )

        weather_str = _resolve_weather_summary(trip, destination, body.weather_summary)
        cost_str = _resolve_cost_summary(trip, destination, preferences, member_count, body.origin_city or "delhi", body.cost_summary)

        return ai_assistant_service.explain_destination(
            destination=destination,
            ml_score=ml_score,
            reasons=reasons,
            weather_summary=weather_str,
            cost_summary=cost_str,
            group_size=member_count,
            preferences_summary=preferences_summary,
        )

    # -----------------------------------------------------------------------
    # Action: compare
    # -----------------------------------------------------------------------
    if action == "compare":
        if body.destination_id is None or body.destination_id_b is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=(
                    "Both destination_id and destination_id_b are required "
                    "for the 'compare' action"
                ),
            )

        dest_a = _get_destination_or_404(db, body.destination_id)
        dest_b = _get_destination_or_404(db, body.destination_id_b)

        scores: dict = {}
        if preferences:
            scores = score_destinations(
                preferences=preferences,
                destinations=[dest_a, dest_b],
                traveler_type=trip.traveler_type,
            )

        origin = body.origin_city or "delhi"
        weather_a = _resolve_weather_summary(trip, dest_a, body.weather_summary)
        weather_b = _resolve_weather_summary(trip, dest_b, body.weather_summary_b)
        cost_a = _resolve_cost_summary(trip, dest_a, preferences, member_count, origin, body.cost_summary)
        cost_b = _resolve_cost_summary(trip, dest_b, preferences, member_count, origin, body.cost_summary_b)

        return ai_assistant_service.compare_destinations(
            dest_a=dest_a,
            dest_b=dest_b,
            scores=scores,
            weather_a=weather_a,
            weather_b=weather_b,
            cost_a=cost_a,
            cost_b=cost_b,
        )

    # -----------------------------------------------------------------------
    # Action: summary
    # -----------------------------------------------------------------------
    if action == "summary":
        # Fetch all trip candidate destinations
        trip_dest_rows = (
            db.query(TripDestination)
            .filter(TripDestination.trip_id == trip_id)
            .all()
        )
        destination_ids = [td.destination_id for td in trip_dest_rows]

        destinations: list[Destination] = []
        if destination_ids:
            destinations = (
                db.query(Destination)
                .filter(Destination.id.in_(destination_ids))
                .all()
            )

        # Build ML score mapping for top recommendation
        top_recommendation: str | None = None
        if preferences and destinations:
            scores = score_destinations(
                preferences=preferences,
                destinations=destinations,
                traveler_type=trip.traveler_type,
            )
            if scores:
                best_id = max(scores, key=lambda k: scores[k])
                best_dest = next(
                    (d for d in destinations if d.id == best_id), None
                )
                if best_dest:
                    top_recommendation = best_dest.name

        # Build vote results: destination name → vote count
        vote_results: dict[str, int] = {}
        if trip_dest_rows:
            td_id_to_name: dict[UUID, str] = {}
            td_id_map = {td.id: td.destination_id for td in trip_dest_rows}
            dest_id_to_name = {d.id: d.name for d in destinations}
            for td in trip_dest_rows:
                name = dest_id_to_name.get(td.destination_id, str(td.destination_id))
                td_id_to_name[td.id] = name

            votes = (
                db.query(TripVote)
                .filter(TripVote.trip_id == trip_id)
                .all()
            )
            for vote in votes:
                dest_name = td_id_to_name.get(vote.trip_destination_id, "Unknown")
                vote_results[dest_name] = vote_results.get(dest_name, 0) + 1

        return ai_assistant_service.generate_trip_summary(
            trip_name=trip.name,
            destinations=destinations,
            top_recommendation=top_recommendation,
            vote_results=vote_results,
            weather={},   # caller may pre-fetch and pass via future extension
            cost={},
            member_count=member_count,
            preferences_summary=preferences_summary,
        )

    # -----------------------------------------------------------------------
    # Unknown action
    # -----------------------------------------------------------------------
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=(
            f"Unknown action '{action}'. "
            "Valid actions are: explain, compare, summary"
        ),
    )
