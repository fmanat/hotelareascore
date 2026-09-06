# HotelAreaScore — web (Phase 2 product proof)

Static Astro site, no live backend (`docs/adr/001`). Every page is
prerendered at build time from JSON exported from the Phase 1 ETL output —
see `../src/hotelareascore/webdata.py`. There is no server, no Supabase, and
no external call on the page-view path.

## Build

From the repo root (not this directory) — the data export needs the Python
package:

```bash
make web-install   # once
make web-build     # exports web/src/data + web/public/data, then `astro build`
make web-dev        # same export, then a live dev server on :4321
```

`web/src/data/*.json` and `web/public/data/search-index.json` are generated,
gitignored, and regenerated from whatever Overture release is in
`data/etl/` — never hand-edit them.

## Structure

```
src/lib/            flags.ts (feature flags, default off), types.ts, data.ts (JSON imports),
                     dimensions.ts + reasonCodes.ts (UI copy, grounded in docs/scoring.md)
src/layouts/         BaseLayout.astro — robots meta, nav, footer disclosure
src/components/       ScoreDimensions (6 scores + persona selector), NearbyFacts, MapSection,
                     CityComparison, ComparableHotels, CtaSection, SearchBox
src/pages/            index.astro (home), methodology.astro, hotel/[slug].astro (result page)
```

Result page section order is fixed by `docs/strategy.md §2` — don't reorder
without updating that doc first. All pages ship `noindex, nofollow`;
`docs/seo-policy.md §2` governs when that changes.
