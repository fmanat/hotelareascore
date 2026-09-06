"""Deterministic reason codes (docs/scoring.md §6): human explanations must
derive from these, never from free-form LLM text about facts we didn't
compute (CLAUDE.md hard rule 3). Pure functions of already-persisted
hotel_scores + nearby_facts — no new computation, no new data source.
"""
from __future__ import annotations

from . import taxonomy

_TRANSIT_CATEGORIES = set(taxonomy.dimension_config("transit_access")["categories"])

HIGH = 75.0
GOOD = 70.0
LOW_CONFIDENCE = 60.0
QUIET = 80.0
BUSY = 40.0
VERY_CLOSE_TRANSIT_M = 250.0
SPARSE_DATA_THRESHOLD = 3


def compute_reason_codes(scores: dict, confidence: float, nearby_facts: list[dict]) -> list[str]:
    codes: list[str] = []

    if scores["food_essentials"] >= HIGH:
        codes.append("HIGH_RESTAURANT_DENSITY")
    if scores["transit_access"] >= GOOD:
        codes.append("GOOD_TRANSIT_ACCESS")
    if any(f["category"] in _TRANSIT_CATEGORIES and f["distance_m"] <= VERY_CLOSE_TRANSIT_M for f in nearby_facts):
        codes.append("VERY_CLOSE_TRANSIT")
    if scores["quietness_proxy"] >= QUIET:
        codes.append("QUIET_SURROUNDINGS")
    elif scores["quietness_proxy"] < BUSY:
        codes.append("BUSY_SURROUNDINGS")
    if scores["nightlife_access"] >= GOOD:
        codes.append("ACTIVE_NIGHTLIFE")
    if scores["family_convenience"] >= GOOD:
        codes.append("FAMILY_FRIENDLY_SURROUNDINGS")
    if confidence < LOW_CONFIDENCE:
        codes.append("LOW_DATA_CONFIDENCE")
    if len(nearby_facts) < SPARSE_DATA_THRESHOLD:
        codes.append("LIMITED_NEARBY_DATA")

    return codes
