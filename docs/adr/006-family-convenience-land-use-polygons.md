# ADR-006 — family_convenience v2: score from land_use polygons, not points

- **Status:** accepted
- **Date:** 2026-09-06
- **Decision recorded from:** owner decision on
  `docs/reports/phase-3-calibration-sensitivity-report.md` §3; docs/scoring.md
  §3-5; CLAUDE.md §2 (rules 4, 5)

## Context

The §4.2 golden-set calibration found `family_convenience` wrong-signed
against its label in all 3 sample variants (Spearman −0.22 to −0.33, versus
+0.6 required). Root-cause investigation
(`docs/reports/phase-3-family-surface-vs-point.json`) found the cause: the
v1 formula counted **points** from Overture's `places` theme
(park/playground/zoo/aquarium categories) within 600m. A park is a polygon
in reality, and Overture separately publishes that polygon in its
`base/land_use` theme (`subtype='park'`, or `subtype='recreation'` /
`class='playground'`) — same monthly release, never previously ingested by
this pipeline (`src/hotelareascore/ingest.py` read only `places` and
`transportation`). Checked directly against the live release: **9 of 11**
golden-set hotels scoring exactly 0 on family_convenience have a real park
or playground polygon within 600–900m that the points-only extract has no
point for (as close as 60m in one case). A second, opposite effect also
turned up: heavily-mapped landmark parks (Hyde Park, London) are
represented by dozens of separate named points, likely inflating those
hotels' scores instead. Either way, point representation of an inherently
areal feature is inconsistent and not fixable by adjusting a weight.

## Decision

1. Ingest `theme=base/type=land_use` alongside `places` and
   `transportation`, with the same fail-closed schema check
   (`overture.REQUIRED_LAND_USE_COLUMNS`, `overture.check_schema`) —
   staleness over wrongness (CLAUDE.md hard rule 10) applies identically to
   this new source.
2. `family_convenience` becomes a dedicated scoring function
   (`scoring._family_convenience_dimension`, no longer the generic
   `_density_dimension`) that combines two sources into the same
   weighted-count → saturating-curve → city-percentile hybrid every other
   density dimension uses — **the formula shape and its constants
   (`decay_scale_m.family_convenience`, `absolute_saturation.family_convenience`,
   `hybrid_absolute_weight`) are unchanged**, only the input signal is more
   accurate:
   - points (`zoo`, `aquarium` — no polygon footprint exists for these in
     `land_use`);
   - green-space polygons (`park`, `playground`), distance measured via
     `ST_Distance(hotel_point, polygon)` to the **polygon's own boundary**
     (0 if the hotel is inside it) — never a centroid, which can be
     arbitrarily far from a hotel at the edge of a large or oddly-shaped
     park.
3. `park`/`playground` **places-theme points are kept** in the flat POI
   extract as `display_only_categories` (taxonomy-mapping.yml) — they still
   show up in the "Why?" nearby-facts section (a point named "Hyde Park" is
   a useful landmark to display) but no longer feed the score.
4. `score_version` → `1.1.0` (minor: rankings may shift, dimension semantics
   for family_convenience change materially, everything else is untouched).
   Full §5 protocol: re-ingest + re-score all 12 cities, per-city diff
   report, re-run the §4.2 calibration against the same 50 golden-set labels
   for family_convenience specifically (target: Spearman ≥ 0.6; if it still
   fails, stop and report back before touching anything else — no further
   constant tuning without owner review, per the same instruction that
   produced this ADR).

## Rationale

- This is a **data-source gap**, not a constant to retune — the sensitivity
  analysis (`docs/reports/phase-3-sensitivity-4.3.json`) already showed
  every existing constant is stable; reweighting a point-based formula
  further would not have fixed a structurally wrong input.
- Reusing the existing decay scale/saturation constants (rather than
  introducing new ones) keeps this a scoped, single-purpose change: new
  data source, same formula shape, no new tuning surface to also have to
  calibrate blind.
- Keeping park/playground points for display only avoids a display
  regression (losing "Hyde Park" as a nearby fact) while still fixing the
  score.

## Consequences

- New ETL output per city: `green_spaces.parquet`. New ingest failure mode:
  `base/land_use` schema drift now also fails the run closed, same as
  `places`/`transportation` today.
- `hotels.parquet` gains `address_region` (was already available from
  Overture's `addresses` struct, just not extracted) — used for the
  locality-consistency check (docs/STATE.md entity-QA backlog), not for
  scoring.
- If the recalibration still doesn't clear Spearman ≥ 0.6 for
  family_convenience, this ADR's decision (ingest land_use, score by
  boundary distance) stands regardless — the fallback is a further
  investigation (e.g. is `park`/`playground` even the right land_use
  vocabulary, is 600m radius still right for polygon-based proximity), not
  a reversion to points, and requires its own owner conversation before any
  further change ships.
