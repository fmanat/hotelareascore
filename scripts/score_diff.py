#!/usr/bin/env python3
"""Score-version diff report (docs/scoring.md §5 point 2), generalized from
the 1.0.0-proof -> 1.0.1 report so it can be reused for 1.0.1 -> 1.1.0 and
future bumps: per-city biggest movers, mean shift, per-dimension changed
counts. Read-only against two hotel_scores.parquet snapshots -- writes a
markdown report, changes nothing.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import duckdb

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from hotelareascore.config import DIMENSIONS, ETL_DIR, load_cities  # noqa: E402

BIG_MOVER_THRESHOLD = 15.0
CHANGED_THRESHOLD = 0.05


def load_scores(path: Path) -> dict[str, dict]:
    con = duckdb.connect()
    cols = ["hotel_id", "balanced_score"] + list(DIMENSIONS)
    rows = con.execute(f"SELECT {', '.join(cols)} FROM read_parquet('{path.as_posix()}')").fetchall()
    return {r[0]: dict(zip(cols[1:], r[1:])) for r in rows}


def load_names(hotels_path: Path) -> dict[str, str]:
    con = duckdb.connect()
    rows = con.execute(f"SELECT id, name FROM read_parquet('{hotels_path.as_posix()}')").fetchall()
    return {r[0]: r[1] or "(unnamed)" for r in rows}


def diff_city(city_id: str, old_scores: dict[str, dict], new_scores: dict[str, dict], names: dict[str, str]) -> str:
    common = set(old_scores) & set(new_scores)
    added = set(new_scores) - set(old_scores)
    removed = set(old_scores) - set(new_scores)

    deltas = [(hid, new_scores[hid]["balanced_score"] - old_scores[hid]["balanced_score"]) for hid in common]
    changed = [d for d in deltas if abs(d[1]) >= CHANGED_THRESHOLD]
    big_movers = [d for d in deltas if abs(d[1]) >= BIG_MOVER_THRESHOLD]
    mean_delta = sum(d[1] for d in deltas) / len(deltas) if deltas else 0.0
    min_delta = min((d[1] for d in deltas), default=0.0)
    max_delta = max((d[1] for d in deltas), default=0.0)

    per_dim_changed = {}
    for dim in DIMENSIONS:
        n = sum(
            1 for hid in common if abs(new_scores[hid][dim] - old_scores[hid][dim]) >= CHANGED_THRESHOLD
        )
        per_dim_changed[dim] = n

    lines = [f"## {city_id}", ""]
    lines.append(f"- Hotels: {len(common)} common" + (f", {len(added)} added" if added else "") + (f", {len(removed)} removed" if removed else ""))
    lines.append(f"- Balanced score changed: {len(changed)} ({100*len(changed)/len(common):.1f}%)" if common else "- Balanced score changed: n/a")
    lines.append(f"- Big movers (|Δ| ≥ {BIG_MOVER_THRESHOLD}): {len(big_movers)} ({100*len(big_movers)/len(common):.1f}%)" if common else "")
    lines.append(f"- Mean Δ balanced score: {mean_delta:.2f} (range {min_delta:.2f} to {max_delta:.2f})")
    lines.append(
        "- Per-dimension hotels changed: "
        + ", ".join(f"{dim}={n}" for dim, n in per_dim_changed.items())
    )
    lines.append("")

    top = sorted(deltas, key=lambda d: d[1])[:10]
    if top:
        lines.append("Top 10 biggest balanced-score drops:")
        lines.append("")
        lines.append("| Hotel | Old | New | Δ |")
        lines.append("|---|---:|---:|---:|")
        for hid, delta in top:
            old_v = old_scores[hid]["balanced_score"]
            new_v = new_scores[hid]["balanced_score"]
            lines.append(f"| {names.get(hid, hid)} | {old_v:.1f} | {new_v:.1f} | {delta:+.1f} |")
        lines.append("")

    top_gains = sorted(deltas, key=lambda d: -d[1])[:10]
    top_gains = [d for d in top_gains if d[1] > 0]
    if top_gains:
        lines.append("Top 10 biggest balanced-score gains:")
        lines.append("")
        lines.append("| Hotel | Old | New | Δ |")
        lines.append("|---|---:|---:|---:|")
        for hid, delta in top_gains:
            old_v = old_scores[hid]["balanced_score"]
            new_v = new_scores[hid]["balanced_score"]
            lines.append(f"| {names.get(hid, hid)} | {old_v:.1f} | {new_v:.1f} | {delta:+.1f} |")
        lines.append("")

    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--old-dir", required=True, help="directory with <city>/hotel_scores.parquet for the old version")
    ap.add_argument("--old-version", required=True)
    ap.add_argument("--new-version", required=True)
    ap.add_argument("--release", default="2026-08-19.0")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    old_dir = Path(args.old_dir)
    repo_root = Path(__file__).resolve().parents[1]
    etl_dir = repo_root / "data/etl" / args.release

    cities = list(load_cities().keys())
    sections = [
        f"# Score-version diff report — {args.old_version} → {args.new_version}",
        "",
        "Per docs/scoring.md §5: this diff is for owner review before this minor/major "
        "score_version ships.",
        "",
    ]
    for city_id in cities:
        old_path = old_dir / city_id / "hotel_scores.parquet"
        new_path = etl_dir / city_id / "hotel_scores.parquet"
        if not old_path.exists() or not new_path.exists():
            sections.append(f"## {city_id}\n\n(missing old or new scores, skipped)\n")
            continue
        old_scores = load_scores(old_path)
        new_scores = load_scores(new_path)
        names = load_names(etl_dir / city_id / "hotels.parquet")
        sections.append(diff_city(city_id, old_scores, new_scores, names))

    out_path = Path(args.out)
    out_path.write_text("\n".join(sections), encoding="utf-8")
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
