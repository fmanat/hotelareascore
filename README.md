# HotelAreaScore (working name)

Independent hotel-location intelligence: before you book, understand the
surroundings. Computed scores from open geospatial data — not reviews, not
prices, not a booking engine.

**Status: Phase 0 (repo & ADRs) + Phase 0bis (demand validation) — nothing
heavier is authorized yet. Read `docs/STATE.md` first, always.**

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
data/config/           weights, brand aliases (config, never hardcoded)
scripts/               ETL & ops entry points (Phase 1+)
.github/workflows/     CI — gates grow with phases, never weaken
```

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
