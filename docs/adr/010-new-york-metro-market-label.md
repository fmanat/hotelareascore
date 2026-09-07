# ADR-010 — "New York" market relabeled "New York City metro"

- **Status:** accepted
- **Date:** 2026-09-07 (overnight run)
- **Decision recorded from:** owner instruction (this session, task 2);
  `docs/reports/nyc-bbox-options.md` option (c)

## Context

351 of the "New York" dataset's 2,194 hotels (16%) carry a New Jersey
address region — confirmed via Overture's own `addresses[].region` field.
A bounding-box fix cannot separate them from real Staten Island hotels:
the two occupy the same longitude band (`docs/reports/nyc-bbox-options.md`
§"Why a bbox can't cleanly fix this"). That report presented three options
without a recommendation between (b) polygon-based extraction (a data
correctness fix) and (c) a market-label change (a positioning decision,
explicitly flagged as an owner call per CLAUDE.md §4).

## Decision

Owner selected option (c): keep the current bbox and ingested hotel set
unchanged, rename the market label everywhere it is a product-facing city
name from the literal "New York" to **"New York City metro"** — honest
framing for a market that genuinely includes well-connected satellite
cities (Jersey City, Hoboken, Newark, etc.), rather than implying every
hotel in it is literally within the 5 boroughs.

**What changed:** `data/config/cities.yml`'s `new_york` entry's `name`
field only. Every downstream consumer (`webdata.py`'s exported
`city_name`, city-page titles/breadcrumbs/meta description, hotel-page
breadcrumbs, the aggregate city page's JSON-LD `Place.name`) reads this
field, so the rename propagates with no other code change.

**What did NOT change (per the owner's explicit instruction to keep the
existing disclosure):**
- The bbox itself — still the 5-borough box from `docs/config/cities.yml`.
- `city.expected_region` (`NY`) and the per-hotel `_locality_mismatch`
  check in `webdata.py` — every NJ hotel still gets its own disclosure,
  now reading "Address region (NJ) does not match **New York City metro**
  (NY)" instead of "... New York (NY)" — the check is identical, only the
  market name in the sentence updates.
- Each hotel's own `address_locality` (e.g. "Jersey City", "Newark") — used
  as-is for JSON-LD `addressLocality` and the on-page "New York City metro
  · Jersey City" locality suffix (`hotel/[slug].astro`), unaffected by this
  ADR since it was already sourced from Overture's real address data, not
  the market label.
- `city_id: new_york` (URL slug, internal id) — unchanged; this is a
  display-name change only, not a re-identification.

## Consequences

- The 200-hotel pilot cohort proposal, prior ingestion/coverage reports,
  and `docs/strategy.md`'s launch-city list still say "New York" in their
  own (dated, historical) prose — not rewritten, since they describe what
  was true when written. Anything newly generated (city pages, hotel
  pages, `/methodology`, future reports) uses the new label going forward.
- No re-ingestion, no re-scoring, no data change — `webdata` was re-run
  only to regenerate the static JSON with the new label (same release,
  same score_version at the time of this ADR: 1.2.1, itself a coincidence
  of same-session timing with `docs/adr/009`, not a dependency between the
  two changes).
- If the owner later wants option (b) (polygon-based extraction) instead
  of or in addition to this label, that remains a separate, unstarted
  engineering task — this ADR does not preclude it.
