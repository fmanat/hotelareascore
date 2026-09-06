"""Phase 1 data QA (CLAUDE.md §9 "data tests"): valid coords, no impossible
counts, no duplicate canonical ids, baselines present, versions recorded —
plus the anomaly/suspicious-hotel scan that feeds the Data Proof Report.

Fail closed (CLAUDE.md hard rule 10): `validate_city` raises ValidationError
on any hard-QA failure. Anomalies short of that are reported, not raised —
Phase 1's job is to surface them for owner review, not to silently drop data.
"""
from __future__ import annotations

import json
from typing import Any

from . import overture, taxonomy
from .config import DIMENSIONS, ETL_DIR, get_city


class ValidationError(RuntimeError):
    pass


def _scalar(con, sql: str):
    return con.execute(sql).fetchone()[0]


def validate_city(city_id: str, release: overture.Release) -> dict[str, Any]:
    city = get_city(city_id)
    etl_dir = ETL_DIR / release.id / city.id
    con = overture.connect()
    con.execute(f"CREATE OR REPLACE TEMP TABLE hotels AS SELECT * FROM read_parquet('{etl_dir / 'hotels.parquet'}')")
    con.execute(f"CREATE OR REPLACE TEMP TABLE scores AS SELECT * FROM read_parquet('{etl_dir / 'hotel_scores.parquet'}')")

    manifest = json.loads((etl_dir / "manifest.json").read_text())

    hard_failures: list[str] = []

    # 1. valid coords
    n_bad_coords = _scalar(
        con, "SELECT count(*) FROM hotels WHERE lat IS NULL OR lon IS NULL OR lat < -90 OR lat > 90 OR lon < -180 OR lon > 180"
    )
    if n_bad_coords:
        hard_failures.append(f"{n_bad_coords} hotel(s) with invalid coordinates")

    # 2. no duplicate canonical hotel ids in scores
    n_hotels = _scalar(con, "SELECT count(*) FROM scores")
    n_distinct_ids = _scalar(con, "SELECT count(DISTINCT hotel_id) FROM scores")
    if n_hotels != n_distinct_ids:
        hard_failures.append(f"hotel_scores has {n_hotels - n_distinct_ids} duplicate hotel_id row(s)")

    # 3. no impossible counts: scores/confidence must be within [0, 100]
    n_out_of_range = _scalar(
        con,
        "SELECT count(*) FROM scores WHERE "
        + " OR ".join(f"{d} < 0 OR {d} > 100" for d in DIMENSIONS)
        + " OR confidence < 0 OR confidence > 100 OR balanced_score < 0 OR balanced_score > 100",
    )
    if n_out_of_range:
        hard_failures.append(f"{n_out_of_range} hotel(s) with a dimension/confidence score outside [0, 100]")

    # 4. versions recorded on every row
    n_missing_version = _scalar(con, "SELECT count(*) FROM scores WHERE score_version IS NULL OR source_release IS NULL")
    if n_missing_version:
        hard_failures.append(f"{n_missing_version} score row(s) missing score_version/source_release")

    if hard_failures:
        raise ValidationError(f"{city.id}: " + "; ".join(hard_failures))

    # 5. baselines (city-level aggregate, stand-in for city_score_baselines
    #    until this feeds Supabase in Phase 2 — docs/data-and-costs.md §3)
    baseline_sql = (
        f"SELECT {', '.join(f'avg({d}) AS {d}_mean, median({d}) AS {d}_median' for d in DIMENSIONS)}, "
        "avg(balanced_score) AS balanced_mean, median(confidence) AS confidence_median FROM scores"
    )
    baseline_cursor = con.execute(baseline_sql)
    baseline_cols = [d[0] for d in baseline_cursor.description]
    baseline_row = baseline_cursor.fetchone()
    baseline = {
        "city_id": city.id,
        "score_version": manifest.get("release"),
        "source_release": release.id,
        "n_hotels": n_hotels,
        **dict(zip(baseline_cols, [round(v, 2) if v is not None else None for v in baseline_row])),
    }
    with open(etl_dir / "city_baseline.json", "w", encoding="utf-8") as f:
        json.dump(baseline, f, indent=2)

    # 6. anomaly scan (soft — reported, not fatal)
    n_low_confidence = _scalar(con, "SELECT count(*) FROM scores WHERE confidence < 60")
    n_all_zero = _scalar(con, "SELECT count(*) FROM scores WHERE " + " AND ".join(f"{d} = 0" for d in DIMENSIONS))
    n_unresolved_coincident = _scalar(
        con,
        """
        SELECT count(*) FROM (
            SELECT lat, lon, count(*) c FROM hotels GROUP BY lat, lon HAVING count(*) > 1
        )
        """,
    )
    n_missing_name = _scalar(con, "SELECT count(*) FROM hotels WHERE name IS NULL OR trim(name) = ''")
    coincident_clusters = con.execute(
        """
        SELECT lat, lon, list(name ORDER BY name) AS names, count(*) AS n
        FROM hotels GROUP BY lat, lon HAVING count(*) > 1
        ORDER BY n DESC LIMIT 5
        """
    ).fetchall()

    # "rejects" for the Data Proof Report: lodging-hierarchy places that exist
    # in-bbox but fall outside the v1 hotel_types scope (taxonomy-mapping.yml)
    places_path = overture.places_path(release)
    minx, miny, maxx, maxy = city.bbox
    excluded = ", ".join(f"'{t}'" for t in sorted(taxonomy.hotel_excluded_types()))
    rejected_by_type = con.execute(
        f"""
        SELECT taxonomy.primary, count(*) FROM read_parquet('{places_path}')
        WHERE bbox.xmin BETWEEN {minx} AND {maxx} AND bbox.ymin BETWEEN {miny} AND {maxy}
          AND taxonomy.primary IN ({excluded})
        GROUP BY 1 ORDER BY 2 DESC
        """
    ).fetchall()
    n_rejected_lodging = sum(r[1] for r in rejected_by_type)

    suspicious = con.execute(
        """
        SELECT h.id, h.name, h.address_locality, s.confidence, s.balanced_score,
               h.dedupe_confidence
        FROM hotels h JOIN scores s ON s.hotel_id = h.id
        ORDER BY
            (CASE WHEN h.name IS NULL OR trim(h.name) = '' THEN 0 ELSE 1 END),
            s.confidence ASC,
            s.balanced_score ASC
        LIMIT 10
        """
    ).fetchall()

    result = {
        "city_id": city.id,
        "n_hotels": n_hotels,
        "hotels_raw": manifest["hotels_raw"],
        "dedupe_groups_merged": manifest["dedupe_groups_merged"],
        "dedupe_records_absorbed": manifest["dedupe_records_absorbed"],
        "dupe_rate_pct": round(100.0 * manifest["dedupe_records_absorbed"] / manifest["hotels_raw"], 2) if manifest["hotels_raw"] else 0.0,
        "rejected_lodging_out_of_scope": n_rejected_lodging,
        "rejected_lodging_by_type": {r[0]: r[1] for r in rejected_by_type},
        "pois": manifest["pois"],
        "segments": manifest["segments"],
        "median_confidence": baseline["confidence_median"],
        "n_low_confidence": n_low_confidence,
        "n_all_zero_dimensions": n_all_zero,
        "n_unresolved_coincident_coords": n_unresolved_coincident,
        "n_missing_name": n_missing_name,
        "coincident_coord_clusters_sample": [
            {"lat": r[0], "lon": r[1], "names": r[2], "n": r[3]} for r in coincident_clusters
        ],
        "top_suspicious": [
            {
                "id": r[0], "name": r[1], "locality": r[2],
                "confidence": round(r[3], 1) if r[3] is not None else None,
                "balanced_score": round(r[4], 1) if r[4] is not None else None,
                "dedupe_confidence": r[5],
            }
            for r in suspicious
        ],
        "baseline": baseline,
    }
    with open(etl_dir / "validation_report.json", "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, default=str)
    return result
