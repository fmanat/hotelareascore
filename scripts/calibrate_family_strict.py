#!/usr/bin/env python3
"""Family-specific recalibration against tests/golden/family_strict.csv
(owner-provided, re-labeled to a strict "reachable on foot" definition --
see tests/golden/LABELS-PROVENANCE.md amendment). Owner's pre-authorized
decision rule (overnight mission Bloc A step 4): Spearman >= 0.5 -> Phase 3
family_convenience gate passes; < 0.5 -> stop, no tuning, report.
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from hotelareascore.stats import spearman  # noqa: E402

RELEASE = "2026-08-19.0"
CITY_ID_BY_NAME = {
    "London": "london", "Bangkok": "bangkok", "Paris": "paris", "Rome": "rome",
    "Barcelona": "barcelona", "Amsterdam": "amsterdam", "Lisbon": "lisbon",
    "Sydney": "sydney", "Tokyo": "tokyo", "Dubai": "dubai", "New York": "new_york",
    "Singapore": "singapore",
}

DECISION_THRESHOLD = 0.5


def load_family_strict() -> dict[str, float]:
    with open(ROOT / "tests/golden/family_strict.csv", newline="", encoding="utf-8") as f:
        return {row["hotel_id"]: float(row["family_strict"]) for row in csv.DictReader(f)}


def load_hotel_city() -> dict[str, str]:
    """hotel_id -> city display name, from the original hotels.csv (same 50 ids)."""
    with open(ROOT / "tests/golden/hotels.csv", newline="", encoding="utf-8") as f:
        return {row["hotel_id"]: row["city"] for row in csv.DictReader(f)}


def load_computed_family(city_id: str) -> dict[str, float]:
    con = duckdb.connect()
    path = ROOT / "data/etl" / RELEASE / city_id / "hotel_scores.parquet"
    rows = con.execute(f"SELECT hotel_id, family_convenience FROM read_parquet('{path.as_posix()}')").fetchall()
    return {r[0]: r[1] for r in rows}


def main() -> None:
    labels = load_family_strict()
    hotel_city = load_hotel_city()
    computed_by_city: dict[str, dict[str, float]] = {}

    joined = []
    missing = []
    for hotel_id, label in labels.items():
        city_name = hotel_city.get(hotel_id)
        if city_name is None:
            missing.append(hotel_id)
            continue
        city_id = CITY_ID_BY_NAME[city_name]
        if city_id not in computed_by_city:
            computed_by_city[city_id] = load_computed_family(city_id)
        computed = computed_by_city[city_id].get(hotel_id)
        if computed is None:
            missing.append(hotel_id)
            continue
        joined.append({"hotel_id": hotel_id, "city": city_name, "family_strict": label, "family_convenience": computed})

    if missing:
        print(f"WARNING: {len(missing)} hotel_ids in family_strict.csv not found: {missing}", file=sys.stderr)

    xs = [r["family_strict"] for r in joined]
    ys = [r["family_convenience"] for r in joined]
    rho = spearman(xs, ys)

    print(f"Joined {len(joined)}/{len(labels)} hotels.")
    print(f"Spearman(family_strict, family_convenience) = {rho:.4f}")
    passed = rho >= DECISION_THRESHOLD
    print(f"Decision threshold: {DECISION_THRESHOLD} -> {'PASS' if passed else 'FAIL'}")

    # Per-city breakdown and outliers for the report either way.
    from collections import defaultdict

    by_city_pairs: dict[str, list[tuple[float, float]]] = defaultdict(list)
    for r in joined:
        by_city_pairs[r["city"]].append((r["family_strict"], r["family_convenience"]))
    per_city_rho = {}
    for city, pairs in by_city_pairs.items():
        cxs = [p[0] for p in pairs]
        cys = [p[1] for p in pairs]
        per_city_rho[city] = round(spearman(cxs, cys), 3) if len(pairs) >= 3 else None

    joined_sorted = sorted(joined, key=lambda r: abs((r["family_strict"] - 1) / 4 * 100 - r["family_convenience"]), reverse=True)
    print("\nTop 10 largest label-vs-computed gaps:")
    for r in joined_sorted[:10]:
        label_0_100 = (r["family_strict"] - 1) / 4 * 100
        print(f"  {r['hotel_id']} ({r['city']}): label={r['family_strict']} (~{label_0_100:.0f}/100), computed={r['family_convenience']:.1f}")

    report = {
        "n_joined": len(joined),
        "n_missing": len(missing),
        "missing_ids": missing,
        "spearman": rho,
        "decision_threshold": DECISION_THRESHOLD,
        "passed": passed,
        "per_city_spearman": per_city_rho,
    }
    out_path = ROOT / "docs/reports/phase-3-family-strict-calibration.json"
    out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"\nWrote {out_path}")

    joined_path = ROOT / "tests/golden/joined-scores-1.2.0-family-strict.csv"
    with open(joined_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["hotel_id", "city", "family_strict", "family_convenience"])
        w.writeheader()
        w.writerows(joined)
    print(f"Wrote {joined_path}")


if __name__ == "__main__":
    main()
