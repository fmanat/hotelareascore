# STATE.md — project state tracker

> Claude Code: read this first every session; update it whenever phase,
> decisions, or blockers change. Keep it under ~150 lines — this is a
> dashboard, not a journal. Move resolved history to `docs/adr/` or delete it.

## Current phase

**Phase 2 — product proof (London + Bangkok)** (see `docs/strategy.md §5`)
Goal: home, autocomplete on our own index, result page (order per
`docs/strategy.md §2`), persona selector, methodology page, on the 2 existing
cities. Static-first Astro build, all feature flags stay OFF, no live
backend/Supabase — build-time data only from the Phase 1 ETL output
(`docs/adr/002` — nothing here touches the serving world). Owner inspects
15–20 hotel outputs to close this phase's gate.

**Built and running (`web/`, 2026-09-06).** 12,021 hotel pages + home +
methodology, `npm run build` in ~20s. All pages ship `noindex, nofollow`
(flags OFF). **Gate NOT closed yet** — an owner code audit found and this
session fixed a real scoring bug (score_version now `1.0.1`, see Decisions
below); a revised 18-hotel inspection sheet is published for owner review
(link in chat; raw data also at
[`docs/reports/inspection-18.json`](reports/inspection-18.json) so it's
checkable without the Artifact link). Awaiting owner sign-off on the
15–20 outputs to close the gate — do not mark Phase 2 done without it.

Phase 1 Data Proof Report: [`docs/reports/data-proof-report-2026-08-19.0.md`](reports/data-proof-report-2026-08-19.0.md) — **accepted by owner 2026-09-06.**

## Phase gate status

| Phase | Gate | Status |
|---|---|---|
| 0 — repo & ADRs | ADR-001…005 merged, CI green | ✅ committed & pushed 2026-09-06 (github.com/fmanat/hotelareascore) |
| 0bis — demand validation | Kill criteria evaluated, owner GO recorded | ✅ **GO recorded 2026-09-06** (see decision log below) |
| 1 — data proof (2 cities) | Data Proof Report accepted by owner | ✅ **accepted 2026-09-06** |
| 2 — product proof | Owner inspected 15–20 hotel outputs | ▶ current |
| 3 — launch dataset (~12 cities) | Golden set built, calibration done | ☐ |
| 4 — SEO launch (incl. pilot hotel cohort) | Pilot cohort live, GSC connected | ☐ |
| 5 — commercial test | First affiliate integrated, clicks measured | ☐ |
| 6 — growth automation | Weekly GSC loop producing PRs | ☐ |

## Open owner decisions

- [ ] Domain/brand name (blocking public launch, not blocking Phases 1–2)
- [ ] Legal vehicle & jurisdiction for the site and affiliate revenue
      (`docs/strategy.md §8` — owner homework)

## Bounded pre-Phase-3 task (owner-scoped — do NOT start without explicit instruction)

- **Sample the Bangkok generic-`lodging` bucket.** Context: 11,024 places in
  the Bangkok bbox carry Overture's generic/unclassified `lodging` taxonomy
  leaf — more than the 7,558 hotels actually scored — vs. only 749 in London
  (`docs/reports/data-proof-report-2026-08-19.0.md`, "Rejects" section).
  Owner decision 2026-09-06: not worth investigating now; do it as a bounded
  task **before Phase 3** city expansion, not now, and not automatically.
  Scope when instructed: pull a random sample of ~50 of these entries, check
  by hand (name + address pattern) whether they look like real bookable
  hotels miscategorized upstream (→ a coverage gap worth fixing before
  scaling to more Asian cities) or genuine noise (directories, homestays,
  private listings out of MVP scope → no action needed). Output: a short
  finding + a recommendation on whether the taxonomy-mapping fallback logic
  needs a rule for this leaf.

## Decisions taken (pointers, not prose)

- 2026-09-06 — **Phase 0bis GO** recorded (owner: Jean). Basis:
  `rapport-decision-phase-0bis.md` — SERPs held by solo blogs/forums, zero
  data-driven incumbents, direct demand evidence (Tripadvisor thread).
  Inflections: (a) city/area pages are the primary SEO center of gravity
  from Phase 4, hotel pilot cohort stays the measured experiment; (b)
  AI Overviews presence check added to cohort measurement. ADR-001…005
  drafted alongside.
- 2026-09-06 — Phase 1 pipeline built (`src/hotelareascore/`, Python +
  DuckDB): release discovery via the bucket's catalog (never hardcoded,
  docs/adr/003), fail-closed schema check, dedupe, the 6 v1 dimensions via a
  per-city equirectangular projection (avoids a London/Bangkok latitude
  bias), Data Proof Report generator. Full run: 4,463 London + 7,558 Bangkok
  hotels, €0 cost. **Report accepted by owner**; Bangkok generic-`lodging`
  finding deferred to the bounded pre-Phase-3 task above. Phase 2 opened.
- 2026-09-06 — Phase 2 site built (`web/`, Astro, static-first, no adapter):
  `src/hotelareascore/webdata.py` bridges the ETL parquet to build-time JSON
  (slugs, verdict sentences, reason codes, nearest-scoring "comparable
  hotels" — new pure functions, unit-tested). Result page follows the exact
  section order in strategy.md §2; persona selector is client-side and only
  reweights presentation, never the stored scores; map/CTA render as
  disabled placeholders (`MAP_ENABLED`/`AFFILIATE_ENABLED` off). Cosmetic,
  non-blocking anomalies noted: some hotel-taxonomy entries are actually a
  restaurant/sub-venue; Thai-script names slugify to generic `hotel-XXXXXXXX`
  URLs (transliteration pass before Phase 3).
- 2026-09-06 — **Owner code audit, before Phase 2 close** — 2 real bugs fixed,
  1 prior documented, 1 doc/code drift corrected:
  1. **`transit_access` bug:** DuckDB's `least()`/`greatest()` skip NULL
     arguments instead of propagating them, so a hotel with zero transit POIs
     in radius scored 100 instead of 0. Fixed in `scoring.py` (coalesce
     `best_mode_score` to 0.0 before the `least()` call); regression tests
     added for the invariant "POI-dimension score > 0 ⇒ poi_count > 0"
     (`tests/test_scoring_poi_invariant.py`, all 6 POI dimensions).
     **`score_version` bumped `1.0.0-proof` → `1.0.1`** (docs/scoring.md §5,
     minor). Re-scored both cities: 414 London / 1,960 Bangkok hotels moved,
     each by exactly −20 balanced-score points (transit weighs 0.20 in the
     balanced persona) — diff report at
     [`docs/reports/score-diff-1.0.0-proof-to-1.0.1.md`](reports/score-diff-1.0.0-proof-to-1.0.1.md).
  2. **Self-contradictory verdicts:** `nightlife_access` could lead the
     verdict sentence ("Excellent for nightlife…") while quietness_proxy
     independently said "quiet surroundings", because the nightlife penalty
     in quietness_proxy only looks at the *nearest* venue. Fixed by excluding
     `nightlife_access` from verdict lead-clause candidates by default
     (strategy.md §2: "positive only for that persona") — structurally
     prevents the contradiction, not just the observed case.
  3. **Documented, not tuned:** the quietness_proxy nightlife penalty ignores
     venue density (nearest-only, capped at 25 pts) — added as the top
     candidate for the Phase 3 sensitivity pass (docs/scoring.md §4.3), with
     the repro case. No constants changed.
  4. **Doc/code drift fixed:** scoring.md §3 said density used
     `log(1+weighted_count)`; the code has always used the saturating curve
     documented in `score-weights.yml`. Doc corrected to match code;
     `/methodology` copy was already consistent, no change needed there.
  webdata + the 18-hotel inspection sheet regenerated under `1.0.1`; raw JSON
  committed at `docs/reports/inspection-18.json`. **Phase 2 gate stays open**
  pending owner review of the corrected sheet.
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
| 2026-09 | 0 | — | validation + scaffold + Phase 1 pipeline run, all free tiers (docs/reports/data-proof-report-2026-08-19.0.md) |

## Last session summary

- 2026-09-06 — Phase 0bis executed; GO recorded; Phase 1 opened and its Data
  Proof Report **accepted by owner**; Phase 2 opened. Astro product-proof
  site built and verified in-browser (12,021 static hotel pages, all
  noindex). Owner code audit then caught a real `transit_access` scoring bug
  and a self-contradictory verdict case (see Decisions above) — both fixed,
  regression-tested, `score_version` bumped to `1.0.1`, both cities re-scored,
  diff report produced, inspection sheet regenerated and its raw data
  committed. **Phase 2 gate is still open** — not yet signed off. Next: owner
  reviews the corrected 15–20 outputs; on sign-off, close Phase 2 and scope
  Phase 3 (the bounded Bangkok `lodging` sampling task runs before that city
  expansion, not as part of it).
