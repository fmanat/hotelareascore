# ADR-013 — Static-subset hotel pages + client-rendered long tail (12 cities)

- **Status:** accepted
- **Date:** 2026-09-07/08 (night mission #2, Bloc A)
- **Decision recorded from:** night mission order Bloc A; pre-authorization
  conditions in that order; `docs/reports/hotel-pages-architecture-options.md`

## Context

`docs/STATE.md` flagged that `web/src/lib/data.ts` hardcoded only 2 of 12
launch cities (`hotels-london.json`, `hotels-bangkok.json` — a Phase 2
leftover). The pilot cohort spans all 12 cities and `compute_publication.py`
already marks ~200 hotels indexable everywhere, but 10 cities' indexable
hotels had no built page at all, and no route existed for them.

Building a real static page for every one of the 33,966 hotels across 12
cities would need ~34,000 files (`docs/reports/hotel-pages-architecture-options.md`
§2) — 70% over Cloudflare Pages' Free-plan 20,000-file-per-deployment
ceiling. Unlocking the paid 100,000-file tier means a new recurring cost
and a billing/account change, which fails this mission's 0€/no-new-service/
no-account bar. A Supabase-backed dynamic long tail (option b in that
report) is the right eventual architecture but needs the serving database,
which isn't provisioned yet and is explicitly out of scope for tonight.

## Decision

Implement option (c) from the architecture report: build full static pages
for a bounded subset of hotels, and make every other hotel fully
searchable and clickable via a single shared, always-noindex,
client-rendered "limited data" card — no per-hotel file for the long tail
at all, so the file count is independent of total hotel count.

### 1. Static-subset selection (`select_static_subset`, `webdata.py`)

Priority order, computed once across all 12 cities together:

1. **Every indexable hotel** (the recorded `page_publication` decision) —
   non-negotiable; the sitemap must never reference a page that wasn't
   built (CLAUDE.md hard rule 2). Fails closed (raises, doesn't silently
   truncate) if this set alone ever exceeded the budget.
2. **Every hotel one hop away via `comparable`** from an already-included
   hotel — so a full hotel page's "similar-scoring hotels nearby" list
   doesn't route a reader straight into the thin experience. One hop
   only, not a recursive closure, to keep this bounded regardless of the
   comparable graph's shape.
3. **Remaining budget filled per city**, proportional to each city's
   share of all hotels, ranked by confidence then by distinctiveness (a
   hotel's absolute distance from its own city's median balanced score —
   real, already-computed data, never fabricated).

### 2. File budget

Free-tier ceiling 20,000 files, mission-required 20% margin → 16,000
usable. `NON_HOTEL_FILE_RESERVE = 250` covers city/static/legal pages,
build assets, the merged search index, and the 192 sharded search-index
files (§4) — measured at 220, rounded up for headroom.
`STATIC_HOTEL_PAGE_BUDGET = 16,000 − 250 = 15,750`. The actual build
selected **15,749** hotels for static pages (47% of 33,966) and produced
**15,969 total deployed files** — 79.9% of the 20,000 ceiling, comfortably
inside the required margin.

### 3. The "limited data" card (`web/src/pages/hotel/limited.astro`)

One shared static route, `/hotel/limited?slug=...&city=...`, hydrated
client-side from the same `search-index.json` fields SearchBox/
ComparePicker/Compare already fetch (name, locality, the 6 dimension
scores, balanced score, confidence label, verdict) — never a second,
thinner data shape, and never a fabricated fact (CLAUDE.md hard rule 3).
It shows an explicit "Limited profile" disclosure (no nearby facts, map,
or comparable hotels) rather than presenting itself as equivalent to a
full hotel page.

**Always noindex, by design, independent of every flag**: no `indexable`
prop is passed to `BaseLayout`, so `robots` is always `noindex, nofollow`
regardless of `PUBLIC_INDEXING_ENABLED`/`HOTEL_PAGE_INDEXING_ENABLED`.
This is intentionally thin content that should never compete with a real
hotel page in search results — not a page waiting on a flag flip.

A slug that later gains a real static page redirects
(`location.replace`) from `/hotel/limited` to `/hotel/{slug}` rather than
serving duplicate content at two URLs.

### 4. Search-index sharding (perf fix, found during implementation)

First cut: one merged `search-index.json` (~17 MB across all 12 cities).
SearchBox/ComparePicker/Compare fetch it lazily on focus (off the
page-load critical path — no Lighthouse impact, confirmed: home page
still scores 100). But `hotel/limited.astro` fetches it **on page load**
to resolve the one hotel in the URL — measured **Lighthouse performance
37**, LCP 10.5s, TBT 1,600ms. Sharding by city alone (one
`search-index-{city}.json` each) improved this to 74 (Bangkok, the
largest city, is still 4.3 MB) — short of the mission's ≥99 bar.

Fix: shard by **(city, trailing hex digit of the slug)** — `hotel_slug()`
(`slug.py`) always ends in an 8-hex-character id suffix, so a slug's last
character is already a uniform `0-9a-f` digit. 12 cities × 16 buckets =
192 small files (~150–290 KB each), and the client derives its own bucket
from the slug string it already has — no extra data to compute or ship,
no extra round trip. Re-measured: **Lighthouse performance 100** on the
same Bangkok hotel (LCP 0.9s, TBT 0ms). `findHotel()` falls back to the
full merged index if a city param is missing or the shard doesn't contain
the slug (e.g. a stale bookmarked link from before a data refresh moved a
hotel), trading a slower path for correctness rather than a 404.

Spot-checked after the fix: home 100, a real hotel page 100, a city page
99 — all ≥99 as required.

### 5. Linking changes

- `ComparableHotels.astro` takes a `cityId` prop (the current page's own
  city — `_attach_comparable_hotels` only ever picks peers from the same
  city, so this is always correct) and routes each entry to `/hotel/{slug}`
  or `/hotel/limited?slug=...&city=...` based on that entry's
  `has_static_page`.
- `SearchBox.astro`'s `onSelect` does the same routing from
  `search-index.json`'s new `has_static_page`/`city_id` fields.
- `ComparePicker.astro` and `compare.astro` needed no change — the
  Compare page already read hotel data entirely from `search-index.json`
  client-side (pre-existing design, `docs/strategy.md §2` journey B), so
  it already worked for any hotel regardless of static-page status once
  the index covered all 12 cities.
- `city/[id].astro`'s "top by dimension"/"representative hotels" links
  (`_city_page_aggregate`) now check per-hotel static-subset membership
  instead of the old per-city "was this city exported at all" check —
  the same bug class as the `data.ts` one this ADR fixes, just in a
  different template.

### 6. Committed data snapshot

Cloudflare's build step has no ETL pipeline access (`docs/STATE.md`,
commit `5eabef5` "Freeze a data snapshot for tonight's Cloudflare Pages
deploy" — owner decision, `web/.gitignore`'s comment on that commit warns
against silently regenerating/recommitting the frozen 2-city snapshot
without the decision being revisited). This ADR **is** that decision being
revisited, explicitly, by tonight's mission order: extending real pages to
12 cities has no meaning without extending what's actually committed and
built from. `web/.gitignore`'s comment is updated accordingly. The
committed snapshot grows from 2 cities' full hotel sets to 12 cities'
static-subset hotel sets, plus the merged and 192 sharded search-index
files — Cloudflare's build command stays exactly `npm run build`, no
Python, no network fetch, unchanged from the prior decision.

## Consequences

- **Fixes the STATE.md-flagged bug**: every indexable hotel across all 12
  cities now has a real built page and a working sitemap entry (verified
  by `scripts/seo_assertions.py`'s sitemap-vs-recorded-status check, which
  now runs against all 12 cities' data instead of 2).
- 100% of the 33,966 hotels remain searchable and clickable; 47% get a
  full page, 53% get an honest limited-data card instead of a 404 or a
  thin auto-generated page.
- New invariant, tested (`tests/test_webdata_static_subset.py`): every
  indexable hotel is always in the static subset, regardless of how the
  budget or fill-ranking logic changes later. Fails closed (raises) if the
  cohort itself ever exceeded the budget, rather than silently dropping
  pages.
- Reversible: deleting `hotel/limited.astro`, the two `has_static_page`
  routing branches, and reverting `data.ts`'s imports to 2 cities undoes
  this completely; no new external service, no new account, no spend.
- Not done tonight, by design: a Supabase-backed dynamic long tail
  (option b) — the real answer once Phase 5 stands up the serving
  database anyway. Revisit the static-subset budget and selection
  algorithm then; this ADR's mechanism is meant to be replaced, not
  extended indefinitely as hotel count grows.
