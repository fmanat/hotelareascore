#!/usr/bin/env python3
"""Golden-set calibration (docs/scoring.md §4.2).

Joins tests/golden/hotels.csv (Claude-produced labels, see
tests/golden/LABELS-PROVENANCE.md) against the current hotel_scores
parquet files, and reports Spearman rank correlation per dimension pair
in three variants, per-city mean error, and outliers.

Read-only: computes and prints/writes a report, never touches
data/config/score-weights.yml.
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

# CSV "city" display name -> city_id folder name
CITY_ID_BY_NAME = {
    "London": "london",
    "Bangkok": "bangkok",
    "Paris": "paris",
    "Rome": "rome",
    "Barcelona": "barcelona",
    "Amsterdam": "amsterdam",
    "Lisbon": "lisbon",
    "Sydney": "sydney",
    "Tokyo": "tokyo",
    "Dubai": "dubai",
    "New York": "new_york",
    "Singapore": "singapore",
}

# (label column in hotels.csv, computed dimension column in hotel_scores.parquet, expected sign)
DIMENSION_PAIRS = [
    ("transit_convenience", "transit_access", "+"),
    ("nearby_restaurants", "food_essentials", "+"),
    ("major_road_exposure", "quietness_proxy", "-"),
    ("nightlife_intensity", "nightlife_access", "+"),
    ("park_family_convenience", "family_convenience", "+"),
]

PRIOR_EXPOSURE_IDS = {
    "8bca5fde-f7e5-45a4-8bf5-21f4b45770f5",  # Hotel Amano
    "a94d53cb-00c1-4303-b729-4707e35da9b8",  # สุขุมวิทซอย11
}

LOW_CONFIDENCE_IDS = {
    "8490d0c3-f9b4-4f9e-bfd2-a3b1e108ef71",  # Ardra Guest House
    "fbae2641-7c15-458a-9259-45378d2e4ac7",  # Airport Hotels Bangkok Travel Service
    "a303b42c-f890-43c2-b031-5bd456bb36a1",  # Suksawad Hotel
    "66caa9ab-e6a6-482a-95d9-f5c6f8746c37",  # ホテルCOCO
    "4a4ae738-6711-432a-ab0e-e3d4d0d9ccb2",  # Guesthouse SAKAE
    "4b3d8f70-5f4b-470f-b81c-59405312eb54",  # Dusit Thani Dubai
    "0e2256c4-c5f3-4777-a0b4-96d059639a2d",  # ibis budget Amsterdam City South
}

ENTITY_QA_BACKLOG_IDS = {
    "2bf89f8c-dfec-4e9d-a8a4-6ae4ffc59231",  # 桝本屋酒店 (likely a liquor shop, CJK false positive)
    "346a49c0-bf06-4543-bc84-76544715ba84",  # アクアプレイス旭湯 (possible bathhouse/sento)
    "a9b48284-e2df-4e9d-be7f-76fae7f25aa6",  # Souq Madinat Jumeirah (souk/venue, not a hotel)
    "b2a1e3f4-5b32-4901-9dc0-fd94fcd5db40",  # Holiday Inn Paris CDG S.A.R.L. (corporate entity, pin mismatch)
    "756a9130-4883-41ac-b438-3e5a570e1da7",  # SpringHill Suites (pin in Carlstadt NJ, inside NY bbox)
}


def load_labels() -> list[dict]:
    with open(ROOT / "tests/golden/hotels.csv", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def load_computed_scores() -> dict[str, dict]:
    con = duckdb.connect()
    by_id: dict[str, dict] = {}
    for city_id in set(CITY_ID_BY_NAME.values()):
        path = ROOT / "data/etl" / RELEASE / city_id / "hotel_scores.parquet"
        if not path.exists():
            print(f"WARNING: missing {path}", file=sys.stderr)
            continue
        rows = con.execute(
            "SELECT hotel_id, transit_access, food_essentials, quietness_proxy, "
            "nightlife_access, family_convenience, balanced_score, confidence "
            f"FROM read_parquet('{path.as_posix()}')"
        ).fetchall()
        cols = [
            "hotel_id",
            "transit_access",
            "food_essentials",
            "quietness_proxy",
            "nightlife_access",
            "family_convenience",
            "balanced_score",
            "confidence",
        ]
        for row in rows:
            rec = dict(zip(cols, row))
            by_id[rec["hotel_id"]] = rec
    return by_id


def build_joined(labels: list[dict], computed: dict[str, dict]) -> list[dict]:
    joined = []
    missing = []
    for lbl in labels:
        hid = lbl["hotel_id"]
        comp = computed.get(hid)
        if comp is None:
            missing.append((hid, lbl["name"], lbl["city"]))
            continue
        rec = {"hotel_id": hid, "name": lbl["name"], "city": lbl["city"]}
        for label_col, _, _ in DIMENSION_PAIRS:
            rec[label_col] = float(lbl[label_col])
        rec.update(comp)
        joined.append(rec)
    if missing:
        print(f"WARNING: {len(missing)} golden-set hotels not found in computed scores:", file=sys.stderr)
        for hid, name, city in missing:
            print(f"  {hid} {name} ({city})", file=sys.stderr)
    return joined


def variant_rows(joined: list[dict], exclude_ids: set[str]) -> list[dict]:
    return [r for r in joined if r["hotel_id"] not in exclude_ids]


def compute_spearman_table(rows: list[dict]) -> dict[str, float]:
    out = {}
    for label_col, computed_col, sign in DIMENSION_PAIRS:
        xs = [r[label_col] for r in rows]
        ys = [r[computed_col] for r in rows]
        out[f"{label_col} vs {computed_col} ({sign})"] = spearman(xs, ys)
    return out


def compute_per_city_mean_error(rows: list[dict]) -> dict[str, dict]:
    """Mean absolute difference between label (rescaled 1-5 -> 0-100) and
    computed score, per city, per dimension pair -- a rough 'is this city
    systematically off' signal, not a formal error metric (the label scale
    and the computed scale are not the same instrument)."""
    from collections import defaultdict

    per_city: dict[str, dict] = defaultdict(lambda: defaultdict(list))
    for r in rows:
        for label_col, computed_col, sign in DIMENSION_PAIRS:
            label_0_100 = (r[label_col] - 1) / 4 * 100
            computed = r[computed_col]
            if sign == "-":
                computed = 100 - computed
            per_city[r["city"]][label_col].append(abs(label_0_100 - computed))
    result = {}
    for city, dims in per_city.items():
        result[city] = {
            dim: round(sum(vals) / len(vals), 1) for dim, vals in dims.items()
        }
    return result


def main() -> None:
    labels = load_labels()
    computed = load_computed_scores()
    joined = build_joined(labels, computed)
    print(f"Joined {len(joined)}/{len(labels)} golden-set hotels against computed scores.\n")

    variants = {
        "(a) all 50": variant_rows(joined, set()),
        "(b) excl. 2 prior-exposure": variant_rows(joined, PRIOR_EXPOSURE_IDS),
        "(c) excl. 7 low-confidence": variant_rows(joined, LOW_CONFIDENCE_IDS),
    }

    report = {"n_joined": len(joined), "variants": {}}

    for label, rows in variants.items():
        print(f"=== {label} (n={len(rows)}) ===")
        table = compute_spearman_table(rows)
        for k, v in table.items():
            flag = " *** BELOW 0.6 BAR ***" if (v == v and v < 0.6) else ""
            print(f"  {k}: {v:.3f}{flag}" if v == v else f"  {k}: nan{flag}")
        report["variants"][label] = table
        print()

    per_city = compute_per_city_mean_error(variants["(a) all 50"])
    print("=== Per-city mean |label(0-100) - computed| by dimension (variant a) ===")
    for city, dims in sorted(per_city.items()):
        print(f"  {city}: {dims}")
    report["per_city_mean_error"] = per_city

    out_path = ROOT / "docs/reports/phase-3-calibration-4.2.json"
    out_path.write_text(json.dumps(report, indent=2, default=lambda x: None), encoding="utf-8")
    print(f"\nWrote {out_path}")

    joined_path = ROOT / "docs/reports/phase-3-calibration-joined.csv"
    if joined:
        keys = list(joined[0].keys())
        with open(joined_path, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=keys)
            w.writeheader()
            w.writerows(joined)
        print(f"Wrote {joined_path}")


if __name__ == "__main__":
    main()
