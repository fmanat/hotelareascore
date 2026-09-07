#!/usr/bin/env python3
"""Score-version diff for family_convenience 1.2.0 -> 1.2.1 only
(docs/scoring.md §5 point 2), all 12 cities, all hotels.

data/etl/ is gitignored and hotel_scores.parquet was already overwritten
in place by the v1.2.1 score run before this diff was written, so there is
no saved v1.2.0 snapshot to read back. Green-space source data (green_spaces
.parquet) is unchanged between 1.2.0 and 1.2.1 -- only the per-polygon
weight changed -- so this recomputes the OLD (unweighted, weight=1.0 for
every hit) and NEW (docs/adr/009 weighted) family_convenience score directly
from that unchanged source in the same query, rather than diffing two
on-disk snapshots. Read-only; writes a markdown report, changes nothing.
"""
from __future__ import annotations

import sys
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from hotelareascore import geo, taxonomy  # noqa: E402
from hotelareascore.config import ETL_DIR, load_cities, load_score_weights  # noqa: E402

RELEASE = "2026-08-19.0"
BIG_MOVER_THRESHOLD = 15.0


def city_diff(con, city) -> dict:
    etl_dir = ETL_DIR / RELEASE / city.id
    con.execute(f"CREATE OR REPLACE TEMP TABLE hotels AS SELECT * FROM read_parquet('{(etl_dir / 'hotels.parquet').as_posix()}')")
    con.execute(f"CREATE OR REPLACE TEMP TABLE pois AS SELECT * FROM read_parquet('{(etl_dir / 'pois.parquet').as_posix()}')")
    con.execute(f"CREATE OR REPLACE TEMP TABLE green_spaces AS SELECT * FROM read_parquet('{(etl_dir / 'green_spaces.parquet').as_posix()}')")

    weights = load_score_weights()
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
    weight_sql_new = taxonomy.family_convenience_land_weight_sql("g.subtype", "g.class", f"ST_Area({proj_g})")

    def formula(weight_expr: str, name: str) -> str:
        return f"""
        WITH point_hit AS (
            SELECT h.id AS hotel_id, ST_Distance({proj_h}, {proj_p}) AS d, 1.0 AS weight
            FROM hotels h JOIN pois p
              ON p.lon BETWEEN h.lon - {dlon} AND h.lon + {dlon}
             AND p.lat BETWEEN h.lat - {dlat} AND h.lat + {dlat}
             AND {point_predicate}
        ),
        green_hit AS (
            SELECT h.id AS hotel_id, ST_Distance({proj_h}, {proj_g}) AS d, {weight_expr} AS weight
            FROM hotels h JOIN green_spaces g
              ON g.bbox_xmin <= h.lon + {dlon} AND g.bbox_xmax >= h.lon - {dlon}
             AND g.bbox_ymin <= h.lat + {dlat} AND g.bbox_ymax >= h.lat - {dlat}
        ),
        combined AS (
            SELECT hotel_id, d, weight FROM point_hit WHERE d <= {radius_m}
            UNION ALL
            SELECT hotel_id, d, weight FROM green_hit WHERE d <= {radius_m} AND weight > 0
        ),
        agg AS (SELECT hotel_id, sum(weight * {geo.decay_sql('d', decay_scale_m)}) AS wc FROM combined GROUP BY hotel_id)
        SELECT h.id AS hotel_id, h.name,
               {hybrid_w} * (100.0 * (1 - exp(-coalesce(a.wc, 0.0) / {saturation})))
                 + {1 - hybrid_w} * (percent_rank() OVER (ORDER BY coalesce(a.wc, 0.0)) * 100) AS {name}
        FROM hotels h LEFT JOIN agg a ON a.hotel_id = h.id
        """

    old_sql = formula("1.0", "old_score")
    new_sql = formula(weight_sql_new, "new_score")
    rows = con.execute(f"""
        SELECT o.hotel_id, o.name, o.old_score, n.new_score, (n.new_score - o.old_score) AS delta
        FROM ({old_sql}) o JOIN ({new_sql}) n USING (hotel_id)
    """).fetchall()
    deltas = [r[4] for r in rows]
    n = len(deltas)
    mean_shift = sum(deltas) / n if n else 0.0
    big_movers = sorted(rows, key=lambda r: abs(r[4]), reverse=True)[:5]
    n_big = sum(1 for d in deltas if abs(d) > BIG_MOVER_THRESHOLD)
    return {
        "city": city.id, "n": n, "mean_shift": mean_shift, "n_big_movers": n_big,
        "pct_big_movers": 100.0 * n_big / n if n else 0.0,
        "top_movers": [(r[1], r[2], r[3], r[4]) for r in big_movers],
    }


def main() -> None:
    con = duckdb.connect()
    con.execute("INSTALL spatial; LOAD spatial;")
    cities = load_cities()
    lines = [
        "# family_convenience 1.2.0 -> 1.2.1 diff (all 12 cities, all hotels)",
        "",
        "> docs/scoring.md §5 point 2. Recomputed both formulas live from the",
        "> unchanged green_spaces source (see script docstring for why this",
        "> isn't a snapshot diff) -- only family_convenience changes; every",
        "> other dimension and the golden-set labels are untouched by this ADR.",
        "",
        "| City | n hotels | mean shift | hotels moved >15pts | % |",
        "|---|---:|---:|---:|---:|",
    ]
    total_n = 0
    total_big = 0
    all_top = []
    for city_id, city in cities.items():
        r = city_diff(con, city)
        lines.append(f"| {city_id} | {r['n']} | {r['mean_shift']:+.1f} | {r['n_big_movers']} | {r['pct_big_movers']:.1f}% |")
        total_n += r["n"]
        total_big += r["n_big_movers"]
        all_top.extend((city_id, *m) for m in r["top_movers"])
    lines.append(f"| **all 12** | **{total_n}** | | **{total_big}** | **{100.0*total_big/total_n:.1f}%** |")
    lines.append("")
    lines.append("## Largest movers across all 12 cities")
    lines.append("")
    all_top.sort(key=lambda t: abs(t[4]), reverse=True)
    lines.append("| City | Hotel | old (1.2.0) | new (1.2.1) | delta |")
    lines.append("|---|---|---:|---:|---:|")
    for city_id, name, old, new, delta in all_top[:15]:
        lines.append(f"| {city_id} | {name} | {old:.1f} | {new:.1f} | {delta:+.1f} |")

    out = ROOT / "docs/reports/score-diff-1.2.0-to-1.2.1.md"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {out}")
    print(f"Total: {total_n} hotels, {total_big} moved >15pts ({100.0*total_big/total_n:.1f}%)")


if __name__ == "__main__":
    main()
