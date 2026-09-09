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
from hotelareascore.slug import is_numeric_name  # noqa: E402

RELEASE = "2026-08-19.0"
DECIDER = "system:compute_publication"

STAGED_REASON = (
    "Staged for go-live (docs/reports/go-live-seo-checklist.md, night mission #2 "
    "Tache 3) -- ready, but 'draft' not 'indexable' because the owner cohort "
    "review (docs/STATE.md open decision (b)) has not happened yet. 'indexable' "
    "is the recorded decision that flips this AFTER that review, one deliberate "
    "step at a time per the checklist -- never a side effect of this script."
)

# TRAP, found the hard way (night mission #3, Tache 6): while the cohort
# sits in this staged 'draft' state, `make webdata` / `python3 -m
# hotelareascore.cli webdata` silently SHRINKS the static-page subset
# (webdata.py's select_static_subset only forces a hotel in via the
# publication_status == 'indexable' rule -- staged 'draft' doesn't count,
# even though it's a curated real cohort). Re-running webdata now would
# drop ~188 of the 200 cohort hotels' real pages, contradicting
# docs/reports/go-live-sitemap-dry-run-report.md's "0 consistency issues"
# until the checklist's step 5 actually flips these to 'indexable' first.
# Do not run webdata as a side effect of an unrelated change while
# anything here is staged -- only as directed, in the order the checklist
# already specifies (flip to indexable, THEN re-run webdata).

# home/methodology were previously seeded straight to "indexable" (Bloc C,
# before the pilot-cohort review existed as an explicit open decision) --
# that was premature per CLAUDE.md hard rule 2 (a recorded decision, not a
# default). "draft" is the honest state until the owner checklist runs --
# see STATIC_PAGES_DRAFT below, not a separate "indexable" bucket anymore.
STATIC_PAGES_NOINDEX = {
    "compare": "Combinatorial comparison page -- never create indexable URLs merely "
               "because they can be generated (CLAUDE.md hard rule 2).",
}
STATIC_PAGES_DRAFT = {
    "home": STAGED_REASON,
    "methodology": STAGED_REASON,
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

    live_hotel_ids: set[str] = set()

    with publication.connect() as con:
        for page_id, reason in STATIC_PAGES_NOINDEX.items():
            publication.set_status(con, "static", page_id, "noindex", reason, DECIDER)
        for page_id, reason in STATIC_PAGES_DRAFT.items():
            publication.set_status(con, "static", page_id, "draft", reason, DECIDER)

        for city_id in load_cities():
            # All 12 city pages are part of the go-live package (night
            # mission #2 Tache 3) -- "draft", not "indexable", for the same
            # reason as the static pages above: staged, pending the owner
            # cohort review, flipped deliberately by the checklist.
            publication.set_status(con, "city", city_id, "draft", STAGED_REASON, DECIDER)

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
                SELECT h.id, h.name, s.score_version,
                       (h.lat, h.lon) IN (SELECT (lat, lon) FROM coincident) AS is_coincident
                FROM read_parquet('{hotels_path.as_posix()}') h
                JOIN read_parquet('{scores_path.as_posix()}') s ON s.hotel_id = h.id
            """).fetchall()

            for hotel_id, hotel_name, score_version, is_coincident in rows:
                live_hotel_ids.add(hotel_id)
                # is_numeric_name: slug.py's single source of truth
                # (docs/adr/014) -- also the hard gate publication.set_status
                # itself enforces below via hotel_name, so this branch and
                # that gate can never disagree.
                numeric = is_numeric_name(hotel_name)
                if hotel_id in pilot_ids:
                    publication.set_status(
                        con, "hotel", hotel_id, "draft",
                        "Pilot cohort v2 selection (docs/reports/pilot-cohort-proposal.md, "
                        "Latin-script gate + bad-geocode fixes applied) -- " + STAGED_REASON,
                        "system:pilot_cohort_selection", score_version, hotel_name,
                    )
                elif numeric or is_coincident:
                    publication.set_status(
                        con, "hotel", hotel_id, "draft",
                        "Numeric-only name (docs/adr/014, structurally never indexable) or "
                        "unresolved duplicate-coordinate cluster (validate.py QA flags) -- "
                        "not ready to even be a noindex-but-visible page.",
                        DECIDER, score_version, hotel_name,
                    )
                else:
                    publication.set_status(
                        con, "hotel", hotel_id, "noindex",
                        "Default noindex outside the pilot cohort (docs/seo-policy.md §3).",
                        DECIDER, score_version, hotel_name,
                    )

    # Retire any recorded hotel decision whose hotel_id no longer exists in
    # ANY current city's ETL output (e.g. entity-QA exclusions re-ingested
    # out from under an old id, docs/STATE.md "Bad-geocode records").
    # publication.py's own docstring promises a page that stops qualifying
    # "moves to noindex/draft, it doesn't disappear from the audit trail" --
    # found here as a real gap during Tache 3: a hotel that's gone from the
    # dataset ENTIRELY (not just excluded from the cohort) was never
    # revisited by the loop above at all, leaving a stale "indexable" row
    # for a hotel_id no page can ever be built for. "retired" (already in
    # publication.py's Status enum, unused until now) is the correct state
    # -- distinct from noindex/draft, which both imply "the page still
    # exists, just not indexed/not ready".
    with publication.connect() as con:
        stale = [
            r for r in publication.list_by_status(con, "indexable", "hotel")
            + publication.list_by_status(con, "draft", "hotel")
            + publication.list_by_status(con, "noindex", "hotel")
            if r["page_id"] not in live_hotel_ids
        ]
        for r in stale:
            publication.set_status(
                con, "hotel", r["page_id"], "retired",
                f"No longer present in any city's current ETL output (was {r['status']!r}, "
                f"decided {r['decided_at']} by {r['decided_by']}) -- likely an entity-QA "
                "exclusion re-ingested under a different id set.",
                DECIDER, r.get("score_version"),
            )
        if stale:
            print(f"Retired {len(stale)} stale hotel record(s) no longer in any city's ETL output:")
            for r in stale:
                print(f"  {r['page_id']} (was {r['status']})")

    with publication.connect() as con:
        for status in ("draft", "noindex", "indexable", "retired"):
            n_hotel = len(publication.list_by_status(con, status, "hotel"))
            n_city = len(publication.list_by_status(con, status, "city"))
            n_static = len(publication.list_by_status(con, status, "static"))
            print(f"{status}: {n_hotel} hotel, {n_city} city, {n_static} static")

    print(f"\nWrote {publication.DB_PATH}")


if __name__ == "__main__":
    main()
