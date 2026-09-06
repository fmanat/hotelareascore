from hotelareascore.verdict import band_for, build_verdict, quiet_clause_for

FORBIDDEN_WORDS = ("safe", "silent", "best", "perfect", "guaranteed")

BASE_SCORES = {
    "walkability_density": 0,
    "transit_access": 0,
    "food_essentials": 0,
    "family_convenience": 0,
    "nightlife_access": 0,
    "quietness_proxy": 50,
}


def _scores(**overrides):
    return {**BASE_SCORES, **overrides}


def test_band_thresholds():
    assert band_for(90) == "Excellent"
    assert band_for(70) == "Good"
    assert band_for(55) == "Decent"
    assert band_for(49) is None


def test_quiet_clause_bands():
    assert "quiet" in quiet_clause_for(90)
    assert "busy" in quiet_clause_for(10)
    assert quiet_clause_for(60) not in ("quiet surroundings", "busy surroundings")


def test_build_verdict_high_scores_mentions_top_dimensions():
    scores = _scores(walkability_density=90, food_essentials=85, quietness_proxy=85)
    verdict = build_verdict(scores)
    assert "walking to everyday places" in verdict
    assert "restaurants and everyday essentials" in verdict
    assert "quiet surroundings" in verdict


def test_build_verdict_low_scores_falls_back_to_mixed():
    verdict = build_verdict(_scores(quietness_proxy=50))
    assert verdict.startswith("Mixed surroundings")


def test_build_verdict_never_uses_forbidden_brand_words():
    for quiet in (10, 50, 90):
        for lead in (10, 60, 95):
            scores = _scores(walkability_density=lead, transit_access=lead, quietness_proxy=quiet)
            verdict = build_verdict(scores).lower()
            for word in FORBIDDEN_WORDS:
                assert word not in verdict, f"forbidden word '{word}' in: {verdict}"


def test_build_verdict_ends_with_period_and_is_capitalized():
    verdict = build_verdict(_scores(walkability_density=90, quietness_proxy=90))
    assert verdict.endswith(".")
    assert verdict[0].isupper()


def test_build_verdict_never_leads_with_nightlife():
    # docs/strategy.md §2: nightlife_access is "positive only for that
    # persona" -- it must never win a lead-clause slot in the default verdict,
    # even when it's the single highest-scoring dimension by far.
    scores = _scores(nightlife_access=99, walkability_density=10, quietness_proxy=50)
    verdict = build_verdict(scores)
    assert "nightlife" not in verdict.lower()


def test_build_verdict_never_self_contradicts_on_nightlife_vs_quiet():
    # Owner audit repro: 25 bars < 250m (high nightlife_access) alongside a
    # high quietness_proxy (the penalty only looks at the nearest venue --
    # docs/scoring.md §4.3 backlog) used to produce "Excellent for nightlife;
    # ...; quiet surroundings" in the same sentence.
    scores = _scores(nightlife_access=95, quietness_proxy=85, walkability_density=20)
    verdict = build_verdict(scores)
    assert not ("nightlife" in verdict.lower() and "quiet surroundings" in verdict.lower())
