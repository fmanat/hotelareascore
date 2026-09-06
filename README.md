# HotelAreaScore (working name)

Independent hotel-location intelligence: before you book, understand the
surroundings. Computed scores from open geospatial data — not reviews, not
prices, not a booking engine.

**Status: Phase 1 (data proof — London + Bangkok) — pipeline runs end to end;
see `docs/reports/data-proof-report-*.md` for the latest run and
`docs/STATE.md` for what's next. Nothing past Phase 1 is authorized yet.**

## Repo layout

```
CLAUDE.md              operating rules for Claude Code sessions (only file
                       auto-loaded each session)
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
tests/                  unit tests (taxonomy, geo/decay, dedupe, config bounds)
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
