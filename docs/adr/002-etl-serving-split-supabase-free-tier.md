# ADR-002 — ETL world / serving world split; Supabase free-tier fit

- **Status:** accepted (Phase 0)
- **Date:** 2026-09-06
- **Decision recorded from:** docs/data-and-costs.md §2–3, CLAUDE.md §5

## Context

Full filtered POI data for 12 cities is ~1M+ rows (0.5–1 GB with spatial
indexes) and does not fit Supabase Free (500 MB). The €50/month ceiling makes
a paid database tier (~$25/mo) half the entire budget. Meanwhile, a page view
only ever needs a hotel's identity, its precomputed metrics/scores, city
baselines, and a small set of nearby facts.

## Decision

Two worlds, hard boundary:

- **ETL world (offline):** DuckDB + Parquet snapshots in R2/local. Holds raw
  Overture extracts, full `places`, `transport_segments`, dedupe workspace.
  Size irrelevant to serving.
- **Serving world (Supabase Postgres + PostGIS):** only page-view tables:
  `cities, hotels, hotel_metrics, hotel_scores, city_score_baselines,
  page_publication, hotel_affiliate_links, affiliate_providers, source_runs,
  search_events, outbound_clicks, nearby_facts` (top-N per hotel, ~30, drop
  to 15 if size bites). Estimated total ~285 MB for 12 cities.

## Rationale

- This is the single rule that makes the budget credible: serving fits the
  free tier with headroom, and heavy geospatial compute happens where storage
  is nearly free (Parquet in R2).
- Precomputation is already mandated by the runtime budget (1 search query +
  1 result query, no external calls); the split just gives it a storage
  architecture.

## Alternatives considered

- **Everything in Supabase paid:** burns half the budget before launch, and
  invites per-view geospatial queries (hard rule #4 violation risk).
- **SQLite/D1 at the edge:** attractive later; PostGIS maturity and PostgREST
  pooling win for v1. Revisit only via a new ADR if Supabase limits bind.

## Consequences

- Any feature needing full-POI queries at runtime is by construction a design
  error; redesign as a precomputed metric or nearby_fact.
- Free-tier caveats engineered around: weekly ops bot doubles as keep-alive
  (verify against current Supabase terms); use pooler/PostgREST from Workers,
  no long-lived connections.
- Escalation order if limits bite: prune first; Workers paid (~$5) before
  Supabase paid (~$25).
