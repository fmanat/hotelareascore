#!/usr/bin/env python3
"""Pilot cohort selection (Bloc D, overnight mission) per
docs/seo-policy.md §2/§4: propose ~200 hotels for Phase 4's indexable
pilot cohort. REPORT ONLY -- writes docs/reports/pilot-cohort-proposal.md
+ a full CSV; never touches page_publication (which doesn't exist as a
table yet -- see docs/adr/008 in Bloc C) or any indexing flag.

Gate implementation notes (§4's 11 gates), honest about what's computed
vs structural-by-definition at this stage:
  1. confidence >= 80                          -- computed
  2. hotel identity highly reliable             -- computed (proxy below)
  3. all critical score dimensions present      -- computed (poi coverage)
  4. unique location facts present              -- computed (nearby_facts)
  5. city baseline available                    -- always true, all 12 cities
  6. automated content QA passes                -- computed (proxy below)
  7. demonstrated demand OR editorial selection  -- structural: no live
                                                    traffic exists yet
                                                    (search_events isn't
                                                    populated, Phase 4 not
                                                    started), so EVERY
                                                    candidate here is by
                                                    definition the
                                                    "editorial pilot
                                                    selection" branch, not
                                                    independently checked
  8. no canonical duplicate                      -- computed (proxy below)
  9. meaningful comparison/context on page       -- structural: every city
                                                    in this dataset has
                                                    >=1000 hotels, so a
                                                    comparable-hotels
                                                    section always has
                                                    content
  10. user value independent of keyword targeting -- structural, by
                                                     product design (real
                                                     computed scores, not
                                                     keyword-stuffed prose)
  11. affiliate deep-link resolvable OR consciously
      published without CTA                      -- per the owner's
                                                     explicit instruction
                                                     for this run, treated
                                                     as satisfied via the
                                                     "consciously published
                                                     without CTA" branch
                                                     for every candidate
                                                     (no affiliate program
                                                     exists yet, AFFILIATE_
                                                     ENABLED is off)

Gates 1/2/3/4/6/8 are the only ones that actually filter candidates below;
5/7/9/10/11 are recorded as satisfied-by-construction for every row in the
output, not fabricated per-hotel detail.
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from hotelareascore.config import DIMENSIONS, ETL_DIR, load_cities  # noqa: E402
from hotelareascore.entity_qa import HOSPITALITY_BRANDS, _fold  # noqa: E402

RELEASE = "2026-08-19.0"
TARGET_TOTAL = 200
PER_CITY_MIN, PER_CITY_MAX = 12, 25  # docs/seo-policy.md §2
INDEPENDENT_SHARE = 0.70


def is_chain(name: str) -> bool:
    return bool(HOSPITALITY_BRANDS.search(_fold(name or "")))


def load_city_candidates(city_id: str) -> list[dict]:
    con = duckdb.connect()
    etl_dir = ETL_DIR / RELEASE / city_id
    hotels_path = etl_dir / "hotels.parquet"
    scores_path = etl_dir / "hotel_scores.parquet"
    facts_path = etl_dir / "nearby_facts.parquet"
    baseline_path = etl_dir / "city_baseline.json"
    if not (hotels_path.exists() and scores_path.exists()):
        return []

    import json

    baseline = json.loads(baseline_path.read_text()) if baseline_path.exists() else {}

    rows = con.execute(f"""
        WITH coincident AS (
            SELECT lat, lon FROM read_parquet('{hotels_path.as_posix()}')
            GROUP BY lat, lon HAVING count(*) > 1
        ),
        facts AS (
            SELECT hotel_id, count(*) AS n_facts FROM read_parquet('{facts_path.as_posix()}') GROUP BY hotel_id
        )
        SELECT
            h.id, h.name, h.address_locality, h.dedupe_confidence,
            s.confidence, s.balanced_score,
            {', '.join(f's.{d}' for d in DIMENSIONS)},
            coalesce(f.n_facts, 0) AS n_facts,
            (h.lat, h.lon) IN (SELECT (lat, lon) FROM coincident) AS is_coincident,
            regexp_matches(trim(h.name), '^[0-9]+$') AS is_numeric_name
        FROM read_parquet('{hotels_path.as_posix()}') h
        JOIN read_parquet('{scores_path.as_posix()}') s ON s.hotel_id = h.id
        LEFT JOIN facts f ON f.hotel_id = h.id
    """).fetchall()

    cols = ["id", "name", "locality", "dedupe_confidence", "confidence", "balanced_score"] + list(DIMENSIONS) + \
           ["n_facts", "is_coincident", "is_numeric_name"]
    candidates = []
    for row in rows:
        rec = dict(zip(cols, row))
        # Gate 1: confidence >= 80
        if rec["confidence"] < 80:
            continue
        # Gate 2 (proxy): identity reliable -- no dedupe merge needed
        if rec["dedupe_confidence"] < 100:
            continue
        # Gate 3 (proxy): every dimension score present and non-null
        if any(rec[d] is None for d in DIMENSIONS):
            continue
        # Gate 4: at least one nearby fact to show
        if rec["n_facts"] < 1:
            continue
        # Gate 6 (proxy): passes basic content QA -- not a numeric-name record
        if rec["is_numeric_name"]:
            continue
        # Gate 8: no unresolved canonical-duplicate coordinate cluster
        if rec["is_coincident"]:
            continue

        # Distinctiveness: max absolute deviation from city median across
        # the 6 dimensions (docs/seo-policy.md §2: "a hotel where our data
        # tells a story beats a generic one").
        dev = 0.0
        for d in DIMENSIONS:
            median = baseline.get(f"{d}_median")
            if median is not None:
                dev = max(dev, abs(rec[d] - median))
        rec["distinctiveness"] = round(dev, 1)
        rec["chain"] = is_chain(rec["name"])
        rec["city_id"] = city_id
        candidates.append(rec)
    return candidates


def select_for_city(candidates: list[dict], quota: int) -> list[dict]:
    independents = sorted([c for c in candidates if not c["chain"]], key=lambda c: -c["distinctiveness"])
    chains = sorted([c for c in candidates if c["chain"]], key=lambda c: -c["distinctiveness"])

    n_independent = round(quota * INDEPENDENT_SHARE)
    n_chain = quota - n_independent

    picked = independents[:n_independent] + chains[:n_chain]
    # Backfill from whichever pool has leftover supply if the other fell short.
    shortfall = quota - len(picked)
    if shortfall > 0:
        leftover = independents[n_independent:] + chains[n_chain:]
        leftover = [c for c in leftover if c not in picked]
        leftover.sort(key=lambda c: -c["distinctiveness"])
        picked += leftover[:shortfall]
    return picked


def main() -> None:
    cities = list(load_cities().keys())
    all_candidates: dict[str, list[dict]] = {}
    for city_id in cities:
        all_candidates[city_id] = load_city_candidates(city_id)

    # Proportional quota within [PER_CITY_MIN, PER_CITY_MAX], targeting TARGET_TOTAL.
    pool_sizes = {c: len(all_candidates[c]) for c in cities}
    total_pool = sum(pool_sizes.values())
    quotas = {}
    for c in cities:
        share = pool_sizes[c] / total_pool if total_pool else 0
        quota = round(TARGET_TOTAL * share)
        quota = max(PER_CITY_MIN, min(PER_CITY_MAX, quota))
        quota = min(quota, pool_sizes[c])  # never more than available supply
        quotas[c] = quota

    selection: list[dict] = []
    for city_id in cities:
        picked = select_for_city(all_candidates[city_id], quotas[city_id])
        selection.extend(picked)

    # If under target and supply remains, top up from the highest-distinctiveness
    # leftovers across all cities (still respecting PER_CITY_MAX).
    if len(selection) < TARGET_TOTAL:
        picked_ids = {c["id"] for c in selection}
        per_city_count = {c: quotas[c] for c in cities}
        leftover_all = []
        for city_id in cities:
            for c in all_candidates[city_id]:
                if c["id"] not in picked_ids:
                    leftover_all.append(c)
        leftover_all.sort(key=lambda c: -c["distinctiveness"])
        for c in leftover_all:
            if len(selection) >= TARGET_TOTAL:
                break
            if per_city_count[c["city_id"]] >= PER_CITY_MAX:
                continue
            selection.append(c)
            per_city_count[c["city_id"]] += 1

    selection.sort(key=lambda c: (c["city_id"], -c["distinctiveness"]))

    # --- Write CSV (full detail) ---
    csv_path = ROOT / "docs/reports/pilot-cohort-proposal.csv"
    fieldnames = ["city_id", "id", "name", "locality", "chain", "confidence", "balanced_score",
                  "distinctiveness"] + list(DIMENSIONS)
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for c in selection:
            w.writerow({k: c[k] for k in fieldnames})
    print(f"Wrote {csv_path} ({len(selection)} hotels)")

    # --- Write markdown summary report ---
    n_independent = sum(1 for c in selection if not c["chain"])
    n_chain = len(selection) - n_independent
    lines = [
        "# Pilot cohort proposal (Bloc D, overnight mission)",
        "",
        f"> **{len(selection)} hotels proposed** across {len(set(c['city_id'] for c in selection))} cities. "
        "Report only -- no page_publication change, no indexing flag touched. "
        "Full detail: [pilot-cohort-proposal.csv](pilot-cohort-proposal.csv).",
        "",
        "## Method",
        "",
        "Gates 1 (confidence >= 80), 2 (identity reliable -- no dedupe merge "
        "needed), 3 (all 6 dimensions present), 4 (>=1 nearby fact), 6 (not a "
        "numeric-name record), 8 (no unresolved duplicate-coordinate cluster) "
        "from docs/seo-policy.md §4 were computed per hotel and used to filter "
        "candidates. Gates 5, 9, 10 are structurally true for every city in "
        "this dataset (baseline exists, >=1000 hotels means comparison content "
        "always exists, scores are never keyword-stuffed prose by design). "
        "Gate 7 (demonstrated demand OR editorial selection) is the editorial "
        "branch for all 200 -- no live traffic exists yet to demonstrate "
        "demand. Gate 11 (affiliate resolvable OR consciously published "
        "without CTA) is the \"without CTA\" branch for all 200, per this "
        "run's explicit instruction -- no affiliate program exists yet.",
        "",
        f"Within gate-passing candidates: ~70/30 independent/chain weighting "
        f"({n_independent} independent, {n_chain} chain -- "
        f"{100*n_independent/len(selection):.0f}%/{100*n_chain/len(selection):.0f}%), "
        "picked by \"distinctiveness\" (max absolute deviation from the city's "
        "own median across the 6 dimensions -- docs/seo-policy.md §2: \"a hotel "
        "where our data tells a story beats a generic one\"), spread across all "
        f"12 cities within the {PER_CITY_MIN}-{PER_CITY_MAX}/city range from "
        "docs/seo-policy.md §2.",
        "",
        "## Per-city breakdown",
        "",
        "| City | Selected | Independent | Chain | Candidate pool (gates 1-8) |",
        "|---|---:|---:|---:|---:|",
    ]
    for city_id in cities:
        city_rows = [c for c in selection if c["city_id"] == city_id]
        n_ind = sum(1 for c in city_rows if not c["chain"])
        n_ch = len(city_rows) - n_ind
        lines.append(f"| {city_id} | {len(city_rows)} | {n_ind} | {n_ch} | {pool_sizes[city_id]} |")

    lines += [
        "",
        "## Top 5 most distinctive picks per city",
        "",
    ]
    for city_id in cities:
        city_rows = sorted([c for c in selection if c["city_id"] == city_id], key=lambda c: -c["distinctiveness"])[:5]
        if not city_rows:
            continue
        lines.append(f"**{city_id}**")
        lines.append("")
        lines.append("| Hotel | Chain? | Confidence | Balanced | Distinctiveness |")
        lines.append("|---|---|---:|---:|---:|")
        for c in city_rows:
            lines.append(f"| {c['name']} | {'chain' if c['chain'] else 'independent'} | "
                         f"{c['confidence']:.0f} | {c['balanced_score']:.0f} | {c['distinctiveness']:.1f} |")
        lines.append("")

    lines += [
        "## What this is not",
        "",
        "- Not a page_publication change -- that table doesn't exist yet "
        "(Bloc C). This is the candidate list for whoever builds the Phase 4 "
        "publication step.",
        "- Not a demand signal -- gate 7's \"editorial selection\" branch means "
        "this list reflects data quality and distinctiveness, not measured "
        "interest. The 90-day measurement protocol (docs/seo-policy.md §5) "
        "starts only once these are actually indexed.",
        "- Not final -- the owner should sanity-check a sample before Phase 4, "
        "same as every other automated selection in this project.",
        "- **Worth a second look before Phase 4:** \"distinctiveness\" here is "
        "*undirected* (max absolute deviation from the city median, either way) "
        "-- a hotel that scores unusually LOW on a dimension (e.g. very poor "
        "transit access) counts as just as \"distinctive\" as one that scores "
        "unusually HIGH, and some low-balanced-score hotels are in this list "
        "for exactly that reason (see the per-city tables above). That is a "
        "defensible reading of docs/seo-policy.md §2's \"tells a story\" "
        "language (a clearly-quiet-but-far-from-transit hotel is a real, "
        "useful story), but it's an interpretation, not the only one -- if the "
        "owner wants the pilot cohort biased toward hotels that look good "
        "rather than merely distinctive, that's a one-line change to this "
        "script's distinctiveness formula (e.g. weight positive deviations "
        "only, or gate on balanced_score as well).",
    ]

    report_path = ROOT / "docs/reports/pilot-cohort-proposal.md"
    report_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {report_path}")


if __name__ == "__main__":
    main()
