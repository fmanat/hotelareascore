# Phase 3 Batch 1 ingestion report — 8 new cities

Batch 1 of the Phase 3 plan (`docs/reports/phase-3-plan.md`): Paris, Rome, Barcelona, Amsterdam, Lisbon, Sydney, Tokyo, Dubai — ingested, scored, and validated on Overture release `2026-08-19.0`, `score_version 1.0.1`. Entity-QA fixes (items a-d, `docs/STATE.md`) applied to this batch; London and Bangkok were **not** re-ingested (Phase 2 already closed on that data — see the note in `data/config/cities.yml`).

## Entity QA: what actually shipped

The non-hotel name-heuristic (item a) took 3 iterations against this batch's real data before it was safe to trust — worth stating plainly rather than glossing over:

1. **First pass wrongly excluded real hotels** — "tower"/"design" as exclusion markers caught legitimate boutique-hotel branding ("Design Hotel", "Design Apartments") and, severely, most of Dubai's OYO-branded short-term rentals (named after their residential tower, e.g. "OYO 985 Home 1BR Lake City Tower") — **69 of Dubai's 2,070 candidate hotels (3.3%) were wrongly dropped** in that pass.
2. Accented spellings of "hotel" itself weren't recognized ("Hôtel Design Sorbonne" has no plain-ASCII "hotel" match) — fixed with accent-folding.
3. A marker without its own word boundary matched *inside* unrelated words — "temple" inside "Templeton", "church" inside "Hornchurch" (a real London place name) — fixed by bounding every marker individually.

**Net result after all fixes:** exclusion rate dropped from an initial (buggy) 1.14% to a spot-checked **0.26%** across all 10 ingested cities (79 hotels total). Every exclusion is logged in full in each city's `manifest.json` (`entity_qa_excluded_names`) for owner spot-check — not just a sample.

**Known, honest limitation:** the heuristic is effectively English-market-only. It has real recall on London/Bangkok's UK-registered-business-style names (Ltd, Consulting, Housing Association, University) but almost none on French/Italian/Spanish/Japanese/Arabic business names — most new cities show a handful of exclusions (0-6), not because they lack non-hotel noise, but because this pattern-matching approach doesn't understand other languages' business-naming conventions. Worth a language-aware version before this is trusted as a real cleanup mechanism rather than a light first pass.

## Per-city summary

| City | Hotels (raw→final) | Entity-QA excluded | Rejected lodging (rate) | Dupe rate | Median confidence |
|---|---:|---:|---:|---:|---:|
| london *(not re-ingested)* | 4,464 → 4,463 | — | 1,096 (19.7%) | 0.02% | 95.4 |
| bangkok *(not re-ingested)* | 7,560 → 7,558 | — | 11,265 (59.8%) | 0.03% | 90.65 |
| paris | 3,596 → 3,582 | 6 | 565 (13.6%) | 0.22% | 98.56 |
| rome | 5,050 → 5,040 | 6 | 1,649 (24.7%) | 0.08% | 94.02 |
| barcelona | 1,722 → 1,720 | 1 | 363 (17.4%) | 0.06% | 97.09 |
| amsterdam | 1,072 → 1,071 | 0 | 134 (11.1%) | 0.09% | 96.26 |
| lisbon | 1,289 → 1,289 | 0 | 276 (17.6%) | 0.0% | 96.26 |
| sydney | 1,083 → 1,080 | 3 | 235 (17.9%) | 0.0% | 93.73 |
| tokyo | 2,748 → 2,745 | 3 | 554 (16.8%) | 0.0% | 97.65 |
| dubai | 2,070 → 2,065 | 5 | 656 (24.1%) | 0.0% | 91.34 |

Bangkok's 59.8% rejected-lodging rate remains the known outlier (docs/STATE.md bounded task); every Batch 1 city lands in the 11-25% range London already showed (19.7%) — confirms the Phase 3 plan's prediction that Bangkok's severity, not the existence of the pattern itself, was the anomaly.

## New anomaly checks (entity QA items b, c)

| City | Numeric-only names | Far from center (>15 km) |
|---|---:|---:|
| london | 7 | 928 |
| bangkok | — | — |
| paris | 0 | 3 |
| rome | 0 | 0 |
| barcelona | 0 | 0 |
| amsterdam | 0 | 0 |
| lisbon | 0 | 0 |
| sydney | 0 | 72 |
| tokyo | 1 | 221 |
| dubai | 0 | 554 |

London's 928 far-from-center hotels (20.8% of the city) is a real, sizeable finding from turning this check on for the first time — its bbox pulls in commuter towns up to 38 km out (Sevenoaks, Guildford, Stansted). Not re-ingested this round (Phase 2 already closed on that data); every affected hotel now carries an honest "N km from central London" disclosure on its result page instead of implying it's simply "in London" (`webdata.py` `far_from_center`). Batch 1's own bboxes were deliberately tightened for exactly this reason (`cities.yml`) — Tokyo (221) and Dubai (554) still show meaningful counts, Dubai expected given its linear coastal geography (Downtown Dubai and Dubai Marina are themselves ~25 km apart) rather than a bbox error.

## Volumetric estimate: real data vs. the Phase 3 plan's ~130 MB

- **30,613 hotels** across the 10 ingested cities (London + Bangkok + Batch 1) — the Phase 3 plan projected ~35,700 for all 12 (this batch + estimated New York/Singapore).
- **366,394 nearby_facts rows** (~12/hotel, our cap) — plan projected ~428,000 for 12 cities.
- Applying `docs/data-and-costs.md §2`'s per-row Postgres-equivalent assumptions (750 B/hotel, 375 B/hotel_scores row, 125 B/nearby_facts row) to these **real** counts: **~115 MB for these 10 cities**, projecting to **~123 MB at 12** once New York + Singapore are added — within 6% of the Phase 3 plan's ~130 MB estimate. Still comfortably inside Supabase Free (500 MB).
- Raw ETL Parquet on disk for these 10 cities (compressed, not the Postgres-equivalent estimate above): hotels 3.7 MB, hotel_scores 2.9 MB, nearby_facts 10.8 MB — parquet compression means this is much smaller than the serving-DB estimate above; it's not the same number and isn't meant to be compared directly.

## Pipeline performance

- Batch 1 ingest: 369s total across 8 cities.
- Batch 1 score: 159s total.
- **Cost: €0** — same free-tier basis as Phases 1-2 (docs/reports/phase-3-plan.md §5).

## Next

- Batch 1 data is ready for the golden-set labeling tool.
- Batch 2 (New York, Singapore) can run once explicitly instructed — the entity-QA taxonomy fix that was the stated precondition is now live and tested, but per the approved plan, Batch 2 waits for its own go-ahead.
- Entity-QA items (b)-(d) validation/display changes are live for this batch; consider a language-aware pass on item (a) before relying on it for non-English-market cleanup.

