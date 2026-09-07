# ADR-012 — Brand & domain: StayContext / staycontext.com

- **Status:** accepted
- **Date:** 2026-09-07
- **Decision recorded from:** owner instruction, this session, task 1

## Context

`docs/STATE.md`'s open-decisions list carried "domain/brand name" as the
last unresolved item blocking Phase 4 launch framing (it also blocked
giving `web/src/lib/site.ts`'s `SITE_URL` a real value — `docs/adr/008`
used `https://example.invalid`, the RFC 2606 reserved non-resolving
domain, specifically so canonical/JSON-LD generation could be built and
CI-tested ahead of the decision without ever looking like a real URL).

## Decision

Product brand: **StayContext**. Domain: **staycontext.com**, already
owned by the owner (no purchase needed).

## What changed

- `web/src/lib/site.ts`: `SITE_URL = 'https://staycontext.com'` — the
  single constant every canonical URL, sitemap entry, and JSON-LD `url`
  field reads.
- `.env.example`: added `SITE_URL=https://staycontext.com` as a documented
  reference value (not wired to `site.ts`, which stays a static constant
  per its own design — see that file's comment).
- User-facing brand text, everywhere it appeared, replaced "HotelAreaScore"
  with "StayContext": `BaseLayout.astro` (page `<title>` suffix, header
  brand link), `jsonld.ts` (`WebSite.name`, the `PropertyValue.name` on
  every hotel's `LodgingBusiness` JSON-LD), the 4 DRAFT legal pages'
  frontmatter `description`, `methodology.astro`'s `description` (there is
  no separate "about" page — methodology serves that role), and the root
  `README.md`'s title/intro.
- `web/scripts/seo_assertions.py`: the sitemap-path-normalization helper
  hardcoded the string `example.invalid` to strip the host from an
  absolute `<loc>` URL. Fixed properly rather than swapped: replaced with
  a generic `re.sub(r"^https?://[^/]+", "", loc)` that strips ANY absolute
  host, so this doesn't need editing again on a future domain change.

## What deliberately did NOT change

- The internal code name: the GitHub repo (`hotelareascore`), the Python
  package (`src/hotelareascore/`), `CLAUDE.md`'s own title, code comments
  referencing `src/hotelareascore/*.py` module paths, and dated historical
  reports that used "HotelAreaScore" as shorthand for "the scoring system"
  at the time they were written (e.g. `docs/reports/data-proof-report-
  2026-08-19.0.md`, `data/config/taxonomy-mapping.yml`'s comments,
  `pyproject.toml`'s package description). Renaming these would be a
  cosmetic, high-diff, zero-user-value change to code identity — CLAUDE.md
  §0's "smallest reversible change" principle argues against it, and the
  owner's instruction was explicit that the internal code name stays.
- `web/README.md` (the web subpackage's developer build instructions) —
  dev-facing documentation tied to the repo/package identity, not the
  product brand a visitor sees.
- Nothing was deployed, no flag was flipped, every page still renders
  `noindex, nofollow` (`PUBLIC_INDEXING_ENABLED` stays off) — this is a
  content/config change only, verified by re-running the build-time SEO
  assertions, `typecheck`, and the e2e suite locally against the new
  `SITE_URL` before commit.

## Consequences

- Removed from `docs/STATE.md`'s open-decisions list.
- `docs/reports/phase-4-launch-runbook.md` (this session) is the first
  document written against the real domain rather than a placeholder.
- If the domain or brand ever changes again, the same single-constant
  design (`SITE_URL`) plus this ADR's list of "what changed" is the
  checklist to redo.
