"""Regression test for the transit_access NULL/least() bug (owner audit,
score_version 1.0.1): a hotel with zero matching POIs in radius must score
0 on every POI-based dimension, never a positive number from NULL-skipping
SQL functions. DuckDB's least()/greatest() skip NULL arguments instead of
propagating them (least(100.0, NULL) == 100.0), which is exactly what let
`_transit_dimension` return 100 for hotels with no transit stop nearby.

These tests exercise the real SQL in scoring.py against tiny synthetic
tables (no parquet, no network) so the invariant is checked directly against
the implementation, not re-derived by hand.
"""
from __future__ import annotations

import duckdb
import pytest

from hotelareascore import scoring
from hotelareascore.config import City, load_score_weights

CITY = City(id="testcity", name="Test City", country="XX", center_lat=51.5, center_lon=-0.1, bbox=(-0.2, 51.4, 0.0, 51.6))


@pytest.fixture
def con():
    c = duckdb.connect()
    c.execute("INSTALL spatial; LOAD spatial;")
    return c


def _empty_pois(con):
    con.execute(
        """
        CREATE TEMP TABLE pois AS
        SELECT * FROM (
            SELECT 'p'::VARCHAR AS id, 0.0::DOUBLE AS lat, 0.0::DOUBLE AS lon,
                   ''::VARCHAR AS taxonomy_primary, []::VARCHAR[] AS taxonomy_hierarchy,
                   ''::VARCHAR AS name
        ) WHERE FALSE
        """
    )


def _one_hotel(con, hotel_id="h1", lat=51.5, lon=-0.1):
    con.execute(f"CREATE TEMP TABLE hotels AS SELECT '{hotel_id}'::VARCHAR AS id, {lat}::DOUBLE AS lat, {lon}::DOUBLE AS lon")


def test_transit_access_is_zero_not_100_with_no_poi_nearby(con):
    _one_hotel(con)
    _empty_pois(con)
    weights = load_score_weights()

    scoring._transit_dimension(con, CITY, weights)

    row = con.execute("SELECT score, poi_count FROM dim_transit_access WHERE hotel_id = 'h1'").fetchone()
    assert row == (0.0, 0)


def test_transit_access_positive_with_one_nearby_stop(con):
    _one_hotel(con)
    con.execute(
        """
        CREATE TEMP TABLE pois AS
        SELECT 'p1' AS id, 51.5001 AS lat, -0.1001 AS lon, 'train_station' AS taxonomy_primary,
               ['travel_and_transportation', 'train_station'] AS taxonomy_hierarchy, 'Test Station' AS name
        """
    )
    weights = load_score_weights()

    scoring._transit_dimension(con, CITY, weights)

    row = con.execute("SELECT score, poi_count FROM dim_transit_access WHERE hotel_id = 'h1'").fetchone()
    assert row[0] > 0
    assert row[1] == 1


@pytest.mark.parametrize("dimension,diversity_bonus", [
    ("food_essentials", True),
    ("walkability_density", False),
    ("nightlife_access", False),
    ("family_convenience", False),
])
def test_density_dimensions_are_zero_with_no_poi_nearby(con, dimension, diversity_bonus):
    _one_hotel(con)
    _empty_pois(con)
    weights = load_score_weights()

    scoring._density_dimension(con, CITY, dimension, weights, diversity_bonus=diversity_bonus)

    row = con.execute(f"SELECT score, poi_count FROM dim_{dimension} WHERE hotel_id = 'h1'").fetchone()
    assert row[1] == 0
    assert row[0] == 0.0, f"{dimension}: expected score 0 with zero nearby POIs, got {row[0]}"


@pytest.mark.parametrize("dimension,category,hierarchy", [
    ("food_essentials", "restaurant", ["food_and_drink", "restaurant"]),
    ("walkability_density", "hair_salon", ["lifestyle_services", "hair_salon"]),
    ("nightlife_access", "bar", ["food_and_drink", "bar"]),
    ("family_convenience", "park", ["sports_and_recreation", "park"]),
])
def test_density_dimensions_positive_with_one_nearby_poi(con, dimension, category, hierarchy):
    _one_hotel(con)
    con.execute(
        f"""
        CREATE TEMP TABLE pois AS
        SELECT 'p1' AS id, 51.5001 AS lat, -0.1001 AS lon, '{category}' AS taxonomy_primary,
               {hierarchy} AS taxonomy_hierarchy, 'Test Place' AS name
        """
    )
    weights = load_score_weights()

    scoring._density_dimension(con, CITY, dimension, weights, diversity_bonus=False)

    row = con.execute(f"SELECT score, poi_count FROM dim_{dimension} WHERE hotel_id = 'h1'").fetchone()
    assert row[1] == 1
    assert row[0] > 0, f"{dimension}: expected a positive score with one nearby matching POI"
