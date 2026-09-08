# Hotel pages architecture options — 12-city static file budget

- **Date:** 2026-09-07 (night mission #2, Bloc A)
- **Context:** `docs/STATE.md` flagged that `web/src/lib/data.ts` hardcodes
  only 2 of 12 launch cities (`hotels-london.json`, `hotels-bangkok.json`),
  a Phase 2 leftover. The pilot cohort (`docs/reports/pilot-cohort-proposal.md`)
  spans all 12 cities and `compute_publication.py` correctly marks ~200
  hotels indexable everywhere, but 10 cities' indexable hotels have no
  built page today. Before fixing this, we need to know whether "build a
  real page for every hotel in all 12 cities" is even possible inside
  Cloudflare Pages' own limits.

## 1. Cloudflare limits (verified, sourced 2026-09-07)

| Limit | Value | Source |
|---|---|---|
| Files per deployment, **Free plan** | **20,000** | [Cloudflare Pages limits](https://developers.cloudflare.com/pages/platform/limits/) |
| Files per deployment, **paid plans** | 100,000 (requires `PAGES_WRANGLER_MAJOR_VERSION=4`) | [Changelog, 2026-01-23](https://developers.cloudflare.com/changelog/post/2026-01-23-pages-file-limit-increase/); [Cloudflare Pages limits](https://developers.cloudflare.com/pages/platform/limits/) |
| Max size of a single asset file | 25 MiB | [Cloudflare Pages limits](https://developers.cloudflare.com/pages/platform/limits/) |
| Build timeout | 20 minutes | [Cloudflare Pages limits](https://developers.cloudflare.com/pages/platform/limits/) |
| Total deployment byte size | No explicit cap stated | [Cloudflare Pages limits](https://developers.cloudflare.com/pages/platform/limits/) |

We are on the **Free plan** (`docs/data-and-costs.md` — "start free", no
paid Cloudflare product in the cost tracker). Unlocking the 100,000-file
ceiling requires a **paid Workers/Pages plan** (Cloudflare's paid tier
starts at $5/month) — a new recurring cost and a billing/account change,
which fails this mission's 0€/no-new-service/no-account bar outright, so
it is not evaluated further tonight. Workers Static Assets (the other
platform mentioned in the mission) shares the same Pages deployment
pipeline and the same 20,000-file free-tier ceiling — not a separate,
higher limit.

Average built hotel page today: **~26 KB** (`web/dist/hotel/*/index.html`),
so the 25 MiB per-file cap is irrelevant here by 3 orders of magnitude —
file *count*, not file *size*, is the binding constraint.

## 2. Exact page count vs. the limit

Counted directly from the ETL output (`data/etl/2026-08-19.0/*/hotels.parquet`,
`select count(*)`), not from the mission brief's ~42,700 estimate:

| City | Hotels |
|---|---:|
| bangkok | 7,546 |
| rome | 5,040 |
| london | 4,397 |
| paris | 3,582 |
| tokyo | 2,745 |
| dubai | 2,067 |
| new_york | 2,194 |
| barcelona | 1,720 |
| lisbon | 1,289 |
| singapore | 1,237 |
| sydney | 1,078 |
| amsterdam | 1,071 |
| **Total** | **33,966** |

> **Discrepancy flagged, not silently corrected:** the mission brief says
> "~42,700 hôtels". The real, live count from the current data release
> (`2026-08-19.0`, confirmed still latest as of 2026-09-07,
> `docs/STATE.md`) is **33,966** — matching `docs/STATE.md`'s own cost
> tracker ("33,970 hotels", rounded). Every calculation below uses the
> real 33,966, not the brief's figure. If ~42,700 refers to a pre-entity-QA
> or pre-dedupe raw count from an earlier session, that's a data-provenance
> question for the owner, not something to guess at here.

Plus non-hotel files: 12 city pages, ~15 static/legal/home/compare/
methodology pages, `robots.txt`, favicons, `_astro/*` build assets (4
today), and `data/search-index.json` (1 file). Call this **~50 files** of
fixed overhead, generously rounded.

**Current state (2 of 12 cities built):** 11,943 hotel pages + 27 other
files = 11,970 total (`find web/dist -type f | wc -l`) — 60% of the
20,000-file free-tier ceiling, for 1/6th of the launch cities.

**Full 12-city, one-page-per-hotel:** 33,966 + ~50 ≈ **34,016 files** —
**70% over** the 20,000-file free-tier ceiling. Not close; no rounding or
trimming of the ~50-file overhead changes the conclusion.

## 3. Options

### (a) Tout-statique (one real page per hotel, all 12 cities)

Build every one of the 33,966 hotels as a static page, same as today's
London/Bangkok pattern.

- **Files:** ~34,016 — needs the **paid** 100,000-file ceiling.
- **Cost:** requires upgrading to a paid Cloudflare plan (≥$5/month) —
  the first paid infra cost this project would take on, before any
  revenue and before the pilot-cohort review has even happened
  (`docs/STATE.md` open decision (b)). At 10,000 visits/day this is still
  a flat plan cost, not a variable one (Cloudflare Pages doesn't meter by
  request within the plan), so it doesn't scale with traffic — but it *is*
  a new standing subscription, a new billing relationship, and (per
  Cloudflare's docs) requires opting into a wrangler major-version
  environment variable, i.e. a platform-config change, not just a bigger
  invoice.
- **Verdict:** fails the mission's 0€/no-new-service/no-account bar.
  **Not evaluated as tonight's action; owner call in the morning if ever
  wanted** (CLAUDE.md hard rule 1: paid dependency needs cost-now,
  cost-at-10k/day, cheaper-fallback documented — this report is that
  documentation, should the owner want to revisit).

### (b) Sous-ensemble statique + longue traîne dynamique (Supabase-backed)

Build full static pages for a curated subset; serve the rest on-demand
from Supabase Postgres (already ADR-002's eventual serving world) via a
Cloudflare Pages Function or Worker.

- **Files:** bounded by the static subset only — trivially under any
  free-tier ceiling.
- **Cost:** Supabase free tier can hold this (`docs/data-and-costs.md §2`
  already reserves the serving tables for exactly this kind of data); a
  Pages Function against Supabase Free is $0 at these volumes. Genuinely
  the cleanest long-term architecture — full per-hotel content, no
  "second-class" page type, real SSR freshness.
- **Blocker:** the serving database (`hotels`, `metrics`, `scores`,
  `page_publication` in Postgres/PostGIS, per `docs/data-and-costs.md §2`)
  **is not provisioned yet** — `docs/STATE.md` confirms `page_publication`
  today is still the local SQLite stand-in
  (`src/hotelareascore/publication.py`), explicitly because "Supabase
  isn't provisioned yet." Standing up Supabase means creating an account
  and a new external service mid-mission.
- **Verdict:** explicitly excluded by tonight's mission order ("nécessite
  la base de service — PAS cette nuit") and independently fails the
  no-new-account rule. **Report only — this is the right Phase 5+ answer,
  not a tonight answer.**

### (c) Sous-ensemble statique + longue traîne cherchable, fiche "données limitées" côté client

Build full static pages for a curated subset (as in (b)), but for every
hotel *outside* that subset, keep it 100% searchable and clickable: the
search box and "similar-scoring hotels" links resolve to a single shared,
always-noindex client-rendered page that hydrates a lightweight card
(name, city, locality, the 6 dimension scores, balanced score, confidence
label, verdict — all fields already computed and already shipped in
`search-index.json` today) from the same search index already fetched for
autocomplete. No second file per hotel; the "page" is one shared static
route plus client-side JS reading data already in memory.

- **Files:** the static subset only (city pages + ~50 overhead + N hotel
  pages, N chosen below) — no growth from the long tail at all, because
  the long tail has no per-hotel file.
- **Cost:** $0. No new service (reuses `search-index.json`, already built
  and already fetched by `SearchBox.astro`/`ComparePicker.astro`/
  `compare.astro`). No new account. Fully reversible — deleting the one
  new route and reverting `data.ts`'s imports undoes it completely.
- **Coverage:** 100% of hotels remain findable via search and via
  "similar-scoring hotels" links; the ones outside the static subset get
  real, sourced data (never fabricated — CLAUDE.md hard rule 3) with an
  honest "limited profile" disclosure instead of a 404 or a thin
  auto-generated page.
- **Trade-off:** the limited-data card has no nearby-facts list, no map,
  no reason codes, no comparable-hotels list — it's intentionally
  thinner than a full hotel page, and is never eligible for indexing (by
  design, independent of `PUBLIC_INDEXING_ENABLED`/
  `HOTEL_PAGE_INDEXING_ENABLED` — see the ADR).
- **Verdict:** meets all four pre-authorization conditions (0€, no new
  service, no new account, reversible) and keeps 100% of hotels
  searchable. **Implemented tonight — see `docs/adr/013`.**

## 4. Static-subset budget (option c)

Free-tier ceiling 20,000 files, with the mission's required 20% margin:
usable budget = 20,000 × 0.8 = **16,000 files**. Reserving ~100 files for
city/static/legal pages and future growth headroom leaves
**15,900 files for static hotel pages** — see `docs/adr/013` for the exact
selection algorithm (pilot cohort ∪ one-hop comparable-hotel links ∪
per-city fill ranked by confidence and distinctiveness from the city
median). This uses 47% of the 33,966 hotels for full pages while staying
21% under even the unmargined 20,000-file ceiling.

## 5. Recommendation

Tonight: implement (c). Revisit (a) only if the owner decides the paid
Cloudflare tier is worth it for a specific reason (e.g. before the paid
Cloudflare tier makes sense, the real fix is (b) — a Supabase-backed
long tail — once Phase 5 stands up the serving database anyway; paying
Cloudflare for more static files without addressing the underlying
"33,966 discrete pieces of content" scale problem just delays the same
decision at a worse price point (Cloudflare's paid plan cost, with no
added product value over what (b) already gives for free at Supabase's
free tier).
