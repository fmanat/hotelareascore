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
(flags OFF). 18-hotel real-data inspection sheet published for owner review —
link in the session's chat transcript (Artifact, not reproduced here since
Artifact links aren't durable repo state). Awaiting owner sign-off on the
15–20 outputs to close the gate.

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
- 2026-09-06 — **Phase 1 Data Proof Report accepted by owner (Jean).** Bangkok
  generic-`lodging` finding acknowledged, explicitly deferred to a bounded
  pre-Phase-3 task (see section above) rather than actioned now. Phase 2
  opened.
- 2026-09-06 — Phase 2 site built (`web/`, Astro, static-first, no adapter):
  `src/hotelareascore/webdata.py` bridges the ETL parquet to build-time JSON
  (slugs, deterministic verdict sentences, reason codes, nearest-scoring
  "comparable hotels" — all new pure functions with unit tests, 52 total now
  green). Result page follows the exact section order in strategy.md §2;
  persona selector is a small client-side script that only reweights
  presentation (never the stored scores); map and CTA sections render as
  disabled placeholders (`MAP_ENABLED`/`AFFILIATE_ENABLED` both off). Two new
  real anomalies surfaced while building (both cosmetic, not scoring bugs):
  (a) a handful of hotel-family taxonomy entries are actually a restaurant/
  sub-venue, not a distinct hotel (e.g. "Royal Princess Dusit Restaurant");
  (b) hotel names with no Latin characters (Thai script) slugify to a
  generic `hotel-XXXXXXXX` URL — fine for this proof, worth a
  transliteration pass before Phase 3.
- **Scope decision, not asked to the owner (ordinary engineering):** `web/`
  is NOT wired into CI. Its build imports the real per-city JSON exported by
  `make webdata`, which needs the (gitignored, network-fetched) Phase 1 ETL
  output — running that on every push would make CI slow, network-dependent
  and non-reproducible as Overture releases roll monthly. Add web CI
  (fixture-data-based `astro check` + build) as its own task before any
  Phase 4 deployment work, not silently bundled into it.

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

- 2026-09-06 — Phase 0bis executed; GO recorded; Phase 1 opened. Phase 1
  pipeline built and run end-to-end (London + Bangkok); Data Proof Report
  generated and **accepted by owner**; Phase 2 opened. Astro product-proof
  site built and verified in-browser (home/autocomplete, result page in the
  strategy.md §2 order, persona selector, methodology) — 12,021 static hotel
  pages, all noindex. Delivered an 18-hotel real-data inspection artifact for
  owner review (diverse: both cities, chain + independent, full confidence
  range). Next: owner reviews the 15–20 outputs; on sign-off, close Phase 2
  and scope Phase 3 (launch dataset, ~12 cities, golden-set calibration) —
  remember the bounded Bangkok `lodging` sampling task above runs before that
  city expansion, not as part of it.
