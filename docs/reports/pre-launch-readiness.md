# Pre-launch readiness — Bloc I

- **Date:** 2026-09-09/10, night mission #4, Bloc I
- **Status: report only.** No flag touched, no `page_publication` write,
  no dashboard action. Every number below is measured live or read from
  the current repo state at the time this was written — not assumed.

## Flags (all OFF, confirmed)

`.env.example` / `web/src/lib/flags.ts`, 9 flags, all `false`:
`PUBLIC_INDEXING_ENABLED`, `HOTEL_PAGE_INDEXING_ENABLED`,
`AFFILIATE_ENABLED`, `AI_SUMMARIES_ENABLED`,
`MISSING_HOTEL_GEOCODING_ENABLED`, `MAP_ENABLED`, `DATA_REFRESH_ENABLED`,
`SEO_AUTOMATION_ENABLED`, `ANALYTICS_ENABLED`. No live deployment env var
overrides these (unverifiable without dashboard access, but nothing in
this repo or the go-live checklist would have set one).

## `page_publication` (current state, queried live)

| Status | hotel | city | static |
|---|---:|---:|---:|
| draft | 712 | 12 | 6 |
| noindex | 33,254 | 0 | 1 |
| indexable | 0 | 0 | 0 |
| retired | 4 | 0 | 0 |

712 hotel-draft = 200 pilot-cohort v2 (staged, `docs/reports/go-live-seo-checklist.md`)
+ 512 numeric-name/unresolved-duplicate (never meant to go live, `docs/adr/014`).
12 city-draft = all 12, staged. 6 static-draft = home, methodology, 4
legal pages. 1 static-noindex = compare (permanent, by design). **Nothing
is currently `indexable`** — the go-live checklist's steps 3/5 haven't
run.

## Sitemaps, canonicals, robots.txt, headers, 404 — live-verified just now

`make verify-prod` against `https://staycontext.com`: **48/50 checks
pass.**

- **Sitemaps**: all 4 endpoints return 404 with our own 404 page's body
  (not sitemap content) — confirmed not exposed.
- **Canonicals**: every sampled page type (home, static-subset hotel,
  limited-data hotel, city, compare, methodology, 4 legal pages) has
  exactly one canonical, pointing at `https://staycontext.com/...`.
- **robots.txt**: served by our own `robots.txt.ts` (`Disallow: /` for
  `*`, no `Sitemap:` line) — **confirmed live, not the Cloudflare
  "Managed robots.txt" zone fallback seen during the September 9 platform
  incident.** Per this mission's note, that zone feature has been
  disabled on the owner's side; this check is the independent
  confirmation that it's actually gone, not just reported gone.
- **Headers**: HSTS (`max-age=31536000; includeSubDomains`),
  `X-Content-Type-Options: nosniff`, `Referrer-Policy`,
  `Permissions-Policy`, and `Content-Security-Policy-Report-Only` all
  present and correct on the live custom domain (this specifically was
  broken during the incident — re-confirmed fixed).
- **404**: a nonsense path returns a real 404 status with our own
  `404.astro` page.
- **Only failures**: `https://www` doesn't redirect to the apex (serves
  correctly, just doesn't consolidate) — known, minor, no SEO risk
  (canonicals already handle it), Cloudflare dashboard item.

## Performance & accessibility — live Lighthouse, just now

| Page | Performance | Accessibility |
|---|---:|---:|
| Home | 100 | 100 |
| Hotel (static subset) | 99 | 100 |
| City (Tokyo) | 98 | 100 |

Accessibility 100 on every sampled page. Known **open, not fixed this
session** (`docs/reports/phase-4-accessibility-audit.md`, re-checked just
now against current code):
- Finding 1 (HIGH, no keyboard model for autocompletes) — **fixed**
  (shared `lib/autocomplete.ts`, WAI-ARIA combobox pattern, verified by
  this session's own 12-city keyboard-only E2E tests, Bloc H item 2).
- Finding 2 (MODERATE, incomplete combobox pattern) and finding 4
  (MODERATE, no live-region on persona switch) — **very likely fixed by
  the same change** (the shared module implements both), not
  independently re-verified against the original finding's exact
  reproduction steps this session.
- Finding 6 (three drifted widget copies) — **fixed** (now one shared
  module).
- Finding 3 (MODERATE, persona `tablist`/`tab` roles with no
  Left/Right-arrow keyboard model) — **still open**, confirmed by reading
  `ScoreDimensions.astro` just now: the roles exist, no arrow-key handler
  does.
- Finding 5 (LOW-MODERATE, border color contrast) — **still open**,
  `--border: #e6e2da` against `--bg: #fbfaf8` not re-measured against
  WCAG 1.4.11 this session, no code change since the finding.

## Open decision: AI Crawl Control (Cloudflare zone feature) — pros/cons, no recommendation forced

Cloudflare's AI Crawl Control lets a zone allow/block AI crawlers
(GPTBot, ClaudeBot, Google-Extended, etc.) independent of `robots.txt`.
The Cloudflare-managed fallback robots.txt seen during the incident had
this baked in (`Content-Signal: search=yes,ai-train=no,use=reference`,
named-bot `Disallow:`) — now disabled per this mission's note, so our own
`robots.txt.ts` is the only signal in effect. Whether to configure AI
Crawl Control deliberately (once real content is indexable) is still
open:

- **For blocking AI training crawlers**: the product's differentiator is
  computed, licensed-source data (Overture), not editorial prose — AI
  systems training on scraped copies of the site gain little that isn't
  already free from Overture itself, while search/AI-answer crawlers
  quietly reading and citing the site (ChatGPT/Perplexity-style
  citations) could still be a real, free discovery channel worth keeping
  open. `docs/STATE.md`'s own "AI Overviews" blocker already flags this
  as unmeasured territory — blocking AI crawlers entirely would remove
  the chance to observe it.
- **For allowing them broadly**: more surface area for AI-answer engines
  to cite/link back (a possible top-of-funnel channel with literally
  zero infrastructure cost), and it's consistent with `robots.txt`
  already being wide open to every crawler once indexing turns on (no
  reason to selectively wall off just AI systems if regular search
  engines are welcome).
- **Middle ground**: allow AI *answer/citation* crawlers, block AI
  *training* crawlers specifically — the exact distinction Cloudflare's
  own `Content-Signal` mechanism is built for (`search`/`ai-input`/
  `ai-train` as separate signals) — closest to what the now-disabled
  zone default was already doing.

No recommendation is recorded here on purpose — this is a product-
positioning call (CLAUDE.md §0.4's owner-decision-boundary rule), not a
technical one.

## What's still missing before GO, in order

**Depends on the owner:**
1. **Pilot cohort v2 review** — the only real remaining blocker
   (`docs/STATE.md` open decision (b), `docs/reports/pilot-cohort-proposal.md`).
   Nothing else below can start until this is a recorded GO.
2. Legal placeholders on the 4 legal pages (Companies House number,
   address, contact email, governing-law line) — owner-provided content,
   not technical work.
3. GSC domain-property verification (needs the owner's Google account —
   `docs/reports/go-live-seo-checklist.md` step 2 has the exact DNS TXT
   procedure via Cloudflare).
4. AI Crawl Control decision (above) — not blocking, but worth deciding
   before real crawl traffic starts.
5. `https://www` → apex redirect rule (Cloudflare dashboard, cosmetic).
6. Destination/resort hotel-type detection refinement decision
   (`docs/reports/destination-type-detection-feasibility.md`) — separate
   track, not a go-live blocker.
7. Golden-set labeling pass, including the 6 new non-urban hotels
   (`docs/reports/golden-set-expansion-2026-09.md`) — publish
   `tools/golden-labeler` as an Artifact when ready.

**Depends on Claude (mechanical, once the above unblock it):**
1. Execute `docs/reports/go-live-seo-checklist.md` steps 3-6 (flip flags,
   flip `page_publication` to indexable, rebuild, submit sitemap, start
   the 90-day clock) — already written, tested via dry-run, just gated.
2. Persona-selector keyboard model (a11y finding 3) — small, scoped fix,
   not started.
3. Border-contrast fix (a11y finding 5) — needs a real WCAG 1.4.11
   measurement first, not started.
4. Detection-refinement implementation, only after item 6 above is
   decided.
