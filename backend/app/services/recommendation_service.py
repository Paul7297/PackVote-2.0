import logging
from uuid import UUID

from sqlalchemy.orm import Session

from app.ml.content_recommender import explain_destination, score_destinations
from app.models.destination import Destination
from app.models.trip import Trip
from app.models.trip_destination import TripDestination
from app.models.trip_preference import TripPreference
from app.services.cost_estimation_service import generate_destination_summary

logger = logging.getLogger(__name__)

# Summaries can be slow (weather / cost lookups), so only the top N
# ranked destinations get one.
TOP_N_SUMMARIES = 5


def _normalise(value) -> str:
    return str(value).strip().lower() if value is not None else ""


def _normalise_list(values) -> set[str]:
    """Normalise a list-like column. Comma-separated strings are also accepted."""
    if isinstance(values, str):
        values = values.split(",")
    if not isinstance(values, (list, tuple, set)):
        return set()
    return {
        _normalise(value)
        for value in values
        if _normalise(value)
    }


def _missing_destination_metadata(destination) -> list[str]:
    """Identify destination fields needed for scoring."""
    missing = []

    if not _normalise(destination.cost_tier):
        missing.append("cost_tier")

    if not _normalise(destination.climate):
        missing.append("climate")

    if not _normalise_list(destination.suitable_travel_styles):
        missing.append("suitable_travel_styles")

    if not _normalise_list(destination.suitable_activities):
        missing.append("suitable_activities")

    if not _normalise_list(destination.suitable_traveler_types):
        missing.append("suitable_traveler_types")

    return missing


def _count_members(preferences) -> int:
    """
    Count distinct members who submitted preferences.
    Falls back to the row count if rows carry no user_id.
    """
    user_ids = {
        getattr(pref, "user_id", None)
        for pref in preferences
        if getattr(pref, "user_id", None) is not None
    }
    return max(1, len(user_ids) if user_ids else len(preferences))


def recommend_destinations(
    db: Session,
    trip_id: UUID,
    origin_city: str = "delhi",
) -> list[dict]:
    """
    Rank catalog destinations using the ML TF-IDF recommender model.
    Scores represent scaled cosine similarities (0-100).
    Existing trip candidates are excluded from recommendations.
    Summaries are generated only for the top TOP_N_SUMMARIES results.

    Raises ValueError if the trip is not found or has no preferences;
    the caller should map these to 404 / 400 responses.
    """
    origin_city = _normalise(origin_city) or "delhi"

    trip = db.query(Trip).filter(Trip.id == trip_id).first()

    if trip is None:
        raise ValueError("Trip not found")

    preferences = (
        db.query(TripPreference)
        .filter(TripPreference.trip_id == trip_id)
        .all()
    )

    existing_rows = (
        db.query(TripDestination.destination_id)
        .filter(TripDestination.trip_id == trip_id)
        .all()
    )
    existing_ids = {row[0] for row in existing_rows}

    # The full catalog is loaded (not filtered in SQL) so the ML scorer
    # sees the same corpus regardless of which destinations are already
    # on the trip. Existing candidates are dropped from the output below.
    destinations = (
        db.query(Destination)
        .order_by(Destination.name.asc())
        .all()
    )

    # Trip-level checks and values do not change per destination.
    trip_missing = []
    if not _normalise(trip.traveler_type):
        trip_missing.append("trip.traveler_type")

    member_count = _count_members(preferences)

    # 1. Invoke the machine learning TF-IDF content recommender if preferences exist
    ml_scores = {}
    if preferences:
        ml_scores = score_destinations(
            preferences=preferences,
            destinations=destinations,
            traveler_type=trip.traveler_type,
        )

    recommendations = []

    for destination in destinations:
        if destination.id in existing_ids:
            continue

        # 2. Extract ML similarity score (returns None if unscoreable or no preferences yet)
        group_score = ml_scores.get(destination.id)

        missing_attributes = _missing_destination_metadata(destination) + trip_missing

        if group_score is None:
            metadata_status = "insufficient"
        elif missing_attributes:
            metadata_status = "partial"
        else:
            metadata_status = "complete"

        # 3. Generate ML feature-match explanations
        if preferences:
            reasons = explain_destination(
                preferences=preferences,
                destination=destination,
                traveler_type=trip.traveler_type,
            )
            if group_score is None:
                reasons.insert(
                    0,
                    "No ML similarity score is available for this destination.",
                )
        else:
            reasons = [
                "Group preferences have not been submitted yet. Submit preferences to calculate personalized ML similarity scores."
            ]

        if missing_attributes:
            reasons.append(
                "Missing metadata: " + ", ".join(missing_attributes)
            )

        try:
            summary = generate_destination_summary(
                trip=trip,
                destination=destination,
                preferences=preferences,
                member_count=member_count,
                ml_score=group_score,
                origin_city=origin_city,
            )
        except Exception:
            logger.exception("Summary generation failed for destination %s", destination.id)
            summary = None

        recommendations.append({
            "destination_id": destination.id,
            "name": destination.name,
            "compatibility_score": group_score,
            "reasons": reasons,
            "metadata_status": metadata_status,
            "missing_attributes": missing_attributes,
            "summary": summary,
        })

    # Scored destinations appear first. Unscored entries are ordered by name.
    recommendations.sort(
        key=lambda item: (
            item["compatibility_score"] is None,
            -(item["compatibility_score"] or 0),
            item["name"].lower(),
        )
    )

    return recommendations