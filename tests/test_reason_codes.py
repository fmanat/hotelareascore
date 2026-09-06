from hotelareascore.reason_codes import compute_reason_codes

BASE_SCORES = {
    "walkability_density": 50,
    "transit_access": 50,
    "food_essentials": 50,
    "quietness_proxy": 50,
    "family_convenience": 50,
    "nightlife_access": 50,
}


def _scores(**overrides):
    return {**BASE_SCORES, **overrides}


def test_high_restaurant_density():
    codes = compute_reason_codes(_scores(food_essentials=80), confidence=90, nearby_facts=[])
    assert "HIGH_RESTAURANT_DENSITY" in codes


def test_good_transit_access():
    codes = compute_reason_codes(_scores(transit_access=75), confidence=90, nearby_facts=[])
    assert "GOOD_TRANSIT_ACCESS" in codes


def test_very_close_transit_from_nearby_facts():
    facts = [{"category": "train_station", "distance_m": 120, "name": "Central Station"}]
    codes = compute_reason_codes(_scores(), confidence=90, nearby_facts=facts)
    assert "VERY_CLOSE_TRANSIT" in codes


def test_not_very_close_transit_when_far():
    facts = [{"category": "train_station", "distance_m": 600, "name": "Central Station"}]
    codes = compute_reason_codes(_scores(), confidence=90, nearby_facts=facts)
    assert "VERY_CLOSE_TRANSIT" not in codes


def test_quiet_vs_busy_are_mutually_exclusive():
    quiet_codes = compute_reason_codes(_scores(quietness_proxy=90), confidence=90, nearby_facts=[])
    busy_codes = compute_reason_codes(_scores(quietness_proxy=10), confidence=90, nearby_facts=[])
    assert "QUIET_SURROUNDINGS" in quiet_codes and "BUSY_SURROUNDINGS" not in quiet_codes
    assert "BUSY_SURROUNDINGS" in busy_codes and "QUIET_SURROUNDINGS" not in busy_codes


def test_low_data_confidence_flag():
    codes = compute_reason_codes(_scores(), confidence=45, nearby_facts=[{"category": "cafe", "distance_m": 50, "name": "x"}] * 5)
    assert "LOW_DATA_CONFIDENCE" in codes


def test_limited_nearby_data_flag():
    codes = compute_reason_codes(_scores(), confidence=90, nearby_facts=[{"category": "cafe", "distance_m": 50, "name": "x"}])
    assert "LIMITED_NEARBY_DATA" in codes


def test_no_spurious_codes_at_neutral_scores():
    codes = compute_reason_codes(_scores(), confidence=90, nearby_facts=[{"category": "cafe", "distance_m": 50, "name": "x"}] * 5)
    assert codes == []
