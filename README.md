# StayContext

Independent hotel-location intelligence: before you book, understand the
surroundings. Computed scores from open geospatial data — not reviews, not
prices, not a booking engine.

Brand/domain: **StayContext**, staycontext.com (`docs/adr/012`). The repo,
Python package (`src/hotelareascore/`), and internal docs keep the
`hotelareascore` code name — only the product-facing brand changed.

**Status: see `docs/STATE.md` — the authoritative, current phase/gate
tracker. Don't trust a phase claim anywhere else in this README or in
`web/README.md`; both go stale between sessions, `docs/STATE.md` doesn't.**

## Prerequisites

- Python >= 3.11 (`pyproject.toml`), Node.js >= 22.12.0 (`web/package.json`)
- No accounts, no API keys, no `.env` needed to install or run tests —
  the ETL reads Overture's public S3 parquet directly (`src/hotelareascore/overture.py`)
- `gh` CLI only needed for CI/PR inspection, not for install or tests

## Install & test

```bash
pip install -e ".[dev]"    # Python package + dev/test deps
make test                  # pytest -q -- unit + data + integration tests

cd web
npm install                 # once
npm run typecheck           # astro check
npx playwright install      # once, for the E2E browsers
npm run test:e2e            # playwright test -- builds + serves fixture data itself
```

`npm run test:e2e` needs no manual fixture setup: its `webServer` config
(`web/playwright.config.ts`) runs `e2e/prepare-fixtures.mjs` then
`astro build` before starting the suite.

## Repo layout

```
CLAUDE.md              operating rules, auto-loaded each session by Claude Code
AGENTS.md              same operating rules, identical content, read by Codex
docs/
  STATE.md             phase tracker, gates, open decisions — start here
  strategy.md          thesis, journeys, phases, commercial model, legal list
  validation.md        Phase 0bis demand validation & kill/pivot/go criteria
  seo-policy.md        indexing policy, page types, pilot hotel cohort
  scoring.md           score model, calibration, version-change protocol
  data-and-costs.md    sources, ETL/serving split, volumetrics, cost bot
  affiliate-matching.md  hotel ↔ partner-inventory entity resolution
  adr/                 architecture decision records (001–005 = founding set)
  reports/             generated Data Proof Reports (owner acceptance artifact)
src/hotelareascore/     ETL package: Overture -> hotels/POIs/scores (Python + DuckDB)
data/config/            cities, taxonomy mapping, score weights (config, never hardcoded)
data/etl/               ETL-world output (Parquet, gitignored — regenerate with `make`)
web/                    Phase 2 product-proof site: Astro, static-first, no live backend
tests/                  unit tests (taxonomy, geo/decay, dedupe, slugs, verdict, config bounds)
scripts/                ops entry points (Phase 4+ bots)
.github/workflows/     CI — gates grow with phases, never weaken
```

## Phase 1 pipeline

```bash
pip install -e ".[dev]"
make ingest CITY=all      # Overture release -> per-city hotels/POIs/segments (data/etl/)
make score CITY=all       # -> hotel_scores + nearby_facts (docs/scoring.md v1 formulas)
make validate CITY=all    # data QA, fails closed on hard issues (CLAUDE.md hard rule 10)
make report CITY=london,bangkok RELEASE=latest   # -> docs/reports/data-proof-report-<release>.md
```

`make all` runs the four in sequence for both pilot cities. Every constant
behind the scores lives in `data/config/score-weights.yml` and is an
explicit v1 prior (docs/scoring.md §3) pending Phase 3 calibration.

## Phase 2 product-proof site

```bash
make web-install         # once
make web-build           # exports web/src/data + web/public/data, then `astro build`
make web-dev             # same export, then a live dev server
```

Static Astro site (docs/adr/001), no live backend: every hotel page is
prerendered at build time from the Phase 1 ETL output via
`src/hotelareascore/webdata.py` (no Supabase yet — see `docs/adr/002` for why
that's deliberate at this phase). `web/src/data/*.json` + `web/public/data/
search-index.json` are committed (not gitignored) since 2026-09-07's first
deploy — a build host like Cloudflare Pages has no `data/etl/` to export
from; see `web/README.md`'s "Committed artifacts" section for the exact
files, the regen command, and the build guard that fails fast if one is
missing. All feature flags
(`PUBLIC_INDEXING_ENABLED`, `MAP_ENABLED`, `AFFILIATE_ENABLED`, …) default
off, so every page ships `noindex, nofollow` and the map/CTA sections render
as disabled placeholders until an owner decision turns them on.

## Founding decisions (see docs/adr/)

1. Astro static-first on Cloudflare Pages/Workers (+R2)
2. ETL world (DuckDB/Parquet/R2) split from serving world (Supabase free tier)
3. Overture Maps primary source; STAC discovery; fail-closed schema adapters
4. Versioned scoring; golden-set regression; sensitivity-driven calibration
5. Indexability as recorded decision; 150–300-page pilot hotel cohort

## Non-negotiables (short form — full list in CLAUDE.md §2–3)

No invented facts, no fake freshness, no doorway/scaled pages, no per-view
geospatial API calls, no silent score changes, affiliate never influences
scores, secrets server-side only, fail closed on bad upstream data.
