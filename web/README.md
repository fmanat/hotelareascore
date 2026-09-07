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

`web/src/data/*.json` and `web/public/data/search-index.json` are generated
from whatever Overture release is in `data/etl/` — never hand-edit them.

**Committed artifacts, not gitignored (2026-09-07 — the first Cloudflare
Pages deploy, docs/adr/012 and docs/reports/phase-4-launch-runbook.md):**
`data/etl/` isn't committed (it's the ETL world, deliberately separate —
`docs/adr/002`), so a fresh checkout on a build host like Cloudflare Pages
has nothing to export from. Rather than run the full ingest+score
pipeline inside that build (network-dependent, several minutes, exactly
the scope this deploy was kept out of — see the runbook), the current
export is committed: `web/src/data/{hotels-london,hotels-bangkok,
city-baselines,city-pages,meta,personas}.json` and
`web/public/data/search-index.json`, un-ignored in `web/.gitignore` with
a comment. Scoped to `--city london,bangkok` (matching which cities
actually get individual hotel pages — see `src/lib/data.ts`'s
`ALL_HOTELS`), not `--city all`: including every city's hotel export
would bloat the commit for data no page ever reads. Regenerate and
recommit with:

```bash
python3 -m hotelareascore.cli webdata --city london,bangkok  # from the repo root, needs data/etl/
```

`npm run build` runs `scripts/check-data-exports.mjs` first (an npm
`prebuild` hook) — it fails fast with an explicit message naming the
missing file and the command above, instead of a bare bundler
`UNRESOLVED_IMPORT` several build-minutes in.

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
