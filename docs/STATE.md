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
      [pilot-cohort-proposal.md](reports/pilot-cohort-proposal.md). A
      12-hotel inspection pack is ready to support this review — full
      published-page fiche, 11 gates, and selection reasoning per hotel,
      including 2 flagged as most discutable (a likely non-hotel
      institution, an ambiguous short-term-rental listing) —
      [cohort-inspection-12.json](reports/cohort-inspection-12.json). **This
      is now the ONLY remaining blocker before go-live** —
      [go-live-seo-checklist.md](reports/go-live-seo-checklist.md) (night
      mission #2 Tache 3) is the exact 6-step sequence from here to the
      90-day clock starting. The package is staged (`page_publication`:
      home/methodology/12 cities/200-cohort all `draft`, re-run via
      `python3 scripts/compute_publication.py`) and dry-run verified —
      [go-live-sitemap-dry-run-report.md](reports/go-live-sitemap-dry-run-report.md):
      all 214 staged URLs resolve to a real built page, 0 consistency
      issues.

Resolved this session, no longer open: family_convenience gate (closed,
`docs/adr/009`); New York/New Jersey market label (`docs/adr/010` — market
renamed "New York City metro", per-hotel disclosure unchanged); legal
vehicle (`docs/adr/011` — FrenchSquare Ltd, an existing English company;
the 4 DRAFT legal templates already name it as publisher/data controller).
Resolved this session (see below): brand & domain (`docs/adr/012` —
StayContext / staycontext.com, owned). Resolved night mission #2, Bloc A:
`web/src/lib/data.ts`'s 2-city hardcoding, and the 10-cities-with-no-built-
hotel-page bug it caused — all 12 cities now have real pages for every
indexable hotel, via a static-subset + client-rendered-long-tail
architecture (`docs/adr/013`, `docs/reports/hotel-pages-architecture-options.md`).
**Night mission #3, Tache 5 note:** the requested ops-bot skeletons
(monthly data-refresh, weekly health/cost) were already fully delivered
an earlier session (commit `6321f9e`, "Bloc F") — verified still correct
and re-ran `cost_bot.py` rather than duplicating the work. The one
documented gap (a per-release score diff step in the monthly workflow) is
still blocked on Supabase not being provisioned, unchanged from when that
gap was first written down.

## Entity QA — known limitations (not blockers, tracked for a future pass)

Full detail in `docs/reports/phase-3-batch-1-ingestion-report.md` and
`tests/golden/LABELS-PROVENANCE.md` §"Data-quality specimens". Summary:

- **English-market-only name filter** (`entity_qa.py`): near-zero recall on
  CJK/Arabic/etc. non-hotel names. Original 2 specimens (Tokyo liquor shop
  + bathhouse), `xfail`-tested. **6 more found in the pilot-cohort v1 audit
  (2026-09-07)**, all non-Latin-script non-hotels: `a995410c…` an
  archaeological site, `dd23804b…` a sake shop, `7c60ea93…` a share house
  (all Tokyo); `02f2535f…` a boat pier, `c4ce64a3…` a housing estate,
  `6679c755…` a university residence complex (all Bangkok) — full names in
  `docs/reports/destination-name-mismatch-audit.md`. All 8 now excluded
  from pilot-cohort candidacy by gate 12 (Latin-script name,
  `docs/seo-policy.md §2`), but remain in the full dataset as "hotels" —
  gate 12 is a cohort-eligibility rule, not an entity-QA fix; the
  still-unattempted language-specific marker list is the real fix.
- **Brand-allowlist short-circuit**: ~33 hotel sub-venues (restaurant/spa/
  parking sharing a parent brand name) pass through across all 12 cities;
  one additional case (Souq Madinat Jumeirah) confirmed not caught because
  "Jumeirah" hits the allowlist first.
- **Corporate-entity records**: at least one (`Holiday Inn Paris CDG
  S.A.R.L.`, pin ~25 km from the airport at Porte de Charenton) looks like
  a legal-entity record, not a bookable property.
- **Numeric-name records — RESOLVED 2026-09-09 (`docs/adr/014`):** 9
  hotels with a purely-numeric `name` (Overture reference number, not a
  real name) — slug fix (`hotel-` prefix) plus a hard, structural
  indexability gate now enforced in `publication.set_status()` (raises
  rather than allowing `'indexable'`) and re-checked in `webdata.py`'s
  export as a second layer. No longer an open question.
- **Bad-geocode records — fixed, not just logged (2026-09-07 owner
  audit):** 4 real hotels whose own `address_freeform` contradicted their
  extraction city (a Bora Bora resort and a Fiji resort both in the
  "Sydney" extract; a Bali villa in "London"; a Bali hotel whose name and
  address disagreed, in "Singapore") — found via a systematic
  destination-name search, verified per-record before exclusion, not
  guessed from the name alone. Now excluded from their cities' datasets
  entirely via `entity_qa.KNOWN_BAD_GEOCODE`, re-ingested. Full triage
  (including same-pattern hits checked and NOT excluded — Tokyo's "Petit
  Bali" love-hotel naming convention, Lisbon's "Pensão Nova Goa", etc. —
  for insufficient evidence of an actual mismatch) in
  [destination-name-mismatch-audit.md](reports/destination-name-mismatch-audit.md).

## Phase 4 commitment: `search_events` as the coverage KPI

No automatic "rejected lodging" rescue rule will be built off blind
sampling (owner decision, 2026-09-06,
`docs/reports/phase-3-coverage-bangkok-nyc.md`). Once the live site is up,
`search_events` (searches with no matching hotel) becomes the per-city
coverage KPI; a rescue rule gets reconsidered only against real demand
data from that metric. Whoever picks up Phase 4: wire this in from the
start.

## Blockers / risks being watched

- **Cloudflare Pages platform incident, INTERMITTENT, ongoing since
  ~08:00 UTC 2026-09-09** (their platform, not us — the owner's own
  Cloudflare support draft confirms every Pages project on the account,
  including a brand-new throwaway one, 503s on its own `*.pages.dev` URL,
  which rules out zone/DNS/custom-domain config). Not the repo: a clean
  `git clone` + `npm ci` + `npm run build` from the committed snapshot
  succeeds every time this has been checked. **The production Cloudflare
  Pages project is named `staycontext`** — an older project,
  `hotelareascorec`, is dead/unused; do not delete it, just don't confuse
  it for prod (no reference to it exists in this repo either way). Seen
  so far: sustained 521 for the ~24h up to 2026-09-09 09:00 UTC, then
  200 on every check since — but per the incident's own description
  ("intermittent"), do not treat a period of 200s as resolved. A
  continuous background probe (`scripts/prod_probe.py` +
  `prod_probe_loop.sh`, every 30s against home/a nonexistent path/
  sitemap-static.xml/the `.pages.dev` URL) is running for the rest of
  night mission #3 — raw log and hourly up/down summary in
  `docs/reports/incident-2026-09-09-cloudflare-pages/`, the evidence for
  the support ticket.
  **Two anomalies found while the site was briefly reachable, NEITHER
  confirmed yet — both marked "re-measure once the probe shows ≥30
  continuous minutes of 200s", not acted on**: (1) `_headers`
  (HSTS/CSP-Report-Only/Permissions-Policy) present on
  `staycontext.pages.dev` but missing on `staycontext.com` itself in one
  check; (2) a nonsense path and the sitemap endpoints returned 200 with
  the home page's HTML instead of 404 in one check (custom `404.astro`
  never served) — looked like a Cloudflare Pages "serve index.html for
  unmatched routes" (SPA-fallback) setting, but a LATER check on the same
  URLs correctly returned 404, so this may just be more of the same
  platform instability rather than a real project-config bug. Do not
  trust either finding until re-measured on a stable window
  (`docs/reports/incident-2026-09-09-cloudflare-pages/` records the
  re-measurement once it happens).
- **Data freshness (checked 2026-09-07):** `2026-08-19.0` is still
  Overture's latest release (live catalog check, not cached) — no
  re-ingestion needed. Re-check next time rather than assuming still true.
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
- **Night mission #2, Bloc B was cut off mid-instruction** ("CSP en
  Report-Only d'abord av...") — implemented what was unambiguous
  (`web/public/_headers`: HSTS w/o `preload` — deliberately, that's a
  harder-to-reverse commitment than one truncated line should authorize —
  X-Content-Type-Options, Referrer-Policy, a minimal Permissions-Policy,
  and CSP in Report-Only mode with no `report-uri` since wiring one needs
  a new service). Whatever came after "av" in the original order is
  unknown — re-issue Bloc B in full if there was more to it.

## Cost tracker (update monthly)

| Month | Est. recurring € | Main driver | Notes |
|---|---:|---|---|
| 2026-09 | 0 | - | 33,966 hotels, 185 MB ETL output, all free tiers |

## Decision & session history

Full narrative history lives in `docs/adr/001` through `013` (each records
context/decision/consequences) and the dated reports under `docs/reports/`
they reference. Batch ingestion, golden-set construction, and calibration
runs are documented in `docs/reports/phase-3-*` and
`docs/reports/score-diff-*`. This file tracks only current state — see git
log and the ADR index for anything not summarized above.
