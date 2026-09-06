"""Local-metric geometry helpers.

Web Mercator (EPSG:3857) "meters" are inflated by secant(latitude) — at
London's 51.5N that is a ~1.6x distortion, at Bangkok's 13.8N it is
negligible (~1.03x). Using it directly would bias every proximity-based
dimension between the two pilot cities and violate the "no systematic city
bias" check in docs/scoring.md §4.2. Instead we project to a per-city
equirectangular (Plate Carree) CRS centered on the city, which is accurate to
well under 1% at city scale and free of latitude-dependent skew between
cities.
"""
from __future__ import annotations

import math

from .config import City


def equirect_proj4(city: City) -> str:
    return (
        f"+proj=eqc +lat_ts={city.center_lat} +lon_0={city.center_lon} "
        "+x_0=0 +y_0=0 +ellps=WGS84 +units=m"
    )


def project_sql(geom_expr: str, city: City) -> str:
    """SQL expression projecting `geom_expr` (WGS84 geometry) to city-local meters."""
    proj4 = equirect_proj4(city)
    return f"ST_Transform({geom_expr}, 'EPSG:4326', '{proj4}', always_xy := true)"


def degree_margin(radius_m: float, city: City, safety_factor: float = 1.3) -> tuple[float, float]:
    """(dlat, dlon) degree half-widths that safely bound `radius_m` around city.center.

    Used only as a cheap pre-filter before the exact projected-distance test;
    the safety_factor covers longitude convergence error across a city's
    latitude span.
    """
    dlat = (radius_m * safety_factor) / 111_320.0
    dlon = (radius_m * safety_factor) / (111_320.0 * max(math.cos(math.radians(city.center_lat)), 0.01))
    return dlat, dlon


def decay_sql(distance_expr: str, scale_m: float) -> str:
    return f"exp(-({distance_expr}) / {scale_m})"
