"""Content-based destination scoring from trip preferences.

Accommodation preferences map directly to destination cost tiers because both
use the same ``budget``, ``mid``, and ``luxury`` values. Numeric budget ranges
are intentionally omitted: the application does not define their currency or
provide a comparable numeric destination budget.

Scoring notes:

* The TF-IDF vocabulary and IDF weights are fitted on destinations only, so a
  destination's score does not depend on how many members are in the group.
* Multi-word values (``"water sports"``) are collapsed into one token
  (``water_sports``) so each feature keeps its category prefix.
* Two scoring methods are available:
  - ``"cosine"`` (default): cosine similarity. Destinations with many tags
    are diluted relative to sparsely tagged ones.
  - ``"coverage"``: the IDF-weighted share of a member's wanted features that
    the destination offers. Extra destination tags are not penalised.
"""

from collections.abc import Iterable, Sequence
from enum import Enum

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


_NO_PREFERENCE = "no_preference"
_METHODS = ("cosine", "coverage")


def _value(value: object) -> str | None:
    raw_value = value.value if isinstance(value, Enum) else value
    if not isinstance(raw_value, str):
        return None
    # Collapse internal whitespace so "water sports" stays a single token.
    normalized = "_".join(raw_value.strip().lower().split())
    return normalized or None


def _values(value: object) -> Iterable[object]:
    if value is None:
        return ()
    if isinstance(value, str):
        # Accept comma-separated strings, e.g. "hiking, camping".
        return value.split(",")
    if isinstance(value, Enum):
        return (value,)
    if isinstance(value, Iterable):
        return value
    return (value,)


def _features(item: object, fields: tuple[tuple[str, str], ...]) -> set[str]:
    features: set[str] = set()
    for attribute, feature_name in fields:
        for raw_value in _values(getattr(item, attribute, None)):
            normalized = _value(raw_value)
            if normalized is None or normalized == _NO_PREFERENCE:
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
    method: str = "cosine",
) -> dict[object, float]:
    """Return mean member similarity on a 0-100 scale, not a probability.

    The group-level ``traveler_type`` is optional because it belongs to a trip,
    not an individual preference record. When supplied, it is included in each
    member profile and compared with destination suitability metadata.

    ``method`` is ``"cosine"`` or ``"coverage"`` (see module docstring).
    Destinations with no usable metadata are omitted from the result.
    """
    if method not in _METHODS:
        raise ValueError(f"method must be one of {_METHODS}, got {method!r}")

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
    if group_traveler_type is not None and group_traveler_type != _NO_PREFERENCE:
        traveler_feature = f"traveler_type__{group_traveler_type}"
        for features in preference_features:
            features.add(traveler_feature)

    scorable = []
    for destination in destinations:
        features = _features(destination, _DESTINATION_FIELDS)
        if features:
            scorable.append((destination, features))
    if not scorable:
        return {}

    # Keep category names in each token so, for example, "warm" climate cannot
    # accidentally match a "warm" text value from another attribute.
    vectorizer = TfidfVectorizer(
        lowercase=False,
        token_pattern=r"(?u)\S+",
    )

    # Fit on destinations only: IDF reflects the catalog, not the group size.
    destination_docs = [" ".join(sorted(features)) for _, features in scorable]
    destination_matrix = vectorizer.fit_transform(destination_docs)

    # Member features absent from every destination are ignored by transform.
    member_docs = [" ".join(sorted(features)) for features in preference_features]
    member_matrix = vectorizer.transform(member_docs)

    if method == "cosine":
        similarities = cosine_similarity(member_matrix, destination_matrix)
    else:
        # Weighted share of each member's wanted features that a destination
        # offers. Numerator uses a binary destination matrix.
        presence = (destination_matrix > 0).astype(float)
        matched = (member_matrix @ presence.T).toarray()
        totals = np.asarray(member_matrix.sum(axis=1)).reshape(-1, 1)
        similarities = np.divide(
            matched,
            totals,
            out=np.zeros_like(matched),
            where=totals > 0,
        )

    scores: dict[object, float] = {}
    for column, (destination, _) in enumerate(scorable):
        scores[destination.id] = round(
            float(similarities[:, column].mean()) * 100,
            1,
        )
    return scores