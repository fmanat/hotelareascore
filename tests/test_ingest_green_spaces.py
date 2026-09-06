"""_green_spaces_sql (ingest.py) is where family_convenience's polygon
inclusion/exclusion actually happens (docs/adr/007) -- scoring.py trusts
whatever ends up in green_spaces.parquet without re-checking subtype/class.
These tests exercise the real predicate-building code against synthetic
land_use/land-shaped tables, so the exclusion list documented in
taxonomy-mapping.yml and docs/reports/family-v1.2.0-diagnostic.md is
actually enforced, not just described.
"""
from __future__ import annotations

import duckdb
import pytest

from hotelareascore import ingest

INCLUDED = [
    ("park", "park"),
    ("park", "village_green"),
    ("park", "dog_park"),
    ("protected", "nature_reserve"),
    ("recreation", "playground"),
    ("recreation", "pitch"),
    ("recreation", "track"),
    ("recreation", "recreation_ground"),
    ("managed", "grass"),
    ("entertainment", "zoo"),
]

EXCLUDED = [
    ("horticulture", "garden"),
    ("horticulture", "allotments"),
    ("golf", "fairway"),
    ("golf", "golf_course"),
    ("agriculture", "meadow"),
    ("agriculture", "farmland"),
    ("campground", "camp_site"),
    ("recreation", "stadium"),
    ("recreation", "marina"),
    ("residential", "residential"),
    ("education", "school"),
    ("cemetery", "cemetery"),
]

LAND_INCLUDED = [
    ("forest", "wood"),
    ("forest", "forest"),
    ("grass", "grass"),
    ("grass", "grassland"),
    ("grass", "meadow"),
    ("sand", "beach"),
]

LAND_EXCLUDED = [
    ("tree", "tree"),
    ("tree", "tree_row"),
    ("shrub", "scrub"),
    ("wetland", "wetland"),
    ("rock", "bare_rock"),
    ("physical", "cliff"),
    ("sand", "sand"),  # generic/desert sand, NOT the recreational 'beach' class
]


@pytest.fixture
def con():
    c = duckdb.connect()
    c.execute("INSTALL spatial; LOAD spatial;")
    return c


def test_land_use_included_classes_survive_the_filter(con):
    sql = _build_filtered_source(con, INCLUDED)
    assert len(sql) == len(INCLUDED)


def test_land_use_excluded_classes_are_dropped(con):
    sql = _build_filtered_source(con, EXCLUDED)
    assert len(sql) == 0


def test_land_included_classes_survive_the_filter(con):
    sql = _build_filtered_source(con, LAND_INCLUDED, land=True)
    assert len(sql) == len(LAND_INCLUDED)


def test_land_excluded_classes_are_dropped(con):
    sql = _build_filtered_source(con, LAND_EXCLUDED, land=True)
    assert len(sql) == 0


def _build_filtered_source(con, rows: list[tuple[str, str]], land: bool = False) -> list:
    """Runs the real predicate-building code from ingest.py against a
    synthetic table shaped like the land_use or land theme, and returns the
    surviving rows -- exercises the actual filter, not a re-description of
    it, so the test catches drift if ingest.py's predicate changes."""
    predicate = ingest.land_green_predicate() if land else ingest.land_use_green_predicate()

    con.execute(
        f"CREATE OR REPLACE TEMP TABLE source AS "
        f"SELECT * FROM (VALUES "
        + ", ".join(f"('r{i}', '{subtype}', '{cls}')" for i, (subtype, cls) in enumerate(rows))
        + ") AS t(id, subtype, class)"
    )
    return con.execute(f"SELECT id FROM source WHERE {predicate}").fetchall()
