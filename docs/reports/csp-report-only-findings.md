# CSP Report-Only findings — key pages

- **Date:** 2026-09-09 (night mission #2 follow-up, Tache 2)
- **Method:** the live site is down (`docs/STATE.md` "PROD DOWN"), so this
  is a static analysis of the same build that would deploy — inline
  `<script>`/JSON-LD/`<style>` content in `web/dist/**` for one sample of
  each page type, diffed against the shipped
  `Content-Security-Policy-Report-Only` (`web/public/_headers`). No
  browser devtools console, no report collector (wiring one needs a new
  service, out of scope). Re-run `make verify-prod` once prod is back for
  the real thing — it does the same diff against live responses.
- **Policy stays Report-Only this session, as instructed** — nothing below
  enforces or blocks anything.

## What the first cut of the policy would have flagged

`script-src 'self'` (no `'unsafe-inline'`) — the initial Bloc B
policy — would have reported a violation on every page that has ANY
inline `<script>`, including `type="application/ld+json"` (CSP's
`script-src` gates all `<script>` elements regardless of `type`, even
though JSON-LD isn't executable):

| Page | Inline `<script>` blocks | Of which JSON-LD |
|---|---:|---:|
| home | 1 | 1 |
| hotel (static subset) | 4 | 3 |
| hotel (limited-data card) | 1 | 0 |
| city | 2 | 2 |
| compare | 0 | 0 |
| methodology | 0 | 0 |
| legal-notice / privacy / affiliate-disclosure / terms | 0 | 0 |
| 404 | 0 | 0 |

`style-src 'self' 'unsafe-inline'` already covered every page's inline
`<style>` block (Astro's `build.inlineStylesheets: 'always'`,
`astro.config.mjs`) and the hotel page's 6 inline `style="…"` attributes —
no violations there, nothing to change.

## Verdict: these script-src violations are legitimate, not a red flag

Every single one is first-party, build-time-generated content — never
user-supplied, never fetched from a third party:

- The JSON-LD blocks are `JSON.stringify()` of typed data
  (`web/src/lib/jsonld.ts`) built from our own scores/hotel records —
  Astro escapes template output by default, and nothing on this site
  accepts free-text user input that gets rendered server-side (no
  comments, no reviews, no forms that echo back).
- The non-JSON-LD inline scripts are the site's own small interactive
  widgets: `SearchBox.astro`, `ComparePicker.astro`, `compare.astro`'s
  picker, the persona-tab switcher, `hotel/limited.astro`'s fetch-and-
  render logic — all committed, reviewed code, none of it third-party.

There is no injection point anywhere on the site (confirmed while writing
`docs/reports/hotel-pages-architecture-options.md`-adjacent work: zero
external scripts, zero user-generated content, `default-src 'self'`
already blocks loading JS from any external origin, which is the other
half of what a strict `script-src` usually protects against).

**Policy corrected**: `script-src 'self'` → `script-src 'self'
'unsafe-inline'` (matching `style-src`'s existing pattern) — the
Report-Only run against this build now has nothing left to flag. Not
enforced this session.

## What this does and doesn't buy

- **Still meaningful**: `default-src 'self'` blocks loading a script,
  style, image, font, or making a `fetch()`/`XHR` to any external origin —
  the actual "someone injected a `<script src="https://evil">`" attack.
  `frame-ancestors 'none'` blocks clickjacking. `object-src 'none'` blocks
  plugin-based attacks. `base-uri`/`form-action 'self'` block base-tag and
  form-hijack redirection tricks.
- **Weakened by `'unsafe-inline'` on script-src**: an attacker who found a
  way to inject an inline `<script>` tag (there is currently no known
  injection point) would have it execute — CSP's inline-script protection
  specifically is not in effect.
- **A stronger option exists, not implemented tonight**: per-page SHA-256
  hashes of each inline script (`script-src 'self' 'sha256-...'`) would
  close that gap without `'unsafe-inline'` — but every hotel page's
  JSON-LD hash is unique to that hotel's data, so a single static
  `_headers` file can't express it (Cloudflare Pages `_headers` does
  support per-path rules, but one unique hash per hotel page across
  15,749+ static pages is not a "simplicity"-priority fix, CLAUDE.md §1).
  The real fix, if this is ever worth tightening, is nonces generated at
  request time — which needs a Cloudflare Pages Function (SSR), a bigger
  architecture change than a night-mission header tweak. Flagged for a
  future decision, not attempted here.
