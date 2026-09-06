# STATE.md — project state tracker

> Claude Code: read this first every session; update it whenever phase,
> decisions, or blockers change. Keep it under ~150 lines — this is a
> dashboard, not a journal. Move resolved history to `docs/adr/` or delete it.

## Current phase

**Phase 3 — launch dataset (~12 cities), golden set, calibration** (see
`docs/strategy.md §5`). Plan **approved by owner 2026-09-06** with 3
amendments (2-batch ingestion, 2-wave golden set, blind/mobile-first
labeling tool) — see [`docs/reports/phase-3-plan.md`](reports/phase-3-plan.md).

**Done this session:** entity-QA items (a)-(d) implemented; Batch 1 (Paris,
Rome, Barcelona, Amsterdam, Lisbon, Sydney, Tokyo, Dubai) ingested, scored
(`score_version 1.0.1`), validated —
[ingestion report](reports/phase-3-batch-1-ingestion-report.md). Golden-set
labeling tool built and published (blind, mobile-first, 42 Batch-1 hotels
loaded) — link in chat; not reproduced here since Artifact links aren't
durable repo state. **Batch 2 (New York, Singapore) has NOT been ingested —
waits for its own go-ahead per the approved plan.**

Phase 2 gate: ✅ closed 2026-09-06. Phase 1 Data Proof Report: accepted
2026-09-06 ([report](reports/data-proof-report-2026-08-19.0.md)).

## Phase gate status

| Phase | Gate | Status |
|---|---|---|
| 0 — repo & ADRs | ADR-001…005 merged, CI green | ✅ committed & pushed 2026-09-06 (github.com/fmanat/hotelareascore) |
| 0bis — demand validation | Kill criteria evaluated, owner GO recorded | ✅ **GO recorded 2026-09-06** (see decision log below) |
| 1 — data proof (2 cities) | Data Proof Report accepted by owner | ✅ **accepted 2026-09-06** |
| 2 — product proof | Owner inspected 15–20 hotel outputs | ✅ **closed 2026-09-06** |
| 3 — launch dataset (~12 cities) | Golden set built, calibration done | ▶ current — Batch 1 ingested (10/12 cities), golden-set labeling in progress |
| 4 — SEO launch (incl. pilot hotel cohort) | Pilot cohort live, GSC connected | ☐ |
| 5 — commercial test | First affiliate integrated, clicks measured | ☐ |
| 6 — growth automation | Weekly GSC loop producing PRs | ☐ |

## Open owner decisions

- [ ] Domain/brand name (blocking public launch, not blocking Phases 1–2)
- [ ] Legal vehicle & jurisdiction for the site and affiliate revenue
      (`docs/strategy.md §8` — owner homework)

## Entity QA — done this session (items a-d)

All 4 items from the bounded pre-Phase-3 task are implemented and live in
Batch 1's data (full detail: `docs/reports/phase-3-batch-1-ingestion-report.md`):

- **(a)** `src/hotelareascore/entity_qa.py` — name-pattern non-hotel
  exclusion, wired into `ingest.py`. Took 3 iterations against real Batch 1
  data (see module docstring for the false-positive history — "tower"/
  "design" markers wrongly excluded real hotels, up to 3.3% of Dubai's
  candidates, before removal). **Known limitation: effectively English-market
  only** — near-zero recall on French/Italian/Japanese/Arabic business
  names. Every exclusion logged in full per city (`manifest.json`).
- **(b)** `validate.py` flags purely-numeric and empty hotel names
  (`n_numeric_name`).
- **(c)** Every hotel now carries `distance_from_center_km` +
  `far_from_center` (>15 km, `webdata.py`); result pages show an honest
  disclosure instead of implying "in London" etc. Batch 1 bboxes also
  deliberately tightened (`cities.yml`). London itself: 928 hotels (20.8%)
  are >15 km from center — not re-ingested (Phase 2 closed), but now
  disclosed.
- **(d)** `nearby_facts_display_exclude` in `taxonomy-mapping.yml` — pet
  services, personal coaching, delivery services no longer clutter the
  "Why?" section; walkability_density's SCORE predicate is unchanged.

**Blind-labeling rule** added to `docs/scoring.md §4.1` per owner
instruction: the labeling tool never shows our scores/verdict/reason codes.

## Batch 2 (New York, Singapore) — do NOT start without explicit instruction

Waits on its own go-ahead per the approved plan, even though its stated
precondition (entity-QA taxonomy fix) is now live and tested. When
instructed: `make ingest/score/validate --city new_york,singapore` (bboxes
not yet defined in `cities.yml` — add them first, tightened per the Batch 1
lesson), then extend the golden set with ~8 more hotels (wave 2, per the
approved plan) using the same tool/collection.

## Decisions taken (pointers, not prose)

- 2026-09-06 — **Phase 0bis GO** (owner: Jean; `rapport-decision-phase-0bis.md`).
  ADR-001…005 drafted. Phase 1 pipeline built (`src/hotelareascore/`,
  Python+DuckDB; release discovery, fail-closed schema check, dedupe, the 6
  v1 dimensions via a per-city equirectangular projection). Full run: 4,463
  London + 7,558 Bangkok hotels, €0 cost — **report accepted by owner.**
  Phase 2 Astro site built (`web/`, static-first, `webdata.py` bridges ETL
  → build-time JSON; result page in the strategy.md §2 order; map/CTA
  disabled placeholders, flags off).
- 2026-09-06 — **Owner code audit before Phase 2 close** found a real
  `transit_access` bug: DuckDB's `least()`/`greatest()` skip NULL args
  instead of propagating them, so a hotel with zero transit POIs scored 100
  instead of 0. Fixed (coalesce before `least()`); regression tests added
  (`tests/test_scoring_poi_invariant.py`). **`score_version` → `1.0.1`**
  (docs/scoring.md §5, minor) — 414 London / 1,960 Bangkok hotels moved,
  each exactly −20 balanced-score points
  ([diff report](reports/score-diff-1.0.0-proof-to-1.0.1.md)). Also fixed:
  self-contradictory verdicts (excluded `nightlife_access` from verdict
  lead-clauses — strategy.md §2); scoring.md §3 doc/code drift (density
  formula description corrected to match the code). Documented, not tuned:
  quietness's nearest-only nightlife penalty, flagged for the Phase 3
  sensitivity pass (§4.3). Inspection sheet + `docs/reports/inspection-18.json`
  regenerated under `1.0.1`.
- 2026-09-06 — **Phase 2 gate closed by owner**; Phase 3 plan researched
  (10 candidate cities, real Overture queries, no ingestion) and presented
  ([plan](reports/phase-3-plan.md)).
- 2026-09-06 — **Owner approved the Phase 3 plan** with 3 amendments
  (2-batch ingestion, 2-wave golden set, blind/mobile-first tool). Entity QA
  (a)-(d) implemented (see section above). Batch 1 (8 cities) ingested,
  scored, validated — [ingestion report](reports/phase-3-batch-1-ingestion-report.md).
  Golden-set tool built (`db` capability, blind, mobile-first, keyboard
  shortcuts, shuffled order, "can't judge" skip) and published with 42
  Batch-1 candidates loaded, stratified by score/confidence/chain-vs-
  independent plus 2 deliberate calm-vs-nightlife tension cases (Tokyo). Not
  yet reviewed by owner.
- **Scope decision, not asked to the owner (ordinary engineering):** `web/`
  is NOT wired into CI — its build needs the gitignored, network-fetched ETL
  output, which would make CI slow and non-reproducible across monthly
  Overture releases. Add web CI (fixture-data-based `astro check` + build) as
  its own task before Phase 4 deployment work.

## Blockers / risks being watched

- **AI Overviews (unmeasured):** validation could not observe whether Google
  AI Overviews already answer cluster-2 queries. Mitigation: owner spot-check
  when convenient; mandatory AI-Overview column in the day-90 cohort
  measurement (`docs/seo-policy.md §5`). If AI Overviews cleanly answer the
  majority of tracked cluster-2 queries → execute PIVOT path
  (`docs/validation.md §3`).
- No search-volume data was available in Phase 0bis (SERP composition only);
  treat all traffic projections as unvalidated priors.
- Affiliate program eligibility likely requires a live site with traffic —
  sequencing in `docs/affiliate-matching.md §5`.
- Supabase free-tier fit depends on keeping POIs out of the serving DB —
  `docs/data-and-costs.md §2`.

## Cost tracker (update monthly)

| Month | Est. recurring € | Main driver | Notes |
|---|---:|---|---|
| 2026-09 | 0 | — | validation + Phases 1–3 (Batch 1, 10/12 cities), all free tiers (docs/reports/phase-3-batch-1-ingestion-report.md) |

## Last session summary

- 2026-09-06 — Phase 0bis → Phase 1 → Phase 2 (with an owner code audit that
  fixed a real scoring bug, `score_version 1.0.1`) → **Phase 2 gate closed**.
  Phase 3 plan researched, presented, and **approved with 3 amendments**.
  Entity QA (a)-(d) implemented and tested against real data (3 iterations
  to get item (a)'s heuristic safe — see "Entity QA" section above for the
  false-positive history, worth reading before trusting it further). Batch 1
  (Paris, Rome, Barcelona, Amsterdam, Lisbon, Sydney, Tokyo, Dubai) ingested,
  scored, validated — real volumetry (~115 MB / 10 cities) landed within 6%
  of the plan's estimate. Golden-set labeling tool built and published: 42
  hotels, blind (no scores/verdicts shown), mobile-first, keyboard
  shortcuts, auto-resume via the `db` capability. **Batch 2 (New York,
  Singapore) intentionally not started** — waits for its own go-ahead.
  Next: owner works through the 42-hotel labeling tool; on completion (or
  alongside it), decide on Batch 2's go-ahead.
