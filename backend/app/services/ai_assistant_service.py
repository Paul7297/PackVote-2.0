"""Gemini-backed AI travel assistant for PackVote.

All HTTP calls use the standard library (urllib) so that no third-party SDK is
required.  Each public function returns a plain dict and *never* raises an
exception — callers receive an ``{"error": ..., "content": None}`` payload on
any failure instead.
"""

import json
import urllib.error
import urllib.request
from typing import Any

from app.core.config import settings

# ---------------------------------------------------------------------------
# Gemini REST endpoint (v1beta, gemini-flash-lite-latest)
# ---------------------------------------------------------------------------

_GEMINI_URL_TEMPLATE = (
    "https://generativelanguage.googleapis.com"
    "/v1beta/models/gemini-flash-lite-latest:generateContent?key={key}"
)

_TIMEOUT_SECONDS = 30

_SYSTEM_INSTRUCTION = (
    "You are a travel planning assistant for PackVote. "
    "Only discuss the provided structured evidence. "
    "Do not invent prices, weather data, or scores. "
    "Be concise (3-4 paragraphs)."
)

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _call_gemini(prompt: str) -> str | None:
    """POST *prompt* to the Gemini REST API and return the text response.

    Returns ``None`` if the key is empty or the call fails for any reason.
    """
    api_key = settings.gemini_api_key
    if not api_key:
        return None

    url = _GEMINI_URL_TEMPLATE.format(key=api_key)
    payload = {
        "system_instruction": {
            "parts": [{"text": _SYSTEM_INSTRUCTION}]
        },
        "contents": [{"parts": [{"text": prompt}]}],
    }
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=_TIMEOUT_SECONDS) as response:
            raw = response.read()
            data = json.loads(raw)
            return data["candidates"][0]["content"]["parts"][0]["text"]
    except (urllib.error.URLError, KeyError, IndexError, json.JSONDecodeError):
        return None


def _error_no_key() -> dict:
    return {
        "error": (
            "AI assistant is not configured. "
            "Add GEMINI_API_KEY to the backend .env file."
        ),
        "content": None,
    }


def _error_unavailable() -> dict:
    return {
        "error": "AI service temporarily unavailable.",
        "content": None,
    }


# ---------------------------------------------------------------------------
# Public functions
# ---------------------------------------------------------------------------


def explain_destination(
    destination: Any,
    ml_score: float | None,
    reasons: list[str],
    weather_summary: str,
    cost_summary: str,
    group_size: int,
    preferences_summary: str,
) -> dict:
    """Return a Gemini-generated explanation for a single destination.

    Args:
        destination: ORM Destination object (name, country, climate, cost_tier,
            suitable_activities).
        ml_score: ML cosine similarity score on 0-100 scale, or None.
        reasons: Feature-match reason strings from the content recommender.
        weather_summary: Pre-fetched weather description (caller-supplied).
        cost_summary: Pre-fetched cost description (caller-supplied).
        group_size: Number of group members.
        preferences_summary: Aggregated description of group preferences.

    Returns:
        dict with keys: type, destination, content, evidence_used
    """
    if not settings.gemini_api_key:
        return _error_no_key()

    score_text = (
        f"{ml_score:.1f} / 100 (ML cosine similarity score, not a probability)"
        if ml_score is not None
        else "Not available (insufficient destination metadata)"
    )

    activities = (
        ", ".join(destination.suitable_activities)
        if destination.suitable_activities
        else "Not specified"
    )

    reasons_text = "\n".join(f"  - {r}" for r in reasons) if reasons else "  - None"

    evidence_used = ["ml_score", "reasons", "weather", "cost", "preferences"]

    prompt = f"""You are evaluating a travel destination for a group trip.

=== Destination ===
Name: {destination.name}
Country: {destination.country or "Unknown"}
Climate: {destination.climate or "Unknown"}
Cost Tier: {destination.cost_tier or "Unknown"}
Suitable Activities: {activities}

=== ML Recommendation Score ===
{score_text}

=== ML Feature Match Reasons ===
{reasons_text}

=== Weather ===
{weather_summary or "No weather data provided"}

=== Cost Estimate ===
{cost_summary or "No cost data provided"}

=== Group Information ===
Group Size: {group_size} member(s)
Group Preference Summary: {preferences_summary or "Not provided"}

Based solely on the above structured evidence, write a concise 3-4 paragraph \
explanation of why {destination.name} may or may not suit this group. \
Reference the ML score, feature matches, weather, and cost directly. \
Do not invent any additional data."""

    content = _call_gemini(prompt)
    if content is None:
        return _error_unavailable()

    return {
        "type": "explanation",
        "destination": destination.name,
        "content": content,
        "evidence_used": evidence_used,
    }


def compare_destinations(
    dest_a: Any,
    dest_b: Any,
    scores: dict,
    weather_a: str,
    weather_b: str,
    cost_a: str,
    cost_b: str,
) -> dict:
    """Return a Gemini-generated side-by-side comparison of two destinations.

    Args:
        dest_a: First ORM Destination object.
        dest_b: Second ORM Destination object.
        scores: Mapping of destination id → ML score (0-100 or None).
        weather_a: Weather summary for dest_a.
        weather_b: Weather summary for dest_b.
        cost_a: Cost summary for dest_a.
        cost_b: Cost summary for dest_b.

    Returns:
        dict with keys: type, destinations, content
    """
    if not settings.gemini_api_key:
        return _error_no_key()

    def _score_text(dest: Any) -> str:
        dest_id = getattr(dest, "id", None)
        score = scores.get(dest_id) if dest_id is not None else None
        if score is None:
            score = scores.get(getattr(dest, "name", None))
        if score is None:
            return "Not available"
        return f"{score:.1f} / 100 (ML cosine similarity score, not a probability)"

    def _activities(dest: Any) -> str:
        acts = getattr(dest, "suitable_activities", None)
        return (
            ", ".join(acts)
            if acts
            else "Not specified"
        )

    prompt = f"""You are comparing two travel destinations for a group trip.

=== Destination A: {dest_a.name} ===
Country: {dest_a.country or "Unknown"}
Climate: {dest_a.climate or "Unknown"}
Cost Tier: {dest_a.cost_tier or "Unknown"}
Suitable Activities: {_activities(dest_a)}
ML Score: {_score_text(dest_a)}
Weather: {weather_a or "No weather data provided"}
Cost Estimate: {cost_a or "No cost data provided"}

=== Destination B: {dest_b.name} ===
Country: {dest_b.country or "Unknown"}
Climate: {dest_b.climate or "Unknown"}
Cost Tier: {dest_b.cost_tier or "Unknown"}
Suitable Activities: {_activities(dest_b)}
ML Score: {_score_text(dest_b)}
Weather: {weather_b or "No weather data provided"}
Cost Estimate: {cost_b or "No cost data provided"}

Based solely on the structured data above, write a concise 3-4 paragraph \
comparison of {dest_a.name} and {dest_b.name}. Highlight key differences in \
climate, cost, activities, and ML score. Do not invent any data."""

    content = _call_gemini(prompt)
    if content is None:
        return _error_unavailable()

    return {
        "type": "comparison",
        "destinations": [dest_a.name, dest_b.name],
        "content": content,
    }


def generate_trip_summary(
    trip_name: str,
    destinations: list[Any],
    top_recommendation: str | None,
    vote_results: dict,
    weather: dict,
    cost: dict,
    member_count: int,
    preferences_summary: str,
) -> dict:
    """Return a Gemini-generated summary for an entire group trip.

    Args:
        trip_name: Human-readable trip name.
        destinations: List of ORM Destination objects considered for the trip.
        top_recommendation: Name of the top-ranked destination (or None).
        vote_results: Mapping of destination name → vote count.
        weather: Mapping of destination name → weather summary string.
        cost: Mapping of destination name → cost summary string.
        member_count: Number of group members.
        preferences_summary: Aggregated description of group preferences.

    Returns:
        dict with keys: type, content
    """
    if not settings.gemini_api_key:
        return _error_no_key()

    dest_lines = []
    for dest in destinations:
        if isinstance(dest, str):
            name = dest
            country = "Unknown"
            climate = "Unknown"
            cost_tier = "Unknown"
        else:
            name = getattr(dest, "name", str(dest))
            country = getattr(dest, "country", None) or "Unknown"
            climate = getattr(dest, "climate", None) or "Unknown"
            cost_tier = getattr(dest, "cost_tier", None) or "Unknown"

        weather_str = weather.get(name, "No weather data") if isinstance(weather, dict) else (weather or "No weather data")
        cost_str = cost.get(name, "No cost data") if isinstance(cost, dict) else (cost or "No cost data")
        vote_count = vote_results.get(name, 0) if isinstance(vote_results, dict) else 0
        dest_lines.append(
            f"  - {name} | Country: {country} | "
            f"Climate: {climate} | "
            f"Cost Tier: {cost_tier} | "
            f"Votes: {vote_count} | Weather: {weather_str} | Cost: {cost_str}"
        )

    destinations_block = "\n".join(dest_lines) if dest_lines else "  (none listed)"

    votes_block = (
        "\n".join(f"  {name}: {count} vote(s)" for name, count in vote_results.items())
        if vote_results
        else "  No votes recorded"
    )

    prompt = f"""You are writing a trip planning summary for a group.

=== Trip: {trip_name} ===
Group Size: {member_count} member(s)
Group Preference Summary: {preferences_summary or "Not provided"}
Top ML Recommendation: {top_recommendation or "Not determined"}

=== Candidate Destinations ===
{destinations_block}

=== Vote Results ===
{votes_block}

Based solely on the structured data above, write a concise 3-4 paragraph \
summary of this group's trip planning. Describe the top candidates, the vote \
outcome, and how well the options match the group's stated preferences. \
Do not invent any data."""

    content = _call_gemini(prompt)
    if content is None:
        return _error_unavailable()

    return {
        "type": "trip_summary",
        "content": content,
    }
