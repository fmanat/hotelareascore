# STATE.md — project state tracker

> Claude Code: read this first every session; update it whenever phase,
> decisions, or blockers change. Keep it under ~150 lines — this is a
> dashboard, not a journal. Move resolved history to `docs/adr/` or the
> dated report it already lives in; don't re-narrate it here.

## Current phase

**Phase 3 — launch dataset (~12 cities), golden set, calibration —
CLOSED 2026-09-07.** All 12 cities ingested/scored/validated on
`score_version` **1.2.1**. Final dimension status:
- Transit, restaurants, nightlife: pass (Spearman 0.77-0.83), frozen.
- Quietness and family_convenience: both closed as **documented
  thin-to-moderate proxies**, not robustly validated dimensions —
  `/methodology` and `docs/scoring.md §4.3` state this explicitly.
  family_convenience's last iteration (`docs/adr/009`): Spearman 0.5052
  against `tests/golden/family_strict.csv`, a 0.005 margin above the
  owner's 0.5 bar, with per-city Spearman still ranging −0.632 to +1.0
  (3-5 hotels/city). No further tuning without an explicit new review.

Golden-set labels are Claude-produced, not owner-verified
(`tests/golden/LABELS-PROVENANCE.md`) — read every calibration number with
that caveat. Phase 4 SEO-launch machinery (`docs/adr/008`) was built ahead
of time and stays fully inert (flags off) — see open decisions below.

## Phase gate status

| Phase | Gate | Status |
|---|---|---|
| 0 — repo & ADRs | ADR-001…005 merged, CI green | ✅ 2026-09-06 |
| 0bis — demand validation | Kill criteria evaluated, owner GO | ✅ GO 2026-09-06 |
| 1 — data proof (2 cities) | Data Proof Report accepted | ✅ 2026-09-06 |
| 2 — product proof | Owner inspected 15–20 hotel outputs | ✅ 2026-09-06 |
| 3 — launch dataset (~12 cities) | Golden set + calibration | ✅ **closed 2026-09-07** (`docs/adr/009`) |
| 4 — SEO launch (incl. pilot cohort) | Pilot cohort live, GSC connected | ▶ machinery ready (`docs/adr/008`), all flags OFF — blocked on decisions below |
| 5 — commercial test | First affiliate integrated, clicks measured | ☐ |
| 6 — growth automation | Weekly GSC loop producing PRs | ☐ |

## Open owner decisions (blocking Phase 4, nothing else)

- [ ] **(a) Legal placeholders on the 4 legal pages** (`/legal-notice`,
      `/privacy`, `/affiliate-disclosure`, `/terms`) — publisher is settled
      (FrenchSquare Ltd, `docs/adr/011`) but Companies House number,
      registered office address, contact email, "last updated" dates, and
      `/terms`'s governing-law line are still owner-provided placeholders,
      not technical work
- [ ] **(b) Pilot cohort review**: sanity-check a sample of the 200
      proposed hotels before any Phase 4 flag is turned on —
      [pilot-cohort-proposal.md](reports/pilot-cohort-proposal.md)

Resolved this session, no longer open: family_convenience gate (closed,
`docs/adr/009`); New York/New Jersey market label (`docs/adr/010` — market
renamed "New York City metro", per-hotel disclosure unchanged); legal
vehicle (`docs/adr/011` — FrenchSquare Ltd, an existing English company;
the 4 DRAFT legal templates already name it as publisher/data controller).
Resolved this session (see below): brand & domain (`docs/adr/012` —
StayContext / staycontext.com, owned).

## Entity QA — known limitations (not blockers, tracked for a future pass)

Full detail in `docs/reports/phase-3-batch-1-ingestion-report.md` and
`tests/golden/LABELS-PROVENANCE.md` §"Data-quality specimens". Summary:

- **English-market-only name filter** (`entity_qa.py`): near-zero recall on
  CJK/Arabic/etc. non-hotel names. Two known live specimens (a Tokyo
  liquor shop and bathhouse misclassified as hotels), one with an honest
  `xfail` test (`test_known_limitation_cjk_liquor_shop_not_caught`).
- **Brand-allowlist short-circuit**: ~33 hotel sub-venues (restaurant/spa/
  parking sharing a parent brand name) pass through across all 12 cities;
  one additional case (Souq Madinat Jumeirah) confirmed not caught because
  "Jumeirah" hits the allowlist first.
- **Corporate-entity records**: at least one (`Holiday Inn Paris CDG
  S.A.R.L.`, pin ~25 km from the airport at Porte de Charenton) looks like
  a legal-entity record, not a bookable property.
- **Numeric-name records**: 9 hotels with a purely-numeric `name` (Overture
  reference number, not a real name) — slug fix shipped (`slug.py` prefixes
  `hotel-`); whether a numeric name should be a hard non-indexable gate in
  `page_publication` is still an open publication-policy question, not a
  data bug.

## Phase 4 commitment: `search_events` as the coverage KPI

No automatic "rejected lodging" rescue rule will be built off blind
sampling (owner decision, 2026-09-06,
`docs/reports/phase-3-coverage-bangkok-nyc.md`). Once the live site is up,
`search_events` (searches with no matching hotel) becomes the per-city
coverage KPI; a rescue rule gets reconsidered only against real demand
data from that metric. Whoever picks up Phase 4: wire this in from the
start.

## Blockers / risks being watched

- **AI Overviews (unmeasured):** could not observe whether Google AI
  Overviews already answer cluster-2 queries. Mandatory AI-Overview column
  in the day-90 cohort measurement (`docs/seo-policy.md §5`); if AI
  Overviews cleanly answer most tracked queries → PIVOT path
  (`docs/validation.md §3`).
- No search-volume data (Phase 0bis was SERP-composition-only) — treat all
  traffic projections as unvalidated priors.
- Affiliate program eligibility likely requires a live site with traffic —
  sequencing in `docs/affiliate-matching.md §5`.
- Supabase free-tier fit depends on keeping POIs out of the serving DB —
  `docs/data-and-costs.md §2`.

## Cost tracker (update monthly)

| Month | Est. recurring € | Main driver | Notes |
|---|---:|---|---|
| 2026-09 | 0 | - | 33,970 hotels, ~131 MB ETL output, all free tiers |

## Decision & session history

Full narrative history lives in `docs/adr/001` through `012` (each records
context/decision/consequences) and the dated reports under `docs/reports/`
they reference. Batch ingestion, golden-set construction, and calibration
runs are documented in `docs/reports/phase-3-*` and
`docs/reports/score-diff-*`. This file tracks only current state — see git
log and the ADR index for anything not summarized above.
