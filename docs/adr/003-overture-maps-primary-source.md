# ADR-003 — Overture Maps as primary data source (STAC discovery, fail-closed adapters)

- **Status:** accepted (Phase 0)
- **Date:** 2026-09-06
- **Decision recorded from:** docs/data-and-costs.md §1, §4; CLAUDE.md §5

## Context

Scores are computed from POIs, transport and road/rail context around hotels,
worldwide, refreshed monthly, at ~zero data cost. Sources considered: Overture
Maps, raw OSM, commercial POI APIs (Google Places, Foursquare, HERE).

## Decision

- **Primary:** Overture Maps monthly GeoParquet releases, per-city bbox
  extraction, release discovery via **catalog/STAC — never a hardcoded
  release path**.
- **Schema adapters mandatory**; unexpected upstream schema → **fail closed**
  (no scores or pages published from that run). Older `categories` field is
  deprecated (2026): code against current taxonomy fields.
- Secondary sources (OSM-derived, Wikidata, GTFS, official open data, airport
  datasets, affiliate hotel metadata) each require: license check,
  attribution, provenance, refresh policy, normalized schema.
- Live traffic never depends on public OSM infra (Nominatim, public Overpass,
  community tiles).
- Theme-level license metadata retained (some themes carry ODbL obligations).

## Rationale

- Overture gives normalized, deduplicated-ish, globally consistent GeoParquet
  that DuckDB reads natively — the entire ETL stays free and reproducible.
- Commercial POI APIs violate both the budget and hard rule #4 (per-view or
  per-hotel API economics, restrictive caching terms).
- Raw OSM alone pushes taxonomy normalization and QA burden onto us; Overture
  already layers much of that, and OSM remains available as a secondary.

## Consequences

- Monthly pipeline starts with release discovery + schema check; a skipped
  month (schema break) is a normal, safe outcome — staleness over wrongness.
- Internal stable taxonomy with tested mappings (docs/scoring.md §6) shields
  scores from upstream taxonomy churn.
- Attribution/licensing page is a product requirement from Phase 2.
