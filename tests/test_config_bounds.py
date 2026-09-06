import pytest

from hotelareascore.config import DIMENSIONS, get_city, load_cities, load_score_weights


def test_pilot_cities_present():
    cities = load_cities()
    assert "london" in cities
    assert "bangkok" in cities


def test_city_bbox_is_well_formed():
    for city in load_cities().values():
        minx, miny, maxx, maxy = city.bbox
        assert minx < maxx
        assert miny < maxy
        assert -180 <= minx and maxx <= 180
        assert -90 <= miny and maxy <= 90


def test_unknown_city_raises():
    with pytest.raises(KeyError):
        get_city("atlantis")


def test_persona_weights_sum_to_one():
    weights = load_score_weights()
    for persona, w in weights["personas"].items():
        total = sum(w.values())
        assert abs(total - 1.0) < 1e-6, f"persona '{persona}' weights sum to {total}, expected 1.0"


def test_persona_weights_cover_all_dimensions():
    weights = load_score_weights()
    for persona, w in weights["personas"].items():
        assert set(w.keys()) == set(DIMENSIONS), f"persona '{persona}' has mismatched dimension keys"


def test_hybrid_absolute_weight_in_bounds():
    weights = load_score_weights()
    assert 0.0 <= weights["hybrid_absolute_weight"] <= 1.0


def test_decay_scales_positive():
    weights = load_score_weights()
    for dim, scale in weights["decay_scale_m"].items():
        assert scale > 0, f"decay scale for {dim} must be positive"


def test_confidence_weights_sum_to_one():
    weights = load_score_weights()
    total = sum(weights["confidence"]["weights"].values())
    assert abs(total - 1.0) < 1e-6


def test_quietness_penalties_non_negative():
    weights = load_score_weights()
    for name, p in weights["quietness"]["penalties"].items():
        assert p["weight"] >= 0
        assert p["scale_m"] > 0
