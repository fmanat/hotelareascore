# CLAUDE.md — HotelAreaScore (operating rules)

> Brand: **StayContext**, staycontext.com — decided 2026-09-07, `docs/adr/012`.
> `HotelAreaScore`/`hotelareascore` remains the internal code name only (repo
> name, Python package `src/hotelareascore/`, this file's own title) — never
> change that to match the brand. Launch language: English.
> Owner budget: ≤ €200 setup, ≤ €50/month before meaningful revenue (target ≤ €35 steady-state, rest is reserve).
> This file contains ONLY operating rules. Strategy, scoring, SEO policy, data
> architecture and validation live in `docs/`. Read them when the task touches them.

## 0. Session protocol

1. Read `docs/STATE.md` first. It says what phase we are in, what is decided,
   and what is blocked. Update it at the end of any session that changes state.
2. Read the doc relevant to your task before changing anything in its domain:
   - product/business/phases → `docs/strategy.md`
   - demand validation & revenue model → `docs/validation.md`
   - indexing, sitemaps, canonicals, page types → `docs/seo-policy.md`
   - score formulas, weights, calibration → `docs/scoring.md`
   - data sources, volumetrics, serving vs ETL split, cost limits → `docs/data-and-costs.md`
   - affiliate deep links & hotel entity matching → `docs/affiliate-matching.md`
   - past decisions → `docs/adr/`
3. Prefer the smallest reversible change that advances the current milestone.
4. Record any decision with lasting consequences as an ADR.

## 1. Priority order when trade-offs conflict

**User usefulness > data truth > SEO safety > simplicity > operating cost >
implementation elegance > page count.**

## 2. Hard rules (never violate)

1. Never introduce a paid dependency without documenting: why, monthly cost now,
   monthly cost at 10,000 visits/day, and a cheaper fallback.
2. Never create new indexable URLs merely because they can be generated.
   Indexability is a decision recorded in `page_publication`, never a side
   effect of a route existing.
3. Never publish factual AI-written claims not grounded in structured project
   data or a cited source.
4. Never call an external geospatial API per page view if the result can be
   precomputed, cached, or served from our own database.
5. Never change a scoring formula silently. Scores are versioned
   (`score_version`), changes go through the golden-set regression
   (`docs/scoring.md §5`).
6. Never fake freshness: `dateModified` changes only on material data or
   analysis change (see change-detection thresholds in `docs/data-and-costs.md`).
7. No dark patterns, fake reviews, fake ratings, fabricated testimonials,
   artificial scarcity.
8. Never expose secrets (Supabase service-role key, affiliate keys). Server-side
   only, via Cloudflare/GitHub secrets. RLS on any client-accessible table.
9. Affiliate links always carry `rel="sponsored"` (optionally `nofollow`).
   Affiliate relationships never influence scores.
10. Fail closed: if an upstream schema changes unexpectedly or data QA fails,
    do not publish scores or pages from that run.

## 3. Refuse and flag

Refuse, and explain why, any request that would: mass-generate near-duplicate
SEO pages; scrape/paraphrase hotel reviews or descriptions; cloak; hide
text/links; create doorway pages; fake timestamps, expert bios, first-hand
experiences or ratings; run paid link schemes; publish mass auto-translations;
or violate a data-source license. The correct alternative is always better
data, better tools, or fewer stronger pages.

## 4. Owner decision boundary

Do NOT ask the owner about ordinary engineering choices already settled in
`docs/` or ADRs. DO ask (with a short decision report: decision required / why /
evidence / cost / expected upside / recommendation) when a choice materially
affects: brand/domain; legal or commercial commitments; paid spend beyond the
documented budget; affiliate contract terms; major positioning; publication of
potentially reputational research; or any Phase 0bis kill-criterion outcome
(`docs/validation.md`).

## 5. Stack (decided — see ADRs for rationale)

- Web: Astro + TypeScript, static-first, minimal client JS, React islands only
  where needed. Do not migrate frameworks without an ADR.
- Hosting: Cloudflare Pages/Workers (+ R2 for snapshots/PMTiles). Start free.
- Serving DB: Supabase Postgres + PostGIS — **serving tables only** (hotels,
  metrics, scores, baselines, publication, events). Heavy geospatial stays in
  the offline ETL (DuckDB + Parquet in R2), never in Supabase. See
  `docs/data-and-costs.md §2` — this is what keeps us on the free tier.
- ETL: Python + DuckDB + Overture CLI, scheduled via GitHub Actions.
- Maps: MapLibre GL JS; OpenFreeMap (or equivalent) behind a provider
  abstraction at launch; Protomaps/PMTiles + R2 as the scale fallback. Lazy-load
  maps; never let map serving become the dominant cost.
- Primary data: Overture Maps monthly releases, discovered via
  catalog/STAC — never hardcode a release path. Schema adapters mandatory.
- Analytics: Cloudflare Web Analytics + first-party events. No accounts, no
  unnecessary cookies in MVP.

## 6. Runtime budget

A hotel lookup at runtime = one search query + one score/result query
(+ optional compare query). No LLM, no Overture, no Overpass, no remote POI or
geocoding call on the page-view path. Cache key for results:
`hotel_id + score_version + source_release`.

## 7. AI usage

Claude is for: coding, architecture, anomaly diagnosis, taxonomy edge cases,
short explanations generated from structured score facts, SEO title/meta
experiments, QA, PRs for owner review.
Claude is NOT a content factory: no invented hotel facts, no generic
destination filler, no "best hotels" listicles, no prose detached from data.
Prefer deterministic reason-code templates; LLM copy only at build time, only
on changed/high-value pages, always generated from a structured facts payload.

## 8. Automation defaults

- Structural SEO changes: output a PR or report, never auto-publish.
- Monthly data bot, weekly ops/SEO bots, cost bot per `docs/strategy.md §7`.
- Feature flags default OFF for new/dangerous behavior:
  `PUBLIC_INDEXING_ENABLED, HOTEL_PAGE_INDEXING_ENABLED, AFFILIATE_ENABLED,
  AI_SUMMARIES_ENABLED, MISSING_HOTEL_GEOCODING_ENABLED, MAP_ENABLED,
  DATA_REFRESH_ENABLED, SEO_AUTOMATION_ENABLED`.

## 9. Testing gates (CI must stay green)

Unit (taxonomy, decay, normalization, persona weights, bounds, slugs) · data
tests (valid coords, no impossible counts, no duplicate canonicals, baselines
present, versions recorded) · integration (sample ingest, migrations, score
generation) · E2E (search → result → persona → compare, mobile, noindex rules,
affiliate rel) · SEO build-time assertions (unique titles, one canonical,
robots, sitemap ⊇ indexable ∧ ∌ noindex, hreflang reciprocity, JSON-LD parses)
· golden-set regression on any scoring change.

## 10. Current milestone

See `docs/STATE.md`. Do not start work belonging to a later phase without an
explicit owner instruction or a passed gate recorded in STATE.md.
