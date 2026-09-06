# data-and-costs.md — data architecture, volumetrics, free-tier fit

> Supersedes §11–13, 17–18, 28–29, 46, 49–50 of the original. Adds the
> volumetric math the original skipped, and the architectural rule that makes
> the €50/month target credible: POIs never live in the serving database.

## 1. Sources

- **Primary: Overture Maps** — global GeoParquet, bbox extraction, monthly
  releases discovered via catalog/STAC (never hardcoded). Schema evolves
  (older `categories` deprecated 2026 → code against current taxonomy fields,
  keep schema-version adapters, fail closed on unexpected schema).
- Secondary (each needs: license check, attribution, provenance, refresh
  policy, normalized schema): OSM-derived data, Wikidata, official open data,
  GTFS, airport datasets, affiliate hotel metadata.
- Never make live traffic depend on public OSM infra (nominatim, public
  Overpass, community tiles). Own DB + provider abstraction + cached fallback.
- Theme-level license metadata kept (some Overture themes carry ODbL
  obligations).

## 2. THE architectural rule: split ETL world from serving world

**ETL world (offline — DuckDB + Parquet snapshots in R2/local):**
raw Overture extracts, full POI tables, transport segments, dedupe workspace.
Size here is irrelevant to Supabase.

**Serving world (Supabase Postgres + PostGIS):** only what a page view needs:
`cities, hotels, hotel_metrics, hotel_scores, city_score_baselines,
page_publication, hotel_affiliate_links, source_runs, search_events,
outbound_clicks` — plus a SMALL `nearby_facts` table (top-N precomputed
nearby POIs per hotel, for the "Why?" section and mini-map pins), NOT the full
`places` table.

### Volumetric estimate (12 cities, order of magnitude)

| Table | Rows | Est. size w/ indexes |
|---|---:|---:|
| hotels (~1–6k/city) | ~40k | ~30 MB |
| hotel_metrics | ~40k | ~40 MB |
| hotel_scores (× versions) | ~80k | ~30 MB |
| nearby_facts (~30/hotel) | ~1.2M | ~150 MB |
| baselines, publication, runs, links | small | ~15 MB |
| events (rolling, pruned) | rolling | ~20 MB |
| **Total serving** | | **~285 MB** |

Fits Supabase Free (500 MB) with headroom. The full `places` table
(~50–150k filtered POIs/city → ~1M+ rows, 0.5–1 GB with spatial indexes) would
NOT fit — that is why it stays in the ETL world. If `nearby_facts` at 30/hotel
proves too heavy, drop to 15/hotel before considering paid tier.

Free-tier caveats to engineer around: Supabase Free pauses after ~1 week of
inactivity (the weekly ops bot's health check doubles as keep-alive — verify
this against current terms) and has connection limits (use the pooler /
PostgREST, no long-lived direct connections from Workers).

Budget escalation order if limits bite: Supabase paid (~$25/mo — already half
the budget: exhaust pruning first) vs Workers paid (~$5/mo — cheap, take it
first if CPU limits bind).

## 3. Serving-DB schema (unchanged essentials)

Tables and fields as in the original §17, with these deltas:
- `places` and `transport_segments` are ETL-world only.
- add `nearby_facts(hotel_id, rank, category, name, distance_m, location,
  source_release)`.
- add `hotel_affiliate_links` + `affiliate_providers`
  (see `docs/affiliate-matching.md §2`).
- `hotel_scores` unique on `(hotel_id, score_version, source_release)`;
  every score row carries version, release, computed_at, confidence,
  reason_codes.

## 4. Pipeline (monthly, GitHub Actions)

discover release → schema check (fail closed) → per-city bbox extract →
normalize to internal taxonomy → dedupe (GERS/source ids → normalized name →
category family → proximity ≤ 25 m → address; never merge distinct branches of
a chain; store canonical id + method + confidence) → data QA → load serving
tables (hotels, metrics recompute, scores, baselines, nearby_facts) → diff vs
prior run → tests → publish only material changes → log to `source_runs`.

Runtime budget (restated): 1 search query + 1 result query; no external calls.
Cache key `hotel_id + score_version + source_release`; edge-cache public pages;
cache popular autocomplete prefixes briefly.

## 5. Change detection & freshness

Material change = dimension score moves ≥ threshold, significant POI cluster
change, hotel identity/coords change, methodology change, meaningful
confidence change. Only material changes update `dateModified` or rebuild copy.
Refresh cadence: Overture monthly; internal popularity daily aggregate; GSC
weekly; affiliate link health weekly; SEO checks every deploy; license review
quarterly; scoring model only deliberately.

## 6. Cost bot

Track monthly estimates. If projected recurring > €35 before meaningful
revenue: identify top driver → disable optional AI → increase caching → reduce
refresh frequency → defer paid enrichment → alert owner. ≥ 25–30% of the €50
stays unused as reserve.

Never pay for: AI filler articles, bulk keyword variations, per-view
geospatial calls, hotel inventory before monetization is validated,
large-scale scraping infra.
