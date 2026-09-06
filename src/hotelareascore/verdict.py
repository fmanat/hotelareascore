"""Deterministic verdict sentence (docs/strategy.md §2: "Excellent for
walking and restaurants; strong transit; active surroundings" beats
"82/100"). Template-based from already-persisted dimension scores only — no
LLM, no free text (CLAUDE.md §7). Brand language never uses "safe", "silent",
"best", "perfect", "guaranteed", or an exact noise claim (docs/strategy.md §1)
— band/clause labels below are chosen to avoid all of them.
"""
from __future__ import annotations

LABELS = {
    "walkability_density": "walking to everyday places",
    "transit_access": "transit access",
    "food_essentials": "restaurants and everyday essentials",
    "family_convenience": "family convenience",
    "nightlife_access": "nightlife",
}

_LEAD_DIMENSIONS = tuple(LABELS.keys())


def band_for(score: float) -> str | None:
    if score >= 80:
        return "Excellent"
    if score >= 65:
        return "Good"
    if score >= 50:
        return "Decent"
    return None


def quiet_clause_for(quietness_score: float) -> str:
    if quietness_score >= 80:
        return "quiet surroundings"
    if quietness_score < 40:
        return "busy surroundings"
    return "moderate surrounding activity"


def build_verdict(scores: dict) -> str:
    candidates = sorted(((dim, scores[dim]) for dim in _LEAD_DIMENSIONS), key=lambda x: -x[1])
    clauses: list[str] = []
    for dim, score in candidates[:2]:
        band = band_for(score)
        if band:
            clauses.append(f"{band.lower()} for {LABELS[dim]}")
    clauses.append(quiet_clause_for(scores["quietness_proxy"]))

    if len(clauses) == 1:
        # every lead dimension scored below the "Decent" floor
        return f"Mixed surroundings; {clauses[0]} — see the full scores below."

    sentence = "; ".join(clauses)
    return sentence[0].upper() + sentence[1:] + "."
