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

# nightlife_access is deliberately NOT a lead-clause candidate for the
# default/balanced verdict: docs/strategy.md §2 marks it "positive only for
# that persona", and it also drives one of the quietness penalty terms
# (score-weights.yml quietness.penalties.nightlife) — a hotel can quite
# legitimately have high nightlife_access (a bar right next door) and a high
# quietness_proxy at the same time (the penalty only looks at the *nearest*
# venue, docs/scoring.md sensitivity backlog), which produced a
# self-contradictory sentence like "Excellent for nightlife; ...; quiet
# surroundings" when nightlife led. Excluding it here is a presentation fix;
# the underlying quietness-vs-nightlife prior is tracked separately, not
# tuned by this change (docs/scoring.md §4.3).
_LEAD_DIMENSIONS = tuple(d for d in LABELS if d != "nightlife_access")


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
