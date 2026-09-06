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
labeling tool source committed at `tools/golden-labeler/` (blind,
mobile-first, CSV export, `db`+`downloads` capabilities) with the 42-hotel
selection versioned at `tests/golden/selection.json`; published Artifact
link in chat, not reproduced here. Coverage check
([report](reports/phase-3-coverage-bangkok-nyc.md)) done — recommendation:
Batch 2 acceptable to run as-is. **Batch 2 (New York, Singapore) has NOT
been ingested — still waits for explicit go-ahead.**

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

The **real** precondition was a coverage check, not the entity-QA
exclusion fix (exclusion only removes false hotels from the *included*
set — it says nothing about real hotels missing from the *excluded* set).
Done: [`docs/reports/phase-3-coverage-bangkok-nyc.md`](reports/phase-3-coverage-bangkok-nyc.md)
hand-classified 50 Bangkok + 50 New York rejected-lodging records.
**Recommendation: acceptable to proceed as-is** — the gap (~10-16% of the
rejected bucket looks like real, miscategorized lodging) is the same order
of magnitude already accepted in Phase 1, and the bulk of the rest (46-58%)
is genuine noise a rescue rule would risk pulling in. A follow-up
"generic-lodging inclusion rescue" is scoped in that report as a later,
separately-tested task — not a Batch 2 blocker.

Still waits on its own explicit go-ahead. When instructed:
`make ingest/score/validate --city new_york,singapore` (bboxes not yet
defined in `cities.yml` — add them first, tightened per the Batch 1
lesson), then extend the golden set with ~8 more hotels (wave 2) via
`tests/golden/selection.json` + `tools/golden-labeler/build.py`, republish.

## Decisions taken (pointers, not prose)

- 2026-09-06 — **Phase 0bis GO** (owner: Jean; `rapport-decision-phase-0bis.md`);
  ADR-001…005 drafted; Phase 1 pipeline built and run (4,463 London + 7,558
  Bangkok hotels, €0 cost) — **report accepted**; Phase 2 Astro site built
  (`web/`, static-first). **Owner code audit** then found and fixed a real
  `transit_access` bug (DuckDB `least()` swallowing NULL, scoring 100
  instead of 0 — `score_version` → `1.0.1`, 414/1,960 hotels moved exactly
  −20 pts, [diff report](reports/score-diff-1.0.0-proof-to-1.0.1.md)) plus a
  self-contradictory-verdict bug and a scoring.md doc/code drift — **Phase 2
  gate closed**. Phase 3 plan researched (10 candidates, no ingestion) and
  presented ([plan](reports/phase-3-plan.md)).
- 2026-09-06 — **Owner approved the Phase 3 plan** with 3 amendments
  (2-batch ingestion, 2-wave golden set, blind/mobile-first tool). Entity QA
  (a)-(d) implemented (see section above). Batch 1 (8 cities) ingested,
  scored, validated — [ingestion report](reports/phase-3-batch-1-ingestion-report.md).
  Golden-set tool built (`db` capability, blind, mobile-first, keyboard
  shortcuts, shuffled order, "can't judge" skip) and published with 42
  Batch-1 candidates loaded, stratified by score/confidence/chain-vs-
  independent plus 2 deliberate calm-vs-nightlife tension cases (Tokyo). Not
  yet reviewed by owner.
- 2026-09-06 — **Owner audit round 2** (before labeling starts): (1) tool
  export + source committed — CSV export (`downloads` capability, copy-paste
  fallback), `tools/golden-labeler/` source + `tests/golden/selection.json`
  committed and versioned, Artifact republished with `db`+`downloads`. (2)
  Coverage check (the real Batch 2 precondition, not the entity-QA fix) —
  hand-classified 100 rejected-lodging records (50 Bangkok + 50 New York):
  ~10-16% look like real miscategorized lodging, ~46-58% genuine noise
  (public housing, real-estate agencies, street-address artifacts), rest
  ambiguous. Recommendation: Batch 2 OK to proceed as-is; a rescue rule is a
  scoped follow-up, not a blocker. (3) Logged (not fixed): brand-allowlist
  short-circuit lets 33 hotel sub-venues (restaurant/spa/bar/parking/
  ballroom sharing a parent brand name, e.g. "Royal Princess Dusit
  Restaurant") through across the 10 ingested cities.
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

- 2026-09-06 — Phase 0bis → Phase 1 → Phase 2 (owner audit fixed a real
  scoring bug, `score_version 1.0.1`) → **gate closed**. Phase 3 plan
  approved with 3 amendments. Entity QA (a)-(d) implemented (3 iterations to
  get item (a) safe). Batch 1 (8 cities) ingested/scored/validated — real
  volumetry within 6% of estimate. Golden-set tool built.
- Same day, before labeling started: **owner audit round 2** required (1)
  CSV export + committed tool source (`tools/golden-labeler/`,
  `tests/golden/selection.json`) before any labels could safely leave the
  Artifact, and (2) a coverage check on Bangkok/New York's rejected-lodging
  buckets as the *real* Batch 2 precondition (not the entity-QA fix, which
  only cleans the included set). Both done: tool republished with
  `db`+`downloads`, [coverage report](reports/phase-3-coverage-bangkok-nyc.md)
  recommends Batch 2 is OK to proceed as-is. Also logged: the brand-allowlist
  short-circuit lets ~33 hotel sub-venues through (not fixed).
  **Batch 2 still not started** — waits for explicit go-ahead. Next: owner
  labels via the tool (exports CSV when done, or Claude reads the Artifact's
  `db` directly next session); separately, decide on Batch 2's go-ahead.
