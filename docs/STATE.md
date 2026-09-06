# STATE.md — project state tracker

> Claude Code: read this first every session; update it whenever phase,
> decisions, or blockers change. Keep it under ~150 lines — this is a
> dashboard, not a journal. Move resolved history to `docs/adr/` or delete it.

## Current phase

**Phase 1 — data proof (London + Bangkok)** (see `docs/strategy.md §5`)
Goal: full pipeline from Overture release to scores for 2 cities, CLI
(`make ingest/score/validate`), and a Data Proof Report for owner acceptance.
Phase 2+ work is NOT authorized until the report is accepted.

**Pipeline built and run end-to-end on release `2026-08-19.0`.** Report:
[`docs/reports/data-proof-report-2026-08-19.0.md`](reports/data-proof-report-2026-08-19.0.md).
Awaiting owner acceptance to open Phase 2 — see "Open owner decisions" below.

## Phase gate status

| Phase | Gate | Status |
|---|---|---|
| 0 — repo & ADRs | ADR-001…005 merged, CI green | ✅ committed & pushed 2026-09-06 (github.com/fmanat/hotelareascore) |
| 0bis — demand validation | Kill criteria evaluated, owner GO recorded | ✅ **GO recorded 2026-09-06** (see decision log below) |
| 1 — data proof (2 cities) | Data Proof Report accepted by owner | ▶ report ready, awaiting owner acceptance |
| 2 — product proof | Owner inspected 15–20 hotel outputs | ☐ |
| 3 — launch dataset (~12 cities) | Golden set built, calibration done | ☐ |
| 4 — SEO launch (incl. pilot hotel cohort) | Pilot cohort live, GSC connected | ☐ |
| 5 — commercial test | First affiliate integrated, clicks measured | ☐ |
| 6 — growth automation | Weekly GSC loop producing PRs | ☐ |

## Open owner decisions

- [ ] **Accept or reject the Phase 1 Data Proof Report** (see link above) to
      open Phase 2. Recommendation in the report: accept — pipeline runs
      end-to-end, fails closed on schema drift, plausible non-degenerate
      scores in both cities.
- [ ] Not blocking, but flagged in the report: in Bangkok, the generic
      unclassified `lodging` taxonomy leaf (11,024 places) outnumbers every
      scored hotel (7,558) — worth a manual sampling pass before Phase 3
      city expansion to see whether real bookable hotels are hiding in it.
- [ ] Domain/brand name (blocking public launch, not blocking Phases 1–2)
- [ ] Legal vehicle & jurisdiction for the site and affiliate revenue
      (`docs/strategy.md §8` — owner homework)

## Decisions taken (pointers, not prose)

- 2026-09-06 — **Phase 0bis GO** recorded (owner: Jean). Basis:
  `rapport-decision-phase-0bis.md` — city-intent SERPs held by solo blogs,
  hotel-brand SEO content and forums, with zero data-driven incumbents;
  computed-surroundings angle unoccupied (Walk Score = US-centric address
  tool, dead hotel integrations); direct demand evidence (Tripadvisor London
  thread requesting exactly this product). Owner accepted Stage A revenue
  reality (~€124/mo mid-case) and time budget (validation.md §2.5).
  Inflections adopted with the GO: (a) city/area pages are the primary SEO
  center of gravity from Phase 4; hotel pilot cohort remains the measured
  experiment; (b) AI Overviews presence check added to cohort measurement.
- ADR-001…005 drafted (stack, ETL/serving split, Overture, score versioning,
  indexability/pilot cohort) — pending first commit.
- 2026-09-06 — Phase 1 pipeline built: `src/hotelareascore/` (Python +
  DuckDB), release discovery via the bucket's own `release/` catalog listing
  (never hardcoded, docs/adr/003), fail-closed schema check, per-city bbox
  extraction, dedupe (normalized name + ≤25m proximity, never merges distinct
  chain branches), the 6 v1 scoring dimensions (docs/scoring.md §2) computed
  via a per-city equirectangular projection — chosen over Web Mercator
  specifically to avoid a London/Bangkok latitude bias in proximity math —
  and a Data Proof Report generator (`make report`). 33 unit tests green.
  Full run on release `2026-08-19.0`: 4,463 London + 7,558 Bangkok hotels
  scored, €0 marginal cost.

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
| 2026-09 | 0 | — | validation + scaffold + Phase 1 pipeline run, all free tiers (docs/reports/data-proof-report-2026-08-19.0.md) |

## Last session summary

- 2026-09-06 — Phase 0bis executed (SERP sampling via web search, competitor
  scan); GO recorded; Phase 1 opened.
- 2026-09-06 — Phase 1 pipeline built and run end-to-end on release
  `2026-08-19.0` (London + Bangkok). Data Proof Report generated; awaiting
  owner acceptance to open Phase 2. Next: owner reviews the report; on
  accept, start Phase 2 (home/autocomplete/result/persona pages on these 2
  cities).
