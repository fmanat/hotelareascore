#!/usr/bin/env python3
"""Sensitivity analysis (docs/scoring.md §4.3 / docs/adr/004 point 4).

Perturbs each major scoring constant, recomputes rankings via the real
scoring SQL (src/hotelareascore/scoring.py's internal dimension functions),
and measures Kendall-tau of the per-city hotel ranking vs the baseline
(current, unperturbed) ranking.

Read-only: never calls COPY to hotel_scores.parquet, never edits
data/config/score-weights.yml. All perturbed computation stays in DuckDB
temp tables that are dropped when the connection closes.
"""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from hotelareascore import overture  # noqa: E402
from hotelareascore.config import ETL_DIR, get_city, load_score_weights  # noqa: E402
from hotelareascore.scoring import (  # noqa: E402
    DENSITY_DIMENSIONS,
    _density_dimension,
    _open_city_tables,
    _quietness_dimension,
    _transit_dimension,
)
from hotelareascore.stats import kendall_tau, spearman  # noqa: E402

RELEASE = "2026-08-19.0"
CITIES = [
    "london", "bangkok", "paris", "rome", "barcelona", "amsterdam",
    "lisbon", "sydney", "tokyo", "dubai", "new_york", "singapore",
]


def compute_dimension_scores(con, city, weights, dimension: str) -> dict[str, float]:
    """Run the real scoring SQL for one dimension with the given weights
    dict and return {hotel_id: score}, without ever touching disk."""
    if dimension == "transit_access":
        _transit_dimension(con, city, weights)
        table = "dim_transit_access"
    elif dimension == "quietness_proxy":
        _quietness_dimension(con, city, weights)
        table = "dim_quietness_proxy"
    else:
        _density_dimension(con, city, dimension, weights, diversity_bonus=(dimension == "food_essentials"))
        table = f"dim_{dimension}"
    rows = con.execute(f"SELECT hotel_id, score FROM {table}").fetchall()
    return {hid: score for hid, score in rows}


def tau_vs_baseline(baseline: dict[str, float], perturbed: dict[str, float]) -> float:
    common = [hid for hid in baseline if hid in perturbed]
    xs = [baseline[hid] for hid in common]
    ys = [perturbed[hid] for hid in common]
    return kendall_tau(xs, ys)


def run_perturbation(label: str, dimension: str, mutate_weights, baselines: dict[str, dict]) -> dict:
    """mutate_weights(weights) mutates a deep copy in place; returns per-city tau."""
    con = overture.connect()
    per_city_tau = {}
    for city_id in CITIES:
        city = get_city(city_id)
        etl_dir = ETL_DIR / RELEASE / city.id
        _open_city_tables(con, etl_dir)
        weights = copy.deepcopy(load_score_weights())
        mutate_weights(weights)
        perturbed = compute_dimension_scores(con, city, weights, dimension)
        per_city_tau[city_id] = round(tau_vs_baseline(baselines[city_id], perturbed), 3)
    con.close()
    taus = list(per_city_tau.values())
    mean_tau = round(sum(taus) / len(taus), 3)
    load_bearing_cities = [c for c, t in per_city_tau.items() if t < 0.8]
    print(f"{label}: mean tau={mean_tau}" + (f"  LOAD-BEARING in: {load_bearing_cities}" if load_bearing_cities else "  stable"))
    return {"label": label, "dimension": dimension, "per_city_tau": per_city_tau, "mean_tau": mean_tau,
             "load_bearing_cities": load_bearing_cities}


def compute_baselines(dimension: str) -> dict[str, dict]:
    con = overture.connect()
    baselines = {}
    for city_id in CITIES:
        city = get_city(city_id)
        etl_dir = ETL_DIR / RELEASE / city.id
        _open_city_tables(con, etl_dir)
        weights = load_score_weights()
        baselines[city_id] = compute_dimension_scores(con, city, weights, dimension)
    con.close()
    return baselines


def nightlife_density_variant(con, city, weights) -> dict[str, float]:
    """Priority candidate (docs/scoring.md §4.3): replace the quietness
    nightlife penalty's nearest-venue term with a density term -- weight *
    (1 - exp(-weighted_count / saturation)) instead of weight *
    exp(-nearest_m / scale) -- so a street of 25 bars penalizes more than a
    single bar at the same distance. Reuses the same categories/radius as
    the existing quietness nightlife penalty (not nightlife_access's own
    radius, which differs)."""
    from hotelareascore import geo, taxonomy

    qcfg = taxonomy.quietness_config()
    qw = weights["quietness"]
    radius_m = qcfg["nightlife_radius_m"]
    cats = qcfg["nightlife_categories"]
    decay_scale_m = qw["penalties"]["nightlife"]["scale_m"]
    saturation = 3.0  # same order of magnitude as nightlife_access's own absolute_saturation (4)
    dlat, dlon = geo.degree_margin(radius_m, city)
    proj_h = geo.project_sql("ST_Point(h.lon, h.lat)", city)
    proj_p = geo.project_sql("ST_Point(p.lon, p.lat)", city)
    cats_sql = ", ".join(f"'{c}'" for c in cats)

    # Recompute the other three penalties unperturbed (baseline weights) so
    # only the nightlife term changes -- keeps this an isolated A/B, not a
    # full re-derivation.
    _quietness_dimension(con, city, weights)

    sql = f"""
        WITH within AS (
            SELECT h.id AS hotel_id, ST_Distance({proj_h}, {proj_p}) AS d
            FROM hotels h JOIN pois p
              ON p.lon BETWEEN h.lon - {dlon} AND h.lon + {dlon}
             AND p.lat BETWEEN h.lat - {dlat} AND h.lat + {dlat}
             AND p.taxonomy_primary IN ({cats_sql})
        ),
        within_r AS (SELECT * FROM within WHERE d <= {radius_m}),
        wc AS (SELECT hotel_id, sum({geo.decay_sql('d', decay_scale_m)}) AS weighted_count FROM within_r GROUP BY hotel_id)
        SELECT h.id AS hotel_id,
               {qw['penalties']['nightlife']['weight']} * (1 - exp(-coalesce(w.weighted_count,0.0) / {saturation})) AS density_penalty,
               q.major_road_nearest_m, q.rail_nearest_m, q.airport_nearest_m
        FROM hotels h
        LEFT JOIN wc w ON w.hotel_id = h.id
        LEFT JOIN dim_quietness_proxy q ON q.hotel_id = h.id
    """
    rows = con.execute(sql).fetchall()
    out = {}
    for hotel_id, density_penalty, major_road_nearest_m, rail_nearest_m, airport_nearest_m in rows:
        major_p = qw["penalties"]["major_road"]["weight"] * (
            __import__("math").exp(-major_road_nearest_m / qw["penalties"]["major_road"]["scale_m"]) if major_road_nearest_m is not None else 0.0
        )
        rail_p = qw["penalties"]["rail"]["weight"] * (
            __import__("math").exp(-rail_nearest_m / qw["penalties"]["rail"]["scale_m"]) if rail_nearest_m is not None else 0.0
        )
        airport_p = qw["penalties"]["airport"]["weight"] * (
            __import__("math").exp(-airport_nearest_m / qw["penalties"]["airport"]["scale_m"]) if airport_nearest_m is not None else 0.0
        )
        score = max(0.0, min(100.0, qw["start"] - major_p - rail_p - airport_p - density_penalty))
        out[hotel_id] = score
    return out


def main() -> None:
    report: dict = {"perturbations": []}

    print("=== Baselines (current weights) ===")
    baseline_by_dim: dict[str, dict] = {}
    for dim in list(DENSITY_DIMENSIONS) + ["transit_access", "quietness_proxy"]:
        baseline_by_dim[dim] = compute_baselines(dim)
    print("done\n")

    print("=== Decay scale perturbations (+/-30%) ===")
    for dim in DENSITY_DIMENSIONS + ("transit_access",):
        for pct, name in [(1.3, "+30%"), (0.7, "-30%")]:
            def mutate(w, dim=dim, pct=pct):
                w["decay_scale_m"][dim] = w["decay_scale_m"][dim] * pct
            r = run_perturbation(f"decay_scale_m.{dim} {name}", dim, mutate, baseline_by_dim[dim])
            report["perturbations"].append(r)

    print("\n=== Hybrid absolute weight (0.70 -> 0.5, 0.9) ===")
    for val in [0.5, 0.9]:
        for dim in DENSITY_DIMENSIONS:
            def mutate(w, val=val):
                w["hybrid_absolute_weight"] = val
            r = run_perturbation(f"hybrid_absolute_weight={val} [{dim}]", dim, mutate, baseline_by_dim[dim])
            report["perturbations"].append(r)

    print("\n=== Quietness penalty weights (+/-30%, one at a time) ===")
    for penalty_name in ["major_road", "rail", "nightlife", "airport"]:
        for pct, name in [(1.3, "+30%"), (0.7, "-30%")]:
            def mutate(w, penalty_name=penalty_name, pct=pct):
                w["quietness"]["penalties"][penalty_name]["weight"] *= pct
            r = run_perturbation(f"quietness.{penalty_name}.weight {name}", "quietness_proxy", mutate, baseline_by_dim["quietness_proxy"])
            report["perturbations"].append(r)

    print("\n=== Priority candidate: nightlife nearest-venue -> density-based penalty ===")
    con = overture.connect()
    density_variant_by_city = {}
    for city_id in CITIES:
        city = get_city(city_id)
        etl_dir = ETL_DIR / RELEASE / city.id
        _open_city_tables(con, etl_dir)
        weights = load_score_weights()
        density_variant_by_city[city_id] = nightlife_density_variant(con, city, weights)
    con.close()
    per_city_tau = {}
    for city_id in CITIES:
        per_city_tau[city_id] = round(tau_vs_baseline(baseline_by_dim["quietness_proxy"][city_id], density_variant_by_city[city_id]), 3)
    taus = list(per_city_tau.values())
    mean_tau = round(sum(taus) / len(taus), 3)
    load_bearing = [c for c, t in per_city_tau.items() if t < 0.8]
    print(f"nightlife density-based variant vs baseline: mean tau={mean_tau}" + (f" LOAD-BEARING in: {load_bearing}" if load_bearing else " stable"))
    report["nightlife_density_variant"] = {"per_city_tau": per_city_tau, "mean_tau": mean_tau, "load_bearing_cities": load_bearing}

    # Cross-check the density variant against the golden labels for the two
    # cities most represented (London, Bangkok) using the joined CSV already
    # produced by calibrate_golden_set.py.
    import csv as _csv
    joined_path = Path(__file__).resolve().parents[1] / "docs/reports/phase-3-calibration-joined.csv"
    if joined_path.exists():
        with open(joined_path, newline="", encoding="utf-8") as f:
            joined_rows = list(_csv.DictReader(f))
        city_display_to_id = {
            "London": "london", "Bangkok": "bangkok", "Paris": "paris", "Rome": "rome",
            "Barcelona": "barcelona", "Amsterdam": "amsterdam", "Lisbon": "lisbon",
            "Sydney": "sydney", "Tokyo": "tokyo", "Dubai": "dubai", "New York": "new_york",
            "Singapore": "singapore",
        }
        xs_major, ys_baseline, ys_density = [], [], []
        for r in joined_rows:
            cid = city_display_to_id[r["city"]]
            hid = r["hotel_id"]
            if hid in density_variant_by_city[cid]:
                xs_major.append(float(r["major_road_exposure"]))
                ys_baseline.append(float(r["quietness_proxy"]))
                ys_density.append(density_variant_by_city[cid][hid])
        sp_baseline = spearman(xs_major, ys_baseline)
        sp_density = spearman(xs_major, ys_density)
        print(f"Spearman(major_road_exposure label, quietness_proxy): baseline={sp_baseline:.3f}  density-variant={sp_density:.3f}")
        report["nightlife_density_variant"]["spearman_major_road_vs_quietness"] = {
            "baseline": sp_baseline, "density_variant": sp_density,
        }

    out_path = Path(__file__).resolve().parents[1] / "docs/reports/phase-3-sensitivity-4.3.json"
    out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"\nWrote {out_path}")


if __name__ == "__main__":
    main()
