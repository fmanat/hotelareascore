"""Load and validate the YAML configs under data/config/.

Config is data, never hardcoded in the pipeline or the UI (docs/scoring.md
§3) — this module is the single place that reads it.
"""
from __future__ import annotations

import functools
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
CONFIG_DIR = REPO_ROOT / "data" / "config"
ETL_DIR = REPO_ROOT / "data" / "etl"
REPORTS_DIR = REPO_ROOT / "docs" / "reports"


def _load_yaml(name: str) -> dict[str, Any]:
    path = CONFIG_DIR / name
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        raise ValueError(f"{path} did not parse to a mapping")
    return data


@dataclass(frozen=True)
class City:
    id: str
    name: str
    country: str
    center_lat: float
    center_lon: float
    bbox: tuple[float, float, float, float]  # minx, miny, maxx, maxy


@functools.lru_cache(maxsize=1)
def load_cities() -> dict[str, City]:
    raw = _load_yaml("cities.yml")["cities"]
    cities: dict[str, City] = {}
    for c in raw:
        bbox = c["bbox"]
        city = City(
            id=c["id"],
            name=c["name"],
            country=c["country"],
            center_lat=float(c["center"]["lat"]),
            center_lon=float(c["center"]["lon"]),
            bbox=(float(bbox["minx"]), float(bbox["miny"]), float(bbox["maxx"]), float(bbox["maxy"])),
        )
        if not (-90 <= city.center_lat <= 90 and -180 <= city.center_lon <= 180):
            raise ValueError(f"city {city.id}: center out of range")
        minx, miny, maxx, maxy = city.bbox
        if not (minx < maxx and miny < maxy):
            raise ValueError(f"city {city.id}: invalid bbox {city.bbox}")
        cities[city.id] = city
    return cities


def get_city(city_id: str) -> City:
    cities = load_cities()
    if city_id not in cities:
        raise KeyError(f"Unknown city '{city_id}'. Known: {sorted(cities)}")
    return cities[city_id]


@functools.lru_cache(maxsize=1)
def load_taxonomy_mapping() -> dict[str, Any]:
    return _load_yaml("taxonomy-mapping.yml")


@functools.lru_cache(maxsize=1)
def load_score_weights() -> dict[str, Any]:
    return _load_yaml("score-weights.yml")


DIMENSIONS = (
    "walkability_density",
    "transit_access",
    "food_essentials",
    "quietness_proxy",
    "family_convenience",
    "nightlife_access",
)
