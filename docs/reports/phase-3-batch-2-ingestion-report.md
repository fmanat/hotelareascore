# Phase 3 Batch 2 ingestion report — New York, Singapore

Batch 2 of the Phase 3 plan (`docs/reports/phase-3-plan.md`), run after the coverage check ([`phase-3-coverage-bangkok-nyc.md`](phase-3-coverage-bangkok-nyc.md)) recommended proceeding as-is. Bboxes tightened per the Batch 1 lesson (`data/config/cities.yml`) — New York to the 5 boroughs proper, Singapore to the city-state's own extent (no "wrong suburb" to trim there). Ingested, scored (`score_version 1.0.1`), validated on release `2026-08-19.0`. This completes all 12 Phase 3 launch cities.

## A 4th entity-QA bug, found by this batch

New York and Singapore surfaced a new false-positive class before this report could be written honestly: **"union" matched inside "W New York – Union Square"** (a real W Hotels property) and **"mosque" matched inside "Wink @ Mosque Street"** (a real Singapore hostel address) — both are streets/squares named after the concept the marker means to catch, not an instance of it. "bank"/"church"/"temple" carry the identical risk (Bank St, Church St, Temple Pl all exist somewhere). Fixed: these four markers now carry a guard — not flagged when immediately followed by a street-type word (street, road, square, avenue, place, ...); "union" itself was dropped outright, no genuine hit for it has turned up yet, only collisions. Regression-tested (`tests/test_entity_qa.py`). Both cities were re-ingested after the fix; the numbers below are post-fix.

**Known residual staleness, not corrected retroactively:** the same fix would rescue 2 already-excluded Dubai records ("...union metro dubai" — Dubai's Union metro station, another place-name collision). Batch 1 is not being re-ingested for this (already reported and out of this request's scope) — noted here and in `entity_qa.py` for visibility.

## Per-city summary

| City | Hotels (raw→final) | Entity-QA excluded | Rejected lodging (rate) | Dupe rate | Median confidence |
|---|---:|---:|---:|---:|---:|
| new_york | 2,216 → 2,194 | 10 | 1,992 (47.6%) | 0.54% | 97.6 |
| singapore | 1,244 → 1,238 | 6 | 1,306 (51.3%) | 0.0% | 93.1 |

Both land at 47.6% (New York) / 51.3% (Singapore) rejected-lodging rate — confirming the Phase 3 plan's prediction exactly: these two share Bangkok's (59.8%) generic-`lodging` data-quality asymmetry, unlike the 8 Batch 1 cities (11-25%). This is the pattern the coverage report was built to check, and its recommendation (proceed as-is, revisit via `search_events` demand signal in Phase 4) stands.

## New anomaly checks

| City | Numeric-only names | Far from center (>15 km) |
|---|---:|---:|
| new_york | 0 | 447 |
| singapore | 0 | 128 |

New York: 447 hotels (20.4%) over 15 km from center — similar rate to London's 20.8%, expected for a genuinely large metro area covering all 5 boroughs (not a bbox error the way London's commuter-belt overreach was). Singapore: 128 (10.3%) — lower, consistent with being a compact city-state where most points are naturally close to the center.

## All 12 cities: cumulative volumetric estimate

- **34,045 hotels** across all 12 launch cities (Phase 3 plan projected ~35,700).
- **407,412 nearby_facts rows** (~12/hotel cap).
- Postgres-equivalent estimate (same `docs/data-and-costs.md §2` per-row assumptions as before): hotels 25.5 MB + hotel_scores 19.2 MB + nearby_facts 50.9 MB + baselines/publication/events 35 MB = **~131 MB total** — within **0.5%** of the Phase 3 plan's ~130 MB estimate, and comfortably inside Supabase Free (500 MB, ~26% utilized).
- Real ETL Parquet on disk for all 12 cities (compressed, not the Postgres-equivalent estimate): 19.2 MB.

**Phase 3 ingestion is now complete for all 12 launch cities.**

## Pipeline performance

- Batch 2 ingest: 95s total across 2 cities.
- Batch 2 score: 35s total.
- **Cost: €0** — same free-tier basis as Phases 1-2 and Batch 1.

## Next

- Golden-set wave 2 (~8 New York/Singapore hotels) to be added to `tests/golden/selection.json` and the labeling tool republished, preserving in-progress wave-1 labels.
- Phase 4 commitment recorded in `docs/STATE.md`: `search_events` (unfulfilled searches) becomes the coverage KPI — real demand data on missing hotels, not another blind sampling pass, decides whether the rejected-lodging rescue rule gets built.

