"""Per-city score-version diff report (docs/scoring.md §5, point 2): "Run
golden-set regression + per-city diff report (biggest movers, mean shift).
A change that improves one city but breaks another must not ship unnoticed."
Phase 2 has no golden set yet (that's Phase 3); this covers the diff-report
half, which any score_version bump needs regardless.

Compares two previously-computed hotel_scores.parquet snapshots for the same
city (caller is responsible for keeping the "before" snapshot around before
re-scoring — this module does not manage version history on disk).
"""
from __future__ import annotations

from pathlib import Path

from . import overture
from .config import DIMENSIONS


def diff_city(city_id: str, hotels_path: Path, old_path: Path, new_path: Path, big_mover_threshold: float = 15.0) -> dict:
    con = overture.connect()
    q = f"""
        WITH o AS (SELECT hotel_id, {', '.join(f'{d} AS old_{d}' for d in DIMENSIONS)},
                          balanced_score AS old_balanced, score_version AS old_version
                   FROM read_parquet('{old_path}')),
             n AS (SELECT hotel_id, {', '.join(f'{d} AS new_{d}' for d in DIMENSIONS)},
                          balanced_score AS new_balanced, score_version AS new_version
                   FROM read_parquet('{new_path}'))
        SELECT o.hotel_id, o.old_balanced, n.new_balanced, n.new_balanced - o.old_balanced AS balanced_delta,
               {', '.join(f'n.new_{d} - o.old_{d} AS {d}_delta' for d in DIMENSIONS)}
        FROM o JOIN n ON n.hotel_id = o.hotel_id
    """
    con.execute(f"CREATE OR REPLACE TEMP TABLE _diff AS {q}")
    con.execute(f"CREATE OR REPLACE TEMP TABLE _hotels AS SELECT id, name FROM read_parquet('{hotels_path}')")

    old_version, new_version = con.execute(
        f"SELECT (SELECT score_version FROM read_parquet('{old_path}') LIMIT 1),"
        f"       (SELECT score_version FROM read_parquet('{new_path}') LIMIT 1)"
    ).fetchone()

    n_hotels = con.execute("SELECT count(*) FROM _diff").fetchone()[0]
    per_dim_changed = {
        d: con.execute(f"SELECT count(*) FROM _diff WHERE abs({d}_delta) > 0.01").fetchone()[0] for d in DIMENSIONS
    }
    n_balanced_changed = con.execute("SELECT count(*) FROM _diff WHERE abs(balanced_delta) > 0.01").fetchone()[0]
    n_big_movers = con.execute(f"SELECT count(*) FROM _diff WHERE abs(balanced_delta) >= {big_mover_threshold}").fetchone()[0]
    mean_delta, min_delta, max_delta = con.execute(
        "SELECT avg(balanced_delta), min(balanced_delta), max(balanced_delta) FROM _diff"
    ).fetchone()

    top_movers = con.execute(
        """
        SELECT h.name, d.old_balanced, d.new_balanced, d.balanced_delta
        FROM _diff d JOIN _hotels h ON h.id = d.hotel_id
        ORDER BY d.balanced_delta ASC LIMIT 10
        """
    ).fetchall()

    return {
        "city_id": city_id,
        "old_version": old_version,
        "new_version": new_version,
        "n_hotels": n_hotels,
        "n_balanced_changed": n_balanced_changed,
        "n_big_movers": n_big_movers,
        "big_mover_threshold": big_mover_threshold,
        "mean_balanced_delta": round(mean_delta, 2) if mean_delta is not None else 0.0,
        "min_balanced_delta": round(min_delta, 2) if min_delta is not None else 0.0,
        "max_balanced_delta": round(max_delta, 2) if max_delta is not None else 0.0,
        "per_dimension_changed": per_dim_changed,
        "top_movers": [
            {"name": r[0], "old": round(r[1], 1), "new": round(r[2], 1), "delta": round(r[3], 1)} for r in top_movers
        ],
    }


def build_report(diffs: list[dict]) -> str:
    lines: list[str] = []
    old_v = diffs[0]["old_version"] if diffs else "?"
    new_v = diffs[0]["new_version"] if diffs else "?"
    lines.append(f"# Score-version diff report — {old_v} → {new_v}")
    lines.append("")
    lines.append(
        "Per docs/scoring.md §5: this diff is for owner review before a "
        "minor/major score_version ships. Phase 2 has no golden set yet "
        "(Phase 3) — this covers ranking-impact visibility only."
    )
    lines.append("")
    for d in diffs:
        lines.append(f"## {d['city_id']}")
        lines.append("")
        lines.append(f"- Hotels: {d['n_hotels']:,}")
        lines.append(
            f"- Balanced score changed: {d['n_balanced_changed']:,} "
            f"({100 * d['n_balanced_changed'] / d['n_hotels']:.1f}%)"
        )
        lines.append(
            f"- Big movers (|Δ| ≥ {d['big_mover_threshold']} pts): {d['n_big_movers']:,} "
            f"({100 * d['n_big_movers'] / d['n_hotels']:.1f}%)"
        )
        lines.append(
            f"- Mean Δ balanced score: {d['mean_balanced_delta']:+.2f} "
            f"(range {d['min_balanced_delta']:+.2f} to {d['max_balanced_delta']:+.2f})"
        )
        lines.append("- Per-dimension hotels changed: " + ", ".join(f"{k}={v:,}" for k, v in d["per_dimension_changed"].items()))
        lines.append("")
        lines.append("Top 10 biggest balanced-score drops:")
        lines.append("")
        lines.append("| Hotel | Old | New | Δ |")
        lines.append("|---|---:|---:|---:|")
        for m in d["top_movers"]:
            lines.append(f"| {m['name']} | {m['old']} | {m['new']} | {m['delta']:+.1f} |")
        lines.append("")
    return "\n".join(lines) + "\n"
