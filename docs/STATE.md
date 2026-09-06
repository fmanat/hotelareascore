# STATE.md — project state tracker

> Claude Code: read this first every session; update it whenever phase,
> decisions, or blockers change. Keep it under ~150 lines — this is a
> dashboard, not a journal. Move resolved history to `docs/adr/` or delete it.

## Current phase

**Phase 3 — launch dataset (~12 cities), golden set, calibration** (see
`docs/strategy.md §5`). Plan presented to owner for approval BEFORE any
ingestion — see [`docs/reports/phase-3-plan.md`](reports/phase-3-plan.md).
Do not run `make ingest` for any new city until that plan is approved.

Phase 2 (product proof) gate: **✅ closed 2026-09-06** — owner inspected the
(bug-fixed, `score_version 1.0.1`) 18-hotel sheet, machine audit + human
review both conclusive. Phase 1 Data Proof Report:
[`docs/reports/data-proof-report-2026-08-19.0.md`](reports/data-proof-report-2026-08-19.0.md)
— accepted 2026-09-06.

## Phase gate status

| Phase | Gate | Status |
|---|---|---|
| 0 — repo & ADRs | ADR-001…005 merged, CI green | ✅ committed & pushed 2026-09-06 (github.com/fmanat/hotelareascore) |
| 0bis — demand validation | Kill criteria evaluated, owner GO recorded | ✅ **GO recorded 2026-09-06** (see decision log below) |
| 1 — data proof (2 cities) | Data Proof Report accepted by owner | ✅ **accepted 2026-09-06** |
| 2 — product proof | Owner inspected 15–20 hotel outputs | ✅ **closed 2026-09-06** |
| 3 — launch dataset (~12 cities) | Golden set built, calibration done | ▶ current — plan awaiting approval |
| 4 — SEO launch (incl. pilot hotel cohort) | Pilot cohort live, GSC connected | ☐ |
| 5 — commercial test | First affiliate integrated, clicks measured | ☐ |
| 6 — growth automation | Weekly GSC loop producing PRs | ☐ |

## Open owner decisions

- [ ] Domain/brand name (blocking public launch, not blocking Phases 1–2)
- [ ] Legal vehicle & jurisdiction for the site and affiliate revenue
      (`docs/strategy.md §8` — owner homework)

## Bounded pre-Phase-3 task: entity QA (owner-scoped — do NOT start without explicit instruction)

Owner decision 2026-09-06: expanded from "sample the Bangkok `lodging`
bucket" into a 4-part entity-QA task, based on findings in the 18-hotel
audit (`docs/reports/inspection-18.json`). Run this **before** Phase 3 city
expansion, not as part of it, and not automatically.

- **(a) Non-hotels classified as hotels.** Audit examples: "RevenuebyDesign"
  (a consultancy) and "อาคารใยแก้ว True Tower" (an office building) both
  carry a hotel-family taxonomy leaf. Estimate the rate on a sample; propose
  exclusion rules (name-pattern signals, source/category cross-checks) for
  `data/config/taxonomy-mapping.yml`.
- **(b) Name sanity checks in `validate.py`.** Purely numeric names
  (e.g. `"8468671"`) and empty names should be flagged (or hard-failed) as a
  QA anomaly, not silently scored.
- **(c) City bbox scope.** "The Hautboy" is in Ockham, Surrey — ~30 km from
  central London — but is labeled "London." Propose either tightening city
  bboxes (`data/config/cities.yml`) or showing an honest `locality`/distance
  on result pages instead of implying it's "in London."
- **(d) Nearby-facts category filter.** The "Why?" section's `walkability_density`-
  hierarchy match pulls in irrelevant `lifestyle_services` leaves (e.g.
  `life_coach`). Tighten the category filter used for `nearby_facts` display
  (docs/data-and-costs.md §2) separately from the scoring predicate if
  needed — scores and displayed facts don't have to share one filter.

Also still relevant from the original framing: Bangkok's generic
`lodging` leaf (11,024 places, `docs/reports/data-proof-report-2026-08-19.0.md`
"Rejects" section) — fold into (a)'s sampling pass rather than a separate
exercise.

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
- 2026-09-06 — **Phase 2 gate closed by owner** (audit + human review both
  conclusive). Entity-QA findings became the bounded pre-Phase-3 task above.
  Phase 3 opened: researched all 10 remaining launch-city candidates with
  real Overture queries (no ingestion) — found New York and Singapore share
  Bangkok's generic-`lodging` data-quality problem. Full plan at
  [`docs/reports/phase-3-plan.md`](reports/phase-3-plan.md), awaiting
  approval.
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
| 2026-09 | 0 | — | validation + Phases 1–2 + Phase 3 city research, all free tiers (docs/reports/phase-3-plan.md §5) |

## Last session summary

- 2026-09-06 — Phase 0bis GO → Phase 1 pipeline + accepted Data Proof Report
  → Phase 2 Astro site, owner-audit bug fixes (`score_version 1.0.1`) →
  **Phase 2 gate closed by owner**. Entity-QA findings from that audit
  expanded into the bounded pre-Phase-3 task (STATE.md above) — not started.
  Phase 3 opened: researched all 10 remaining provisional launch cities with
  real (read-only, no ingestion) Overture queries — found the same
  generic-`lodging` data-quality problem in New York and Singapore that
  Bangkok had, informing a two-batch ingestion sequence. Full plan,
  volumetric/cost estimate, and golden-set labeling protocol presented in
  [`docs/reports/phase-3-plan.md`](reports/phase-3-plan.md) for owner
  approval — **no city has been ingested yet.** Next: owner reviews and
  approves (or amends) the plan; on approval, run the entity-QA task first,
  then Batch 1 ingestion.
