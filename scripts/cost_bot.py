#!/usr/bin/env python3
"""Cost bot (docs/data-and-costs.md §6, CLAUDE.md header budget: <=EUR200
setup, <=EUR50/month, target <=EUR35 steady-state).

No live billing API is queried -- no Cloudflare/Supabase account is wired
into this environment yet (CLAUDE.md hard rule 8: no secrets here), and per
docs/STATE.md every service in use today is still on its free tier. This
script is therefore an ESTIMATE aggregator, not a billing poller: it
measures real, local proxies (actual ETL output size on disk, actual
hotel/dimension row counts) and compares them against the free-tier
ceilings and volumetric estimate already documented in
docs/data-and-costs.md §2, so a real cost pressure shows up here BEFORE an
actual bill does.

Run manually (`python3 scripts/cost_bot.py`) or from the weekly ops
workflow (.github/workflows/ops-weekly.yml). Writes a dated row to
docs/STATE.md's "Cost tracker" table; never edits anything else in that
file.
"""
from __future__ import annotations

import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from hotelareascore.config import ETL_DIR, load_cities  # noqa: E402

# docs/data-and-costs.md §2: documented free-tier ceiling and the
# volumetric estimate the serving-world design was sized against.
SUPABASE_FREE_TIER_MB = 500
SERVING_WORLD_ESTIMATE_MB = 285  # 12-city order-of-magnitude estimate, same doc

# CLAUDE.md header budget.
STEADY_STATE_TARGET_EUR = 35
HARD_BUDGET_EUR = 50


def dir_size_mb(path: Path) -> float:
    if not path.exists():
        return 0.0
    total = sum(f.stat().st_size for f in path.rglob("*") if f.is_file())
    return total / (1024 * 1024)


def latest_release_dir() -> Path | None:
    if not ETL_DIR.exists():
        return None
    releases = sorted(p for p in ETL_DIR.iterdir() if p.is_dir())
    return releases[-1] if releases else None


def count_hotels(release_dir: Path) -> int:
    import duckdb

    con = duckdb.connect()
    total = 0
    for city_id in load_cities():
        path = release_dir / city_id / "hotels.parquet"
        if path.exists():
            total += con.execute(f"SELECT count(*) FROM read_parquet('{path.as_posix()}')").fetchone()[0]
    return total


def main() -> None:
    release_dir = latest_release_dir()
    etl_size_mb = dir_size_mb(ETL_DIR)
    n_hotels = count_hotels(release_dir) if release_dir else 0

    print(f"ETL world (local, would sync to R2): {etl_size_mb:,.0f} MB across "
          f"{release_dir.name if release_dir else 'no release'}")
    print(f"Hotels scored: {n_hotels:,}")
    print(f"Serving-world estimate (docs/data-and-costs.md §2, 12 cities): "
          f"~{SERVING_WORLD_ESTIMATE_MB} MB "
          f"({100 * SERVING_WORLD_ESTIMATE_MB / SUPABASE_FREE_TIER_MB:.0f}% of "
          f"Supabase's {SUPABASE_FREE_TIER_MB} MB free tier)")

    # No live billing today: every service in use is free-tier (Cloudflare
    # Pages/Workers/Analytics, Supabase Free, GitHub Actions). Real EUR cost
    # is 0 until a paid tier is deliberately switched on (CLAUDE.md hard
    # rule 1: never introduce a paid dependency without documenting cost
    # now, cost at 10k visits/day, and a cheaper fallback -- none has been).
    est_recurring_eur = 0
    driver = "-"
    notes_parts = [f"{n_hotels:,} hotels, {etl_size_mb:,.0f} MB ETL output, all free tiers"]

    if est_recurring_eur > HARD_BUDGET_EUR:
        print(f"ALERT: estimated recurring EUR{est_recurring_eur} exceeds the "
              f"EUR{HARD_BUDGET_EUR} hard budget.")
    elif est_recurring_eur > STEADY_STATE_TARGET_EUR:
        print(f"WARNING: estimated recurring EUR{est_recurring_eur} exceeds the "
              f"EUR{STEADY_STATE_TARGET_EUR} steady-state target -- see "
              "docs/data-and-costs.md §6 mitigation order.")
    else:
        print(f"OK: estimated recurring EUR{est_recurring_eur}/month, within budget.")

    month = time.strftime("%Y-%m")
    notes = "; ".join(notes_parts)
    row = f"| {month} | {est_recurring_eur} | {driver} | {notes} |"

    state_path = ROOT / "docs/STATE.md"
    text = state_path.read_text(encoding="utf-8")
    month_row_re = re.compile(rf"^\| {re.escape(month)} \|.*\|$", re.MULTILINE)
    if month_row_re.search(text):
        text = month_row_re.sub(row, text)
        print(f"Updated existing {month} row in docs/STATE.md.")
    else:
        # Insert right after the table header (the two lines starting the
        # "Cost tracker" table), before any existing month rows.
        header_re = re.compile(r"(\| Month \| Est\. recurring € \| Main driver \| Notes \|\n\|---\|---:\|---\|---\|\n)")
        if not header_re.search(text):
            print("Could not find the Cost tracker table header in docs/STATE.md -- not modified.", file=sys.stderr)
            sys.exit(1)
        text = header_re.sub(r"\1" + row + "\n", text)
        print(f"Inserted new {month} row in docs/STATE.md.")
    state_path.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()
