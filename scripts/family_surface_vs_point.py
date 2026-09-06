#!/usr/bin/env python3
"""Surface-vs-point hypothesis test for the family_convenience anomaly
(owner instruction, follow-up to the §4.2 calibration). family_convenience
currently counts POINTS from Overture's `places` theme (park/playground/
zoo/aquarium categories) within 600m. Overture's `base/land_use` theme has
the actual polygon footprints for the same real-world features (subtype
`park`, `recreation` incl. `playground`) but our pipeline never ingests it
(confirmed: src/hotelareascore/ingest.py only reads theme=places and
theme=transportation). Hypothesis: some hotels score 0 on family_convenience
not because there is no nearby park, but because the point-based extract
has no point placed close enough to the hotel, even though a park polygon
exists nearby.

Read-only, ad-hoc analysis: queries the live Overture release directly,
writes a report, changes nothing in the pipeline or its outputs.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import duckdb

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

RELEASE = "2026-08-19.0"
RADIUS_M = 600  # matches taxonomy-mapping.yml family_convenience.radius_m

# The golden-set hotels whose computed family_convenience == 0.0 despite a
# label of 1-5 (i.e. Claude judged *some* family-relevant quality present).
CASES = [
    ("Lisboa Camping & Bungalows", "lisbon", 38.724632263183594, -9.207444190979004, 5),
    ("Le Relais de la Malmaison", "paris", 48.88044357299805, 2.163088083267212, 4),
    ("Changi Lodge", "singapore", 1.3126510381698608, 103.99707794189453, 4),
    ("Ardra Guest House", "london", 51.343299865722656, -0.13348673284053802, 3),
    ("Premia de Mar", "barcelona", 41.3607292175293, 2.1648099422454834, 3),
    ("ホテルCOCO", "tokyo", 35.779666900634766, 139.88726806640625, 3),
    ("Strathfield Hotel", "sydney", -33.87153244018555, 151.09506225585938, 2),
    ("Dusit Thani Dubai", "dubai", 25.06233024597168, 55.1302490234375, 2),
    ("Le Meridien Fairway", "dubai", 25.234235763549805, 55.338829040527344, 2),
    ("OC Hotel", "rome", 41.93758010864258, 12.619841575622559, 1),
    ("Airport Hotels Bangkok Travel Service", "bangkok", 13.703900337219238, 100.7534408569336, 1),
]

# rough meters-per-degree at each latitude, close enough for a bbox margin
def degree_margin(radius_m: float, lat: float) -> tuple[float, float]:
    import math
    dlat = radius_m / 111_320
    dlon = radius_m / (111_320 * max(0.1, math.cos(math.radians(lat))))
    return dlat, dlon


def main() -> None:
    con = duckdb.connect()
    con.execute("INSTALL httpfs; LOAD httpfs; INSTALL spatial; LOAD spatial;")
    con.execute("SET s3_region='us-west-2';")
    landuse_path = f"s3://overturemaps-us-west-2/release/{RELEASE}/theme=base/type=land_use/*"

    results = []
    for name, city, lat, lon, label in CASES:
        dlat, dlon = degree_margin(RADIUS_M * 2, lat)  # generous margin for the bbox prefilter
        cos_lat = __import__("math").cos(__import__("math").radians(lat))
        # Distance from the hotel to each polygon's bbox center, in meters
        # (equirectangular, same spirit as src/hotelareascore/geo.py's
        # per-city projection but done inline since this is a one-off
        # analysis, not a pipeline change). This is a deliberately
        # conservative proxy for "distance to the polygon": the bbox center
        # of a park is never closer to the hotel than the polygon's nearest
        # edge, so a polygon that still shows up within radius on this
        # measure is genuinely nearby.
        sql3 = f"""
            SELECT names.primary AS name, subtype, class,
                   (bbox.xmin + bbox.xmax) / 2 AS cx,
                   (bbox.ymin + bbox.ymax) / 2 AS cy,
                   ST_Area(geometry) AS area_deg2
            FROM read_parquet('{landuse_path}')
            WHERE bbox.xmin BETWEEN {lon - dlon} AND {lon + dlon}
              AND bbox.ymin BETWEEN {lat - dlat} AND {lat + dlat}
              AND ((subtype = 'park') OR (subtype = 'recreation' AND class = 'playground'))
        """
        rows3 = con.execute(sql3).fetchall()
        nearby = []
        for poly_name, subtype, cls, cx, cy, area_deg2 in rows3:
            dx = (cx - lon) * 111320 * cos_lat
            dy = (cy - lat) * 111320
            dist_m = (dx ** 2 + dy ** 2) ** 0.5
            area_m2 = area_deg2 * (111320 * 111320 * cos_lat)
            if dist_m <= RADIUS_M * 1.5:  # generous since this is bbox-center distance, not boundary
                nearby.append({"name": poly_name, "subtype": subtype, "class": cls,
                                "approx_dist_to_bbox_center_m": round(dist_m), "approx_area_m2": round(area_m2)})
        nearby.sort(key=lambda r: r["approx_dist_to_bbox_center_m"])
        print(f"{name} ({city}, label={label}): {len(nearby)} land_use park/playground polygon(s) within ~{int(RADIUS_M*1.5)}m")
        for n in nearby[:5]:
            print(f"    {n}")
        results.append({"hotel": name, "city": city, "label": label, "nearby_land_use_polygons": nearby})

    out_path = Path(__file__).resolve().parents[1] / "docs/reports/phase-3-family-surface-vs-point.json"
    out_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"\nWrote {out_path}")


if __name__ == "__main__":
    main()
