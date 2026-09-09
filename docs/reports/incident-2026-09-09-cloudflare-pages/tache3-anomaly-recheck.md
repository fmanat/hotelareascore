# Tache 3 conditional trigger — anomaly re-check on a stable service

- **Trigger:** probe showed ≥30 continuous minutes of 200s on the home URL
  at 2026-09-09T10:12:49Z (`probe-summary.md`).
- **Action:** `make verify-prod` re-run at 10:13 UTC — **48/50 checks
  pass** (was 3/28 during the outage). Both anomalies from the prior
  session were re-measured directly.

## Anomaly 1 — `_headers` missing on the custom domain: RESOLVED, was transient

Previously: HSTS/CSP-Report-Only/Permissions-Policy present on
`staycontext.pages.dev` but absent on `staycontext.com`. Now: **all
present and identical on both**, confirmed via direct `curl -I` on
`https://www.staycontext.com/` and `https://staycontext.com/` in addition
to `verify-prod`'s own check. This was the platform incident, not a
project config gap — closing, no fix needed.

(Background research done while waiting for the trigger, kept for the
record even though not needed to close this out: Cloudflare's own docs
don't document a custom-domain-vs-pages.dev difference for `_headers`,
but it IS a real, recurring community-reported issue —
[Cloudflare Community thread](https://community.cloudflare.com/t/values-in-headers-files-arent-applying-for-custom-domain/625640)
— worth knowing if this ever recurs on a genuinely stable service.)

## Anomaly 2 — nonsense path / sitemap endpoints returning 200 with home-page HTML: RESOLVED, was transient

Previously: a nonexistent path and all 4 sitemap endpoints returned `200`
with the **home page's** HTML (title, canonical, content all matched
`/`) — looked exactly like a Cloudflare Pages SPA-fallback ("serve
index.html for unmatched routes") misconfiguration. Now: **both correctly
return 404 with our own custom 404 page** (`web/src/pages/404.astro` —
title "Page not found · StayContext", canonical `/404`).

Cloudflare's documented not-found logic (`developers.cloudflare.com/pages/configuration/serving-pages/`,
read while waiting for the trigger): a top-level `404.html` in the
deployment is looked up FIRST; only if none exists does Pages fall back to
SPA mode. `dist/404.html` has existed in every build since Tache 2 shipped
it — confirmed again just now (`npm run build` locally still produces
it). The live behavior now matches that documented logic exactly, which
is strong evidence the earlier 200-with-home-page response was the
platform incident interfering with routing (very plausibly: an in-flight
or partially-failed deployment being served, consistent with the 521s
happening around the same time), not a real project setting — closing, no
fix needed.

## Found while re-checking, not one of the two original anomalies: `verify-prod`'s own sitemap check was too strict

`check_no_sitemap_exposed` required a literal empty body on a 404 —
correct for `sitemapResponse()`'s in-app behavior, but Astro never writes
a file for a route that returns 404 at build time, so on the real edge an
unmatched path is ALWAYS handled by Cloudflare's own 404 logic (our real
404 page, with real content) — a literally empty body was never going to
be observed live. Fixed to check "404 status AND the body isn't
sitemap-shaped XML" instead of "404 status AND empty body" — this is a
tooling fix, not a site fix (`scripts/verify_prod.py`).

## Not one of the two original anomalies, still open: www doesn't redirect to apex

`https://www.staycontext.com` now correctly serves the real site (not the
OVHcloud placeholder seen over plain HTTP during the outage) with correct
headers — but it serves it directly rather than redirecting to
`https://staycontext.com`. No SEO risk today (every page's own
`<link rel="canonical">` already points at the apex, `BaseLayout.astro`),
but worth a redirect rule for cleanliness. This was already flagged in
`docs/STATE.md` from the prior session (Tache 2) as a Cloudflare dashboard
item (DNS/Bulk Redirects) — unchanged, not re-diagnosed here since it was
never part of Tache 3's two specific anomalies.

## Bottom line

Neither anomaly Tache 3 was scoped to persisted on a stable service — no
"correctif prêt à appliquer" needed, because there was nothing left to
fix once the platform stabilized. The only real code change from this
recheck is the `verify-prod` tooling fix above.
