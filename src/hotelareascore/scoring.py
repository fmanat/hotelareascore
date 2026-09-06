"""Phase 1 scoring: ETL parquet (hotels, pois, segments) -> hotel_scores +
nearby_facts, computed entirely in DuckDB SQL against the local-metric
projection in geo.py.

docs/scoring.md v1 status applies to every constant pulled from
data/config/score-weights.yml: "educated prior, not validated." This module
is the reference implementation of the formulas documented there; do not let
the two drift apart without bumping score_version (docs/adr/004).
"""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from . import geo, overture, taxonomy
from .config import City, DIMENSIONS, get_city, load_score_weights

# family_convenience moved to its own dedicated function in score_version
# 1.1.0 (docs/adr/006): it now combines points (zoo/aquarium) with land_use
# polygons (park/playground), which the generic point-only _density_dimension
# below can't express.
DENSITY_DIMENSIONS = ("food_essentials", "walkability_density", "nightlife_access")


def _open_city_tables(con, etl_dir: Path) -> None:
    con.execute(f"CREATE OR REPLACE TEMP TABLE hotels AS SELECT * FROM read_parquet('{etl_dir / 'hotels.parquet'}')")
    con.execute(f"CREATE OR REPLACE TEMP TABLE pois AS SELECT * FROM read_parquet('{etl_dir / 'pois.parquet'}')")
    con.execute(f"CREATE OR REPLACE TEMP TABLE segments AS SELECT * FROM read_parquet('{etl_dir / 'segments.parquet'}')")
    con.execute(f"CREATE OR REPLACE TEMP TABLE green_spaces AS SELECT * FROM read_parquet('{etl_dir / 'green_spaces.parquet'}')")


def _density_dimension(con, city: City, dimension: str, weights: dict[str, Any], diversity_bonus: bool) -> None:
    cfg = taxonomy.dimension_config(dimension)
    radius_m = cfg["radius_m"]
    decay_scale_m = weights["decay_scale_m"][dimension]
    saturation = weights["absolute_saturation"][dimension]
    hybrid_w = weights["hybrid_absolute_weight"]
    predicate = taxonomy.poi_sql_predicate(dimension, primary_col="p.taxonomy_primary", hierarchy_col="p.taxonomy_hierarchy")
    dlat, dlon = geo.degree_margin(radius_m, city)
    proj_h = geo.project_sql("ST_Point(h.lon, h.lat)", city)
    proj_p = geo.project_sql("ST_Point(p.lon, p.lat)", city)

    raw_sql = f"""
        WITH within AS (
            SELECT h.id AS hotel_id,
                   ST_Distance({proj_h}, {proj_p}) AS d,
                   p.taxonomy_primary AS cat
            FROM hotels h
            JOIN pois p
              ON p.lon BETWEEN h.lon - {dlon} AND h.lon + {dlon}
             AND p.lat BETWEEN h.lat - {dlat} AND h.lat + {dlat}
             AND {predicate}
        ),
        within_r AS (SELECT * FROM within WHERE d <= {radius_m}),
        agg AS (
            SELECT hotel_id,
                   sum({geo.decay_sql('d', decay_scale_m)}) AS raw_weighted_count,
                   count(*) AS poi_count,
                   count(DISTINCT cat) AS distinct_categories,
                   min(d) AS nearest_m
            FROM within_r GROUP BY hotel_id
        )
        SELECT h.id AS hotel_id,
               coalesce(a.raw_weighted_count, 0.0) AS raw_weighted_count,
               coalesce(a.poi_count, 0) AS poi_count,
               coalesce(a.distinct_categories, 0) AS distinct_categories,
               a.nearest_m
        FROM hotels h LEFT JOIN agg a ON a.hotel_id = h.id
    """
    diversity_expr = (
        "raw_weighted_count * (1 + 0.1 * least(distinct_categories, 8))" if diversity_bonus else "raw_weighted_count"
    )
    con.execute(f"CREATE OR REPLACE TEMP TABLE _dim_raw_{dimension} AS {raw_sql}")
    con.execute(
        f"""
        CREATE OR REPLACE TEMP TABLE dim_{dimension} AS
        SELECT hotel_id,
               wc,
               100.0 * (1 - exp(-wc / {saturation})) AS absolute_score,
               percent_rank() OVER (ORDER BY wc) * 100 AS city_percentile,
               {hybrid_w} * (100.0 * (1 - exp(-wc / {saturation})))
                 + {1 - hybrid_w} * (percent_rank() OVER (ORDER BY wc) * 100) AS score,
               poi_count, distinct_categories, nearest_m
        FROM (SELECT hotel_id, {diversity_expr} AS wc, poi_count, distinct_categories, nearest_m
              FROM _dim_raw_{dimension})
        """
    )


def _family_convenience_dimension(con, city: City, weights: dict[str, Any]) -> None:
    """family_convenience v2 (score_version 1.1.0, docs/adr/006): combines
    two POI sources into the same weighted-count -> saturating-curve ->
    city-percentile hybrid every other density dimension uses (only the
    source changed, not the formula shape or its constants):
      - points (zoo/aquarium, Overture `places`) -- no polygon footprint
        exists for these in Overture's base theme, so point distance is the
        only option;
      - green-space polygons (park/playground, Overture `base/land_use`) --
        distance is measured to the polygon's own boundary via ST_Distance
        (0 if the hotel is inside it), not to a centroid or a single
        places-theme point, which is what caused 9/11 golden-set hotels with
        a real nearby park to score exactly 0
        (docs/reports/phase-3-family-surface-vs-point.json).
    """
    dim = "family_convenience"
    cfg = taxonomy.dimension_config(dim)
    radius_m = cfg["radius_m"]
    decay_scale_m = weights["decay_scale_m"][dim]
    saturation = weights["absolute_saturation"][dim]
    hybrid_w = weights["hybrid_absolute_weight"]
    point_predicate = taxonomy.poi_sql_predicate(dim, primary_col="p.taxonomy_primary", hierarchy_col="p.taxonomy_hierarchy")
    dlat, dlon = geo.degree_margin(radius_m, city)
    proj_h = geo.project_sql("ST_Point(h.lon, h.lat)", city)
    proj_p = geo.project_sql("ST_Point(p.lon, p.lat)", city)
    proj_g = geo.project_sql("ST_GeomFromText(g.geometry_wkt)", city)

    sql = f"""
        WITH point_hit AS (
            SELECT h.id AS hotel_id, ST_Distance({proj_h}, {proj_p}) AS d, p.taxonomy_primary AS cat
            FROM hotels h
            JOIN pois p
              ON p.lon BETWEEN h.lon - {dlon} AND h.lon + {dlon}
             AND p.lat BETWEEN h.lat - {dlat} AND h.lat + {dlat}
             AND {point_predicate}
        ),
        green_hit AS (
            SELECT h.id AS hotel_id, ST_Distance({proj_h}, {proj_g}) AS d, g.subtype AS cat
            FROM hotels h
            JOIN green_spaces g
              ON g.bbox_xmin <= h.lon + {dlon} AND g.bbox_xmax >= h.lon - {dlon}
             AND g.bbox_ymin <= h.lat + {dlat} AND g.bbox_ymax >= h.lat - {dlat}
        ),
        combined AS (
            SELECT hotel_id, d, cat FROM point_hit WHERE d <= {radius_m}
            UNION ALL
            SELECT hotel_id, d, cat FROM green_hit WHERE d <= {radius_m}
        ),
        agg AS (
            SELECT hotel_id,
                   sum({geo.decay_sql('d', decay_scale_m)}) AS raw_weighted_count,
                   count(*) AS poi_count,
                   count(DISTINCT cat) AS distinct_categories,
                   min(d) AS nearest_m
            FROM combined GROUP BY hotel_id
        )
        SELECT h.id AS hotel_id,
               coalesce(a.raw_weighted_count, 0.0) AS wc,
               100.0 * (1 - exp(-coalesce(a.raw_weighted_count, 0.0) / {saturation})) AS absolute_score,
               percent_rank() OVER (ORDER BY coalesce(a.raw_weighted_count, 0.0)) * 100 AS city_percentile,
               {hybrid_w} * (100.0 * (1 - exp(-coalesce(a.raw_weighted_count, 0.0) / {saturation})))
                 + {1 - hybrid_w} * (percent_rank() OVER (ORDER BY coalesce(a.raw_weighted_count, 0.0)) * 100) AS score,
               coalesce(a.poi_count, 0) AS poi_count,
               coalesce(a.distinct_categories, 0) AS distinct_categories,
               a.nearest_m
        FROM hotels h LEFT JOIN agg a ON a.hotel_id = h.id
    """
    con.execute(f"CREATE OR REPLACE TEMP TABLE dim_family_convenience AS {sql}")


def _transit_dimension(con, city: City, weights: dict[str, Any]) -> None:
    cfg = taxonomy.dimension_config("transit_access")
    radius_m = cfg["radius_m"]
    decay_scale_m = weights["decay_scale_m"]["transit_access"]
    bonus = weights["transit"]["multi_mode_bonus"]
    max_bonus_modes = weights["transit"]["max_bonus_modes"]
    predicate = taxonomy.poi_sql_predicate("transit_access", primary_col="p.taxonomy_primary", hierarchy_col="p.taxonomy_hierarchy")
    dlat, dlon = geo.degree_margin(radius_m, city)
    proj_h = geo.project_sql("ST_Point(h.lon, h.lat)", city)
    proj_p = geo.project_sql("ST_Point(p.lon, p.lat)", city)

    con.execute(
        f"""
        CREATE OR REPLACE TEMP TABLE dim_transit_access AS
        WITH within AS (
            SELECT h.id AS hotel_id, p.taxonomy_primary AS mode,
                   ST_Distance({proj_h}, {proj_p}) AS d
            FROM hotels h
            JOIN pois p
              ON p.lon BETWEEN h.lon - {dlon} AND h.lon + {dlon}
             AND p.lat BETWEEN h.lat - {dlat} AND h.lat + {dlat}
             AND {predicate}
        ),
        within_r AS (SELECT * FROM within WHERE d <= {radius_m}),
        per_mode AS (
            SELECT hotel_id, mode, min(d) AS nearest_m
            FROM within_r GROUP BY hotel_id, mode
        ),
        per_hotel AS (
            SELECT hotel_id,
                   max(100.0 * exp(-nearest_m / {decay_scale_m})) AS best_mode_score,
                   count(*) AS n_modes,
                   min(nearest_m) AS nearest_m
            FROM per_mode GROUP BY hotel_id
        )
        SELECT h.id AS hotel_id,
               -- DuckDB's least()/greatest() skip NULL arguments instead of
               -- propagating them (confirmed: least(100.0, NULL) = 100.0),
               -- so a hotel with zero transit POIs in radius (best_mode_score
               -- NULL from the LEFT JOIN) previously scored 100 instead of 0.
               -- Coalescing best_mode_score to 0.0 BEFORE the least() call
               -- fixes it: score_version 1.0.1 (docs/scoring.md §5 minor bump
               -- — rankings may shift for affected hotels).
               least(100.0, coalesce(p.best_mode_score, 0.0) + {bonus} * least(greatest(p.n_modes - 1, 0), {max_bonus_modes})) AS score,
               coalesce(p.n_modes, 0) AS poi_count,
               coalesce(p.n_modes, 0) AS distinct_categories,
               p.nearest_m
        FROM hotels h LEFT JOIN per_hotel p ON p.hotel_id = h.id
        """
    )


def _quietness_dimension(con, city: City, weights: dict[str, Any]) -> None:
    qcfg = taxonomy.quietness_config()
    qw = weights["quietness"]
    proj_h = geo.project_sql("ST_Point(h.lon, h.lat)", city)

    def nearest_segment_cte(name: str, where_clause: str, radius_m: float) -> str:
        dlat, dlon = geo.degree_margin(radius_m, city)
        proj_geom = geo.project_sql("ST_GeomFromText(s.geometry_wkt)", city)
        return f"""
        {name} AS (
            SELECT h.id AS hotel_id, min(ST_Distance({proj_h}, {proj_geom})) AS nearest_m
            FROM hotels h
            JOIN (
                SELECT geometry_wkt,
                       ST_XMin(ST_GeomFromText(geometry_wkt)) AS xmin,
                       ST_XMax(ST_GeomFromText(geometry_wkt)) AS xmax,
                       ST_YMin(ST_GeomFromText(geometry_wkt)) AS ymin,
                       ST_YMax(ST_GeomFromText(geometry_wkt)) AS ymax
                FROM segments WHERE {where_clause}
            ) s
              ON h.lon BETWEEN s.xmin - {dlon} AND s.xmax + {dlon}
             AND h.lat BETWEEN s.ymin - {dlat} AND s.ymax + {dlat}
            GROUP BY h.id
            HAVING min(ST_Distance({proj_h}, {proj_geom})) <= {radius_m}
        )
        """

    def nearest_poi_cte(name: str, categories: list[str], radius_m: float) -> str:
        dlat, dlon = geo.degree_margin(radius_m, city)
        proj_p = geo.project_sql("ST_Point(p.lon, p.lat)", city)
        cats = ", ".join(f"'{c}'" for c in categories)
        return f"""
        {name} AS (
            SELECT h.id AS hotel_id, min(ST_Distance({proj_h}, {proj_p})) AS nearest_m
            FROM hotels h
            JOIN pois p
              ON p.lon BETWEEN h.lon - {dlon} AND h.lon + {dlon}
             AND p.lat BETWEEN h.lat - {dlat} AND h.lat + {dlat}
             AND p.taxonomy_primary IN ({cats})
            GROUP BY h.id
            HAVING min(ST_Distance({proj_h}, {proj_p})) <= {radius_m}
        )
        """

    road_classes = ", ".join(f"'{c}'" for c in qcfg["road_classes"])
    sql = f"""
        WITH
        {nearest_segment_cte('major_road', f"subtype = 'road' AND class IN ({road_classes})", qcfg['major_road_radius_m'])},
        {nearest_segment_cte('rail', "subtype = 'rail'", qcfg['rail_radius_m'])},
        {nearest_poi_cte('nightlife', qcfg['nightlife_categories'], qcfg['nightlife_radius_m'])},
        {nearest_poi_cte('airport', qcfg['airport_categories'], qcfg['airport_radius_m'])}
        SELECT
            h.id AS hotel_id,
            greatest(0.0, least(100.0, {qw['start']}
                - {qw['penalties']['major_road']['weight']} * coalesce(exp(-mr.nearest_m / {qw['penalties']['major_road']['scale_m']}), 0)
                - {qw['penalties']['rail']['weight']} * coalesce(exp(-r.nearest_m / {qw['penalties']['rail']['scale_m']}), 0)
                - {qw['penalties']['nightlife']['weight']} * coalesce(exp(-n.nearest_m / {qw['penalties']['nightlife']['scale_m']}), 0)
                - {qw['penalties']['airport']['weight']} * coalesce(exp(-ap.nearest_m / {qw['penalties']['airport']['scale_m']}), 0)
            )) AS score,
            mr.nearest_m AS major_road_nearest_m,
            r.nearest_m AS rail_nearest_m,
            n.nearest_m AS nightlife_nearest_m,
            ap.nearest_m AS airport_nearest_m
        FROM hotels h
        LEFT JOIN major_road mr ON mr.hotel_id = h.id
        LEFT JOIN rail r ON r.hotel_id = h.id
        LEFT JOIN nightlife n ON n.hotel_id = h.id
        LEFT JOIN airport ap ON ap.hotel_id = h.id
    """
    con.execute(f"CREATE OR REPLACE TEMP TABLE dim_quietness_proxy AS {sql}")


def _confidence_and_balanced(con, city: City, weights: dict[str, Any], release: str) -> None:
    cw = weights["confidence"]["weights"]
    target_n = weights["confidence"]["city_sample_target_n"]
    default_pc = weights["confidence"]["default_place_confidence"]
    persona_balanced = weights["personas"]["balanced"]
    score_version = weights["score_version"]

    balanced_expr = " + ".join(f"{w} * d.{dim}_score" for dim, w in persona_balanced.items())
    coverage_dims = [d for d in DIMENSIONS if d != "quietness_proxy"]
    coverage_expr = " + ".join(f"(CASE WHEN d.{dim}_poi_count > 0 THEN 1 ELSE 0 END)" for dim in coverage_dims)

    select_dims = ",\n            ".join(f"dim_{dim}.score AS {dim}_score" for dim in DIMENSIONS)
    select_poi_counts = ",\n            ".join(f"dim_{dim}.poi_count AS {dim}_poi_count" for dim in coverage_dims)
    joins = "\n        ".join(f"JOIN dim_{dim} ON dim_{dim}.hotel_id = h.id" for dim in DIMENSIONS)

    con.execute(
        f"""
        CREATE OR REPLACE TEMP TABLE _joined AS
        SELECT h.id AS hotel_id, h.confidence AS place_confidence, h.dedupe_confidence,
            {select_dims},
            {select_poi_counts}
        FROM hotels h
        {joins}
        """
    )

    n_hotels = con.execute("SELECT count(*) FROM hotels").fetchone()[0]
    city_sample_component = min(100.0, 100.0 * n_hotels / target_n)

    con.execute(
        f"""
        CREATE OR REPLACE TEMP TABLE hotel_scores AS
        SELECT
            hotel_id,
            '{city.id}' AS city_id,
            '{score_version}' AS score_version,
            '{release}' AS source_release,
            now() AS computed_at,
            d.walkability_density_score AS walkability_density,
            d.transit_access_score AS transit_access,
            d.food_essentials_score AS food_essentials,
            d.quietness_proxy_score AS quietness_proxy,
            d.family_convenience_score AS family_convenience,
            d.nightlife_access_score AS nightlife_access,
            ({balanced_expr}) AS balanced_score,
            least(100.0, greatest(0.0,
                {cw['place_confidence']} * (100.0 * coalesce(place_confidence, {default_pc / 100})) +
                {cw['poi_coverage']} * (100.0 * ({coverage_expr}) / {len(coverage_dims)}) +
                {cw['city_sample_size']} * {city_sample_component} +
                {cw['dedupe_quality']} * dedupe_confidence
            )) AS confidence
        FROM _joined d
        """
    )


def score_city(city_id: str, release: overture.Release) -> dict[str, Any]:
    from .config import ETL_DIR

    city = get_city(city_id)
    etl_dir = ETL_DIR / release.id / city.id
    weights = load_score_weights()

    con = overture.connect()
    t0 = time.time()
    _open_city_tables(con, etl_dir)

    for dim in DENSITY_DIMENSIONS:
        _density_dimension(con, city, dim, weights, diversity_bonus=(dim == "food_essentials"))
    _family_convenience_dimension(con, city, weights)
    _transit_dimension(con, city, weights)
    _quietness_dimension(con, city, weights)
    _confidence_and_balanced(con, city, weights, release.id)

    con.execute(f"COPY hotel_scores TO '{etl_dir / 'hotel_scores.parquet'}' (FORMAT PARQUET)")
    _write_nearby_facts(con, city, release.id, etl_dir)
    elapsed = time.time() - t0

    stats = con.execute(
        "SELECT count(*), median(confidence), avg(balanced_score) FROM hotel_scores"
    ).fetchone()
    result = {
        "city_id": city.id,
        "release": release.id,
        "score_version": weights["score_version"],
        "score_seconds": round(elapsed, 1),
        "hotels_scored": stats[0],
        "median_confidence": round(stats[1], 1) if stats[1] is not None else None,
        "mean_balanced_score": round(stats[2], 1) if stats[2] is not None else None,
    }
    with open(etl_dir / "score_manifest.json", "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
    return result


def _write_nearby_facts(con, city: City, release_id: str, etl_dir: Path, top_n: int = 12) -> None:
    """Top-N nearby POIs per hotel across all scored dimensions, for the
    'Why?' section (docs/data-and-costs.md §2 — nearby_facts is the ONLY
    per-hotel POI detail that ever reaches the serving DB)."""
    radius_m = max(
        taxonomy.dimension_config(d)["radius_m"]
        for d in DENSITY_DIMENSIONS + ("transit_access", "family_convenience")
    )
    dlat, dlon = geo.degree_margin(radius_m, city)
    proj_h = geo.project_sql("ST_Point(h.lon, h.lat)", city)
    proj_p = geo.project_sql("ST_Point(p.lon, p.lat)", city)
    # Entity QA item (d): a display-only denylist -- these categories still
    # count toward the walkability_density SCORE (unchanged predicate), they
    # just don't clutter the "Why?" section's nearby-facts list.
    display_exclude = taxonomy.nearby_facts_display_exclude()
    exclude_sql = "AND p.taxonomy_primary NOT IN ({})".format(
        ", ".join(f"'{c}'" for c in display_exclude)
    ) if display_exclude else ""
    con.execute(
        f"""
        CREATE OR REPLACE TEMP TABLE nearby_facts AS
        WITH candidates AS (
            SELECT h.id AS hotel_id, p.name, p.taxonomy_primary AS category,
                   ST_Distance({proj_h}, {proj_p}) AS distance_m
            FROM hotels h
            JOIN pois p
              ON p.lon BETWEEN h.lon - {dlon} AND h.lon + {dlon}
             AND p.lat BETWEEN h.lat - {dlat} AND h.lat + {dlat}
            WHERE p.name IS NOT NULL
            {exclude_sql}
        ),
        ranked AS (
            SELECT *, row_number() OVER (PARTITION BY hotel_id ORDER BY distance_m) AS rnk
            FROM candidates WHERE distance_m <= {radius_m}
        )
        SELECT hotel_id, rnk AS rank, category, name, distance_m,
               '{release_id}' AS source_release
        FROM ranked WHERE rnk <= {top_n}
        """
    )
    con.execute(f"COPY nearby_facts TO '{etl_dir / 'nearby_facts.parquet'}' (FORMAT PARQUET)")
