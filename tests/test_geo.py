import math

from hotelareascore.config import City
from hotelareascore.geo import decay_sql, degree_margin, equirect_proj4

LONDON = City(id="london", name="London", country="GB", center_lat=51.5074, center_lon=-0.1278, bbox=(-0.52, 51.29, 0.33, 51.68))
BANGKOK = City(id="bangkok", name="Bangkok", country="TH", center_lat=13.7563, center_lon=100.5018, bbox=(100.32, 13.55, 100.93, 13.95))


def _eval_sql_expr(expr: str) -> float:
    return eval(expr, {"exp": math.exp})


def test_decay_sql_is_one_at_zero_distance():
    assert _eval_sql_expr(decay_sql("0", 250)) == 1.0


def test_decay_sql_decays_with_distance():
    near = _eval_sql_expr(decay_sql("50", 250))
    far = _eval_sql_expr(decay_sql("500", 250))
    assert 0 < far < near < 1


def test_degree_margin_shrinks_longitude_at_high_latitude():
    # At London's latitude (51.5N), a given radius needs MORE degrees of
    # longitude than the same radius at Bangkok's latitude (13.8N) — this is
    # exactly the distortion geo.py exists to route around (see geo.py
    # module docstring): verifies the margin helper reflects cos(latitude)
    # correctly rather than treating both cities the same.
    _, dlon_london = degree_margin(500, LONDON)
    _, dlon_bangkok = degree_margin(500, BANGKOK)
    assert dlon_london > dlon_bangkok


def test_degree_margin_positive():
    dlat, dlon = degree_margin(400, LONDON)
    assert dlat > 0 and dlon > 0


def test_equirect_proj4_centers_on_city():
    proj4 = equirect_proj4(LONDON)
    assert f"lat_ts={LONDON.center_lat}" in proj4
    assert f"lon_0={LONDON.center_lon}" in proj4
    assert "ellps=WGS84" in proj4
