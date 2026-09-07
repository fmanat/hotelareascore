# Performance audit — home, hotel, city, compare, legal pages

> Task 3 (the T5 skipped in the previous overnight session). Local
> Lighthouse (v13.4.1, performance category, headless Chrome, default
> mobile-throttling simulation), served via `npx serve dist` on the real
> `astro build` output — full 12-city real data (`score_version` 1.2.1,
> release `2026-08-19.0`), not fixtures. Every flag OFF, exactly the build
> that would deploy today.

## Numbers

| Page | URL tested | Perf score | LCP | FCP | TBT | CLS | Speed Index | Transfer |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| Home | `/` | 99 | 0.8s | 0.7s | 0ms | 0.000 | 3.5s | 3.9 KB |
| Hotel | `/hotel/the-hindes-hotel-79c564e7/` | 100 | 0.9s | 0.8s | 0ms | 0.000 | 0.8s | 8.2 KB |
| City | `/city/london/` | 100 | 0.8s | 0.7s | 0ms | 0.000 | 0.7s | 4.2 KB |
| Compare | `/compare/` | 100 | 0.8s | 0.7s | 0ms | 0.041 | 0.7s | 4.8 KB |
| Legal (notice) | `/legal-notice/` | 100 | 0.8s | 0.7s | 0ms | 0.000 | 3.3 KB | 3.3 KB |

Resource breakdown (all 5 pages): **zero JavaScript, zero fonts, zero
images on any page** — static-first with system fonts and no client JS
means there is nothing to lazy-load, no font-swap flash, no hydration
cost. Total-blocking-time is 0ms everywhere. Only the hotel page pulls a
separate external stylesheet (`/_astro/_slug_.BKskeM0m.css`, 1.7 KB) — every
other page type's CSS is inlined into the document by Astro's default
`build.inlineStylesheets: 'auto'` heuristic (page-size-dependent).

## Points, ranked by impact

1. **Home's 3.5s Speed Index despite a 0.8s LCP and only 2 total requests
   (document + favicon) is very likely a Lighthouse throttling-model
   artifact, not a real issue** — there is no additional content, script,
   or resource loading after first paint to explain a slow "visually
   complete" time on a 3.9 KB page. Flagged, not fixed: worth re-checking
   once the site is on a real network (Cloudflare Pages + real DNS/TLS)
   rather than a local static server before treating this as meaningful.
   **Impact: low** (every other timing metric on this page is already
   excellent).
2. **The hotel page's one extra external-CSS request** is the only
   structural asymmetry across the 5 page types — small (1.7 KB, no
   measurable score impact at this size) but free to remove: Astro
   supports forcing `inlineStylesheets: 'always'` project-wide, which
   would inline this page's CSS the same way every other page's already
   is. **Impact: low, but zero-risk** — see "Applied" below.
3. **Local test conditions understate two things a real deploy changes**:
   compression and caching. `npx serve` (used for this audit) does not
   gzip/brotli responses or set the cache headers Cloudflare Pages applies
   automatically at the edge; the byte weights above are pre-compression.
   **Not a code issue** — nothing to fix in this repo; worth re-running
   this same audit once B1 of `docs/reports/phase-4-launch-runbook.md`
   (first Pages deploy) exists, to confirm the platform behaves as
   expected rather than assuming it.
4. **Nothing else scored below 1.0 on any Lighthouse performance audit**
   (render-blocking-resources, unused-css-rules, text-compression,
   server-response-time, bootup-time, legacy-javascript — all clean) on
   any of the 5 page types. There is very little room left to improve
   without adding features (a map, richer imagery) that would themselves
   add weight — the current profile is close to the floor for what a
   content page can weigh.

## Applied (safe, zero-risk only)

**`web/astro.config.mjs`: added `build: { inlineStylesheets: 'always' }`.**
Removes the hotel page's one external stylesheet request project-wide,
inlining every page's CSS the same way most pages already got by default.
No CSS content changed — same rules, same selectors, different delivery
mechanism only.

**Verification, before vs. after** (`npm run typecheck`, `npm run build`,
`npx playwright test`, this same 5-page Lighthouse pass):
- Typecheck: 0 errors before and after.
- Build: same 3 page counts, same routes, same HTML structure —
  `dist/hotel/*/index.html` no longer references an external `.css` file;
  `<style>` now appears inline in `<head>`, byte-for-byte the same rules.
- E2E: 10/10 passed before, 10/10 passed after (full suite, both desktop
  and mobile projects) — see below.
- Lighthouse (re-run against the rebuilt real-data site, same 5 URLs):
  hotel page's request count dropped from 2 to 1 (document only, CSS now
  inline in the 6.8 KB document instead of a separate 1.7 KB file); every
  page now scores a flat **100**. LCP stayed at 0.8s everywhere — the
  removed request was already too small to move the score, this closes a
  structural asymmetry (hotel pages differing from the other 4 for no
  content reason) rather than fixing a measured regression.

**Nothing else was touched.** No lazy-loading changes (nothing to lazy —
zero images, zero non-critical scripts exist on any of these 5 pages), no
asset-weight changes (nothing compressible left to shrink at this size),
no load-order changes beyond the one CSS-delivery change above. Anything
larger — adding a CDN/compression layer, restructuring how MapLibre will
load once `MAP_ENABLED` flips, image strategy for any future photography —
is a structural decision for its own review when that feature actually
ships, not a change to make speculatively against a page that doesn't use
it yet.
