"""Content-based destination scoring from trip preferences.

Accommodation preferences map directly to destination cost tiers because both
use the same ``budget``, ``mid``, and ``luxury`` values. Numeric budget ranges
are intentionally omitted: the application does not define their currency or
provide a comparable numeric destination budget.
"""

from collections.abc import Iterable, Sequence
from enum import Enum

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


_NO_CLIMATE_PREFERENCE = "no_preference"


def _value(value: object) -> str | None:
    raw_value = value.value if isinstance(value, Enum) else value
    if not isinstance(raw_value, str):
        return None
    normalized = raw_value.strip().lower()
    return normalized or None


def _values(value: object) -> Iterable[object]:
    if value is None:
        return ()
    if isinstance(value, (str, Enum)):
        return (value,)
    if isinstance(value, Iterable):
        return value
    return (value,)


def _features(item: object, fields: tuple[tuple[str, str], ...]) -> set[str]:
    features: set[str] = set()
    for attribute, feature_name in fields:
        for raw_value in _values(getattr(item, attribute, None)):
            normalized = _value(raw_value)
            if normalized is None:
                continue
            if (
                feature_name == "climate"
                and normalized == _NO_CLIMATE_PREFERENCE
            ):
                continue
            features.add(f"{feature_name}__{normalized}")
    return features


_PREFERENCE_FIELDS = (
    ("travel_style", "travel_style"),
    ("preferred_activities", "activity"),
    ("climate_preference", "climate"),
    ("accommodation_pref", "cost_tier"),
)

_DESTINATION_FIELDS = (
    ("suitable_travel_styles", "travel_style"),
    ("suitable_activities", "activity"),
    ("climate", "climate"),
    ("cost_tier", "cost_tier"),
    ("suitable_traveler_types", "traveler_type"),
)


def score_destinations(
    preferences: Sequence[object],
    destinations: Sequence[object],
    traveler_type: str | Enum | None = None,
) -> dict[object, float]:
    """Return mean member cosine similarity on a 0-100 scale, not a probability.

    The group-level ``traveler_type`` is optional because it belongs to a trip,
    not an individual preference record. When supplied, it is included in each
    member profile and compared with destination suitability metadata.
    """
    if not preferences or not destinations:
        return {}

    preference_features = [
        features
        for preference in preferences
        if (features := _features(preference, _PREFERENCE_FIELDS))
    ]
    if not preference_features:
        return {}

    group_traveler_type = _value(traveler_type)
    if group_traveler_type is not None:
        traveler_feature = f"traveler_type__{group_traveler_type}"
        for features in preference_features:
            features.add(traveler_feature)

    destination_features = [
        _features(destination, _DESTINATION_FIELDS)
        for destination in destinations
    ]
    scorable_indexes = [
        index for index, features in enumerate(destination_features) if features
    ]
    if not scorable_indexes:
        return {}

    # Keep category names in each token so, for example, "warm" climate cannot
    # accidentally match a "warm" text value from another attribute.
    vectorizer = TfidfVectorizer(
        lowercase=False,
        token_pattern=r"(?u)\S+",
    )
    documents = [
        " ".join(sorted(features))
        for features in preference_features + destination_features
    ]
    vectors = vectorizer.fit_transform(documents)
    member_count = len(preference_features)
    similarities = cosine_similarity(
        vectors[:member_count],
        vectors[member_count:],
    )

    scores: dict[object, float] = {}
    for index in scorable_indexes:
        destination_id = getattr(destinations[index], "id")
        scores[destination_id] = round(
            float(similarities[:, index].mean()) * 100,
            1,
        )
    return scores

def explain_destination(
    preferences: Sequence[object],
    destination: object,
    traveler_type: str | Enum | None = None,
) -> list[str]:
    """Explain matching feature tags used by the content recommender."""
    profiles = [
        features
        for preference in preferences
        if (features := _features(preference, _PREFERENCE_FIELDS))
    ]

    group_type = _value(traveler_type)
    if group_type:
        for features in profiles:
            features.add(f"traveler_type__{group_type}")

    destination_features = _features(destination, _DESTINATION_FIELDS)

    if not profiles or not destination_features:
        return ["Insufficient feature data to explain this recommendation."]

    labels = {
        "travel_style": "Travel styles",
        "activity": "Activities",
        "climate": "Climate",
        "cost_tier": "Accommodation tier",
    }

    reasons = []

    for feature, label in labels.items():
        prefix = f"{feature}__"
        destination_values = {
            token for token in destination_features
            if token.startswith(prefix)
        }

        if not destination_values:
            continue

        applicable_profiles = [
            profile for profile in profiles
            if any(token.startswith(prefix) for token in profile)
        ]

        if not applicable_profiles:
            continue

        matches = sum(
            bool(profile & destination_values)
            for profile in applicable_profiles
        )

        reasons.append(
            f"{label} match {matches} of "
            f"{len(applicable_profiles)} usable member profiles."
        )

    group_type_token = (
        f"traveler_type__{group_type}" if group_type else None
    )

    if group_type_token and any(
        token.startswith("traveler_type__")
        for token in destination_features
    ):
        if group_type_token in destination_features:
            reasons.append(
                "Destination suitability includes the trip's traveler type."
            )
        else:
            reasons.append(
                "Destination suitability does not list the trip's traveler type."
            )

    return reasons or [
        "No direct feature matches were found in the available metadata."
    ]
