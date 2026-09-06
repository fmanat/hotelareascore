#!/usr/bin/env python3
"""Seeds/updates data/serving/page_publication.sqlite (Bloc C item 1,
overnight mission) -- the ONLY place hotel/city/static page indexability
decisions are recorded, per CLAUDE.md hard rule 2 and
docs/seo-policy.md §6. Idempotent: re-running updates existing rows with a
fresh `reason`/`decided_at` rather than duplicating; never deletes a row
(a page that no longer qualifies moves to noindex/draft, it doesn't
disappear from the audit trail).

Every write goes through publication.set_status, which requires a reason
and a decider -- there is no path in this script that flips a status
without one.
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from hotelareascore import publication  # noqa: E402
from hotelareascore.config import ETL_DIR, load_cities  # noqa: E402

RELEASE = "2026-08-19.0"
DECIDER = "system:compute_publication"

STATIC_PAGES_INDEXABLE = {
    "home": "Always-potentially-indexable page type (docs/seo-policy.md §3).",
    "methodology": "Always-potentially-indexable page type (docs/seo-policy.md §3).",
}
STATIC_PAGES_NOINDEX = {
    "compare": "Combinatorial comparison page -- never create indexable URLs merely "
               "because they can be generated (CLAUDE.md hard rule 2).",
}
STATIC_PAGES_DRAFT = {
    "legal-notice": "Owner-provided template, not yet reviewed (overnight mission Bloc C item 5).",
    "privacy": "Owner-provided template, not yet reviewed (overnight mission Bloc C item 5).",
    "affiliate-disclosure": "Owner-provided template, not yet reviewed (overnight mission Bloc C item 5).",
    "terms": "Owner-provided template, not yet reviewed (overnight mission Bloc C item 5).",
}


def load_pilot_cohort_ids() -> set[str]:
    path = ROOT / "docs/reports/pilot-cohort-proposal.csv"
    if not path.exists():
        print("WARNING: pilot-cohort-proposal.csv not found -- no hotel will be marked indexable.", file=sys.stderr)
        return set()
    with open(path, newline="", encoding="utf-8") as f:
        return {row["id"] for row in csv.DictReader(f)}


def main() -> None:
    pilot_ids = load_pilot_cohort_ids()
    con_duck = duckdb.connect()

    with publication.connect() as con:
        for page_id, reason in STATIC_PAGES_INDEXABLE.items():
            publication.set_status(con, "static", page_id, "indexable", reason, DECIDER)
        for page_id, reason in STATIC_PAGES_NOINDEX.items():
            publication.set_status(con, "static", page_id, "noindex", reason, DECIDER)
        for page_id, reason in STATIC_PAGES_DRAFT.items():
            publication.set_status(con, "static", page_id, "draft", reason, DECIDER)

        for city_id in load_cities():
            # Bloc C item 4: all 12 city pages generated, all noindex.
            publication.set_status(
                con, "city", city_id, "noindex",
                "City page template shipped this session but not yet measured "
                "against real search demand (docs/seo-policy.md §3) -- noindex "
                "until a Phase 4 decision.",
                DECIDER,
            )

            etl_dir = ETL_DIR / RELEASE / city_id
            hotels_path = etl_dir / "hotels.parquet"
            scores_path = etl_dir / "hotel_scores.parquet"
            if not (hotels_path.exists() and scores_path.exists()):
                continue

            rows = con_duck.execute(f"""
                WITH coincident AS (
                    SELECT lat, lon FROM read_parquet('{hotels_path.as_posix()}')
                    GROUP BY lat, lon HAVING count(*) > 1
                )
                SELECT h.id, s.score_version,
                       regexp_matches(trim(h.name), '^[0-9]+$') AS is_numeric_name,
                       (h.lat, h.lon) IN (SELECT (lat, lon) FROM coincident) AS is_coincident
                FROM read_parquet('{hotels_path.as_posix()}') h
                JOIN read_parquet('{scores_path.as_posix()}') s ON s.hotel_id = h.id
            """).fetchall()

            for hotel_id, score_version, is_numeric_name, is_coincident in rows:
                if hotel_id in pilot_ids:
                    publication.set_status(
                        con, "hotel", hotel_id, "indexable",
                        "Pilot cohort selection (docs/reports/pilot-cohort-proposal.md).",
                        "system:pilot_cohort_selection", score_version,
                    )
                elif is_numeric_name or is_coincident:
                    publication.set_status(
                        con, "hotel", hotel_id, "draft",
                        "Numeric-only name or unresolved duplicate-coordinate cluster "
                        "(validate.py QA flags) -- not ready to even be a noindex-but-visible page.",
                        DECIDER, score_version,
                    )
                else:
                    publication.set_status(
                        con, "hotel", hotel_id, "noindex",
                        "Default noindex outside the pilot cohort (docs/seo-policy.md §3).",
                        DECIDER, score_version,
                    )

    with publication.connect() as con:
        for status in ("draft", "noindex", "indexable", "retired"):
            n_hotel = len(publication.list_by_status(con, status, "hotel"))
            n_city = len(publication.list_by_status(con, status, "city"))
            n_static = len(publication.list_by_status(con, status, "static"))
            print(f"{status}: {n_hotel} hotel, {n_city} city, {n_static} static")

    print(f"\nWrote {publication.DB_PATH}")


if __name__ == "__main__":
    main()
