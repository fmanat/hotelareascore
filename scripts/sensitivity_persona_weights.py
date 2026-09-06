#!/usr/bin/env python3
"""Persona-weight sensitivity (docs/scoring.md §4.3 / docs/adr/004 point 4):
perturb the "balanced" persona's weights +/-10 points (one dimension shifted
up, compensated pro-rata across the rest so weights still sum to 1.0) and
measure Kendall-tau of the resulting balanced_score ranking per city vs the
current weights.

Cheap by construction: balanced_score is a fixed linear combination of the
6 already-computed dimension scores (persona reweighting never touches the
underlying facts/scores, docs/scoring.md §1), so this reads the existing
hotel_scores.parquet directly -- no spatial joins, no DuckDB dimension
recompute, nothing written back.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import duckdb
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from hotelareascore.stats import kendall_tau  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
RELEASE = "2026-08-19.0"
CITIES = [
    "london", "bangkok", "paris", "rome", "barcelona", "amsterdam",
    "lisbon", "sydney", "tokyo", "dubai", "new_york", "singapore",
]
DIMENSIONS = [
    "walkability_density", "transit_access", "food_essentials",
    "quietness_proxy", "family_convenience", "nightlife_access",
]


def load_city_scores(city_id: str) -> dict[str, dict]:
    con = duckdb.connect()
    path = ROOT / "data/etl" / RELEASE / city_id / "hotel_scores.parquet"
    rows = con.execute(
        f"SELECT hotel_id, {', '.join(DIMENSIONS)} FROM read_parquet('{path.as_posix()}')"
    ).fetchall()
    return {r[0]: dict(zip(DIMENSIONS, r[1:])) for r in rows}


def balanced_score(dims: dict[str, float], weights: dict[str, float]) -> float:
    return sum(weights[d] * dims[d] for d in DIMENSIONS)


def perturbed_weights(base: dict[str, float], boost_dim: str, delta: float) -> dict[str, float]:
    """Shift `delta` (e.g. +0.10) onto boost_dim, remove it pro-rata from the
    other 5 dimensions (proportional to their current weight) so the set
    still sums to 1.0."""
    others = [d for d in DIMENSIONS if d != boost_dim]
    others_total = sum(base[d] for d in others)
    out = dict(base)
    out[boost_dim] = base[boost_dim] + delta
    for d in others:
        share = base[d] / others_total if others_total > 0 else 1 / len(others)
        out[d] = base[d] - delta * share
    return out


def main() -> None:
    weights_cfg = yaml.safe_load(open(ROOT / "data/config/score-weights.yml"))
    base = weights_cfg["personas"]["balanced"]

    city_scores = {c: load_city_scores(c) for c in CITIES}
    baseline_balanced = {
        c: {hid: balanced_score(d, base) for hid, d in scores.items()}
        for c, scores in city_scores.items()
    }

    report = {"perturbations": []}
    for dim in DIMENSIONS:
        for delta, label in [(0.10, "+10pt"), (-0.10, "-10pt")]:
            if base[dim] + delta < 0:
                continue  # can't remove more weight than the dimension has
            w = perturbed_weights(base, dim, delta)
            per_city_tau = {}
            for c in CITIES:
                perturbed_balanced = {hid: balanced_score(d, w) for hid, d in city_scores[c].items()}
                xs = list(baseline_balanced[c].values())
                ys = [perturbed_balanced[hid] for hid in baseline_balanced[c]]
                per_city_tau[c] = round(kendall_tau(xs, ys), 3)
            taus = list(per_city_tau.values())
            mean_tau = round(sum(taus) / len(taus), 3)
            load_bearing = [c for c, t in per_city_tau.items() if t < 0.8]
            print(f"balanced.{dim} {label} (-> {w[dim]:.2f}, others rebalanced): mean tau={mean_tau}"
                  + (f"  LOAD-BEARING in: {load_bearing}" if load_bearing else "  stable"))
            report["perturbations"].append({
                "label": f"balanced.{dim} {label}", "per_city_tau": per_city_tau,
                "mean_tau": mean_tau, "load_bearing_cities": load_bearing,
            })

    out_path = ROOT / "docs/reports/phase-3-sensitivity-persona-weights.json"
    out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"\nWrote {out_path}")


if __name__ == "__main__":
    main()
