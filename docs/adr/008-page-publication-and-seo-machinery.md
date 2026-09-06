# ADR-008 — page_publication + SEO machinery, built inert ahead of Phase 4

- **Status:** accepted
- **Date:** 2026-09-06/07 (overnight run, owner-authorized in advance, Bloc C)
- **Decision recorded from:** overnight mission order Bloc C; CLAUDE.md hard
  rule 2; docs/seo-policy.md §4/§6

## Context

Phase 4 (SEO launch) needs `page_publication` (indexability as a recorded
decision), sitemaps split by type, robots.txt, canonicals, structured data,
a city page template, and CI assertions enforcing all of it — but Phase 4
itself has not started, no domain is chosen, and every relevant flag
(`PUBLIC_INDEXING_ENABLED`, `HOTEL_PAGE_INDEXING_ENABLED`) is off. The
order was explicit: build the machinery now, keep it structurally inert,
never launch anything.

## Decision

1. **`page_publication` is a local SQLite store** (`data/serving/
   page_publication.sqlite`, `src/hotelareascore/publication.py`), not a
   live Supabase table — Supabase isn't provisioned yet. The schema
   matches `migrations/0001_page_publication.sql` (the real Postgres DDL
   for when Supabase exists) closely enough that porting means swapping
   the connection in `publication.py`'s one internal function, not
   rewriting callers. Every write goes through `set_status()`, which
   requires a `reason` and a `decided_by` — there is no code path that
   flips a status as a side effect.
2. **`scripts/compute_publication.py`** seeds decisions from
   `docs/reports/pilot-cohort-proposal.csv` (Bloc D): pilot-cohort hotels
   → indexable, numeric-name/unresolved-duplicate hotels → draft, every
   other hotel → noindex, all 12 city pages → noindex, home/methodology →
   indexable, compare → noindex, the 4 legal pages → draft (owner hasn't
   reviewed them).
3. **The static site reads the recorded decision, never infers it**:
   `webdata.py`'s `export_city` looks up each hotel's status and sets
   `hotel.publication_status`; `[slug].astro` passes
   `indexable={hotel.publication_status === 'indexable'}` to `BaseLayout`.
   `BaseLayout` ANDs that with `FLAGS.PUBLIC_INDEXING_ENABLED` and an
   optional per-page-type flag (`requiresFlag`, e.g.
   `HOTEL_PAGE_INDEXING_ENABLED` — previously defined in `flags.ts` but
   never actually wired to anything, a real pre-existing gap closed here)
   before ever rendering `index, follow`.
4. **`robots.txt` is the actual kill switch**, not the sitemap's content:
   while `PUBLIC_INDEXING_ENABLED` is off, `robots.txt` disallows every
   crawler from everything, which makes whatever the sitemap lists moot in
   practice. The sitemap itself is still built correctly (split by type —
   static/cities/hotels — and filtered to the recorded indexable set) so
   the machinery is real and testable now, not a stub to fill in later.
5. **No real domain exists yet** (docs/STATE.md open owner decision).
   Canonical URLs and JSON-LD need an absolute base URL to be structurally
   correct and CI-testable, so `web/src/lib/site.ts` defines `SITE_URL =
   'https://example.invalid'` — the IANA/RFC 2606 reserved domain
   guaranteed to never resolve, never a real-looking placeholder. One
   constant to update when the domain is chosen.
6. **Structured data is Hotel/LodgingBusiness/Place/BreadcrumbList/WebSite
   only** (`web/src/lib/jsonld.ts`) — no `aggregateRating`/`review`/rating
   fields anywhere, ever (CLAUDE.md hard rule 3, 7). Enforced twice: the
   builder functions structurally can't emit those fields, and
   `web/scripts/seo_assertions.py` parses every emitted JSON-LD block and
   fails the build if a forbidden key appears anywhere in it.
7. **City pages** (`/city/{id}`, all 12, all noindex) are generated from a
   new lightweight aggregate (`webdata.py`'s `export_city_pages`) —
   distributions, top-3-per-dimension, 5 representative hotels — computed
   directly from ETL parquet for all 12 cities, NOT a full per-hotel
   export (that stays scoped to the 2-city Phase 2 footprint). Copy is
   explicit "highest-scoring areas ... in our dataset," never "best
   neighborhood" (docs/seo-policy.md §3).
8. **SEO build-time assertions run in CI** (`web/scripts/seo_assertions.py`,
   new `seo-assertions` job) against the built `dist/`: exactly one
   canonical per page (checked on the full build — a structural
   requirement, not an SEO-visibility one), unique titles **among the
   recorded-indexable set only** (checked against the full ~34k-hotel
   build first and found real, legitimate title collisions — multiple
   actual "Premier Inn London Southwark" branches share a name; that has
   nothing to do with SEO since those pages are noindex and never
   submitted to a search engine — narrowed the check accordingly, and also
   fixed the hotel-page title template to include locality, which cut
   collisions substantially on its own), JSON-LD parses and carries no
   forbidden keys, and the hotel sitemap is an exact match (⊇ indexable, ∌
   noindex/draft) against what `web/src/data/hotels-*.json` actually
   recorded.
9. **The 4 owner-provided legal page templates** (legal-notice, privacy,
   affiliate-disclosure, terms) are Astro markdown pages using
   `BaseLayout` via frontmatter `layout:` — which required a BaseLayout
   fix, since Astro passes a markdown page's frontmatter nested under
   `Astro.props.frontmatter`, not spread into top-level props the way an
   explicit `<BaseLayout title=... />` call does; `BaseLayout` now merges
   both so either calling convention works. Every `[bracket]` placeholder
   is untouched, and a visible amber "DRAFT — OWNER REVIEW PENDING" banner
   (a global, not scoped, CSS rule — scoped styles don't reach content
   rendered through a layout's `<slot />`) sits at the top of each. Linked
   from the footer on every page.

## Rationale

- Recording decisions in a real (if local) store with mandatory reasons is
  what makes "indexability is a decision, never a side effect" actually
  true in code, not just true in a doc — a page_publication table nobody
  writes to with a required justification is decoration.
- Splitting the "recorded decision" (page_publication) from "the actual
  kill switch" (robots.txt + PUBLIC_INDEXING_ENABLED) means the real
  machinery — sitemap generation, per-hotel indexable computation, city
  aggregates — can be built, tested, and CI-verified completely honestly
  right now, with zero risk of anything actually reaching a search engine
  before Phase 4 is a deliberate decision.
- Narrowing the title-uniqueness check to the indexable set (rather than
  weakening or dropping the assertion) keeps the CI gate meaningful: it
  answers "will Google see two identical titles," which is what
  docs/seo-policy.md §6 actually cares about, instead of a technically
  stricter but practically meaningless full-dataset check that would fail
  on real, harmless chain-hotel naming.

## Consequences

- Porting `page_publication` to Supabase (Phase 4) means writing a Postgres
  backend for `publication.py`'s `connect()`/`_upsert` path and applying
  `migrations/0001_page_publication.sql`; every caller (`webdata.py`,
  `compute_publication.py`) is unaffected.
- `SITE_URL` must be updated the day a domain is chosen — every canonical,
  sitemap entry, and JSON-LD `url` field depends on it. One file.
- The city page template's `representative_hotels`/`top_by_dimension`
  entries link to a real hotel page only for cities with a full hotel
  export (today: bangkok, london); the other 10 cities show plain text
  until their hotel pages are built — by design, not a bug, documented in
  `webdata.py`'s `_city_page_aggregate`.
- Found and fixed one pre-existing bug while building this:
  `validate.py`'s city baseline wrote the Overture *release* id into the
  `score_version` field (an ingest-manifest key confused for a score
  manifest key) — every `city_baseline.json` ever produced had this wrong.
  Fixed and re-validated all 12 cities.
