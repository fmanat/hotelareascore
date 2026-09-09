#!/usr/bin/env python3
"""verify-prod: read-only checks against the LIVE deployed site
(night mission #2, TACHE 1 -- the "Bloc E" tooling, brought forward
because everything else needs it).

Safe to run any time: GET requests only, no auth, no state change.
staycontext.com is currently in "invisible mode" (docs/STATE.md,
docs/adr/008) -- every flag that would make anything indexable is OFF, so
this script's job is to prove the site stays that way: noindex everywhere,
robots.txt disallowing everything, no sitemap reachable, HTTPS/HSTS
correct, canonicals point at the real domain, a nonsense path 404s, and
apex/www + http/https redirect correctly. It also surfaces (never
enforces) what the CSP-Report-Only policy would have blocked, by
static-diffing the page's own inline <script> blocks against the shipped
policy -- no browser, no report collector (none is wired up, on purpose:
that needs a new service, out of scope).

Exit code is non-zero if anything unexpected is found. Run:
    make verify-prod
    python3 scripts/verify_prod.py [--base-url https://staycontext.com]
"""
from __future__ import annotations

import argparse
import re
import ssl
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field

try:
    import certifi

    SSL_CONTEXT = ssl.create_default_context(cafile=certifi.where())
except ImportError:  # macOS python.org builds sometimes ship no CA bundle
    SSL_CONTEXT = ssl.create_default_context()

DEFAULT_BASE_URL = "https://staycontext.com"
APEX_HOST = "staycontext.com"

# One representative path per page type/state (docs/adr/013's 3 hotel-page
# states + the other templates) -- real slugs from the committed data
# snapshot (web/src/data, web/public/data), not fixtures.
SAMPLE_PATHS: dict[str, str] = {
    "home": "/",
    "hotel (static subset)": "/hotel/1-2-346b137c",
    "hotel (limited/long-tail card)": "/hotel/limited?slug=hotel-701a3bb0&city=bangkok",
    "city": "/city/london",
    "compare": "/compare",
    "methodology": "/methodology",
    "legal-notice": "/legal-notice",
    "privacy": "/privacy",
    "affiliate-disclosure": "/affiliate-disclosure",
    "terms": "/terms",
}

SITEMAP_PATHS = ["/sitemap.xml", "/sitemap-static.xml", "/sitemap-cities.xml", "/sitemap-hotels.xml"]

ROBOTS_RE = re.compile(r'<meta\s+name="robots"\s+content="([^"]*)"', re.IGNORECASE)
CANONICAL_RE = re.compile(r'<link\s+rel="canonical"\s+href="([^"]*)"', re.IGNORECASE)
INLINE_SCRIPT_RE = re.compile(r"<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>", re.IGNORECASE | re.DOTALL)


@dataclass
class Fetched:
    status: int
    headers: dict[str, str]
    body: str
    elapsed_s: float
    error: str | None = None


@dataclass
class Check:
    task: str
    name: str
    ok: bool
    detail: str


RESULTS: list[Check] = []


def record(task: str, name: str, ok: bool, detail: str) -> None:
    RESULTS.append(Check(task, name, ok, detail))


def fetch(base: str, path: str, *, follow_redirects: bool = True) -> Fetched:
    url = base.rstrip("/") + path
    req = urllib.request.Request(url, headers={"User-Agent": "verify-prod/1.0 (+staycontext.com ops)"})

    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, *args, **kwargs):
            return None

    https_handler = urllib.request.HTTPSHandler(context=SSL_CONTEXT)
    handlers = [https_handler] if follow_redirects else [https_handler, NoRedirect()]
    opener = urllib.request.build_opener(*handlers)
    start = time.monotonic()
    try:
        with opener.open(req, timeout=15) as resp:
            elapsed = time.monotonic() - start
            body = resp.read(300_000).decode("utf-8", errors="replace")
            return Fetched(resp.status, {k.lower(): v for k, v in resp.headers.items()}, body, elapsed)
    except urllib.error.HTTPError as e:
        elapsed = time.monotonic() - start
        body = e.read(300_000).decode("utf-8", errors="replace") if e.fp else ""
        return Fetched(e.code, {k.lower(): v for k, v in (e.headers or {}).items()}, body, elapsed)
    except Exception as e:  # noqa: BLE001 -- network layer, report anything as a failure
        elapsed = time.monotonic() - start
        return Fetched(0, {}, "", elapsed, error=str(e))


def check_page_samples(base: str) -> None:
    for label, path in SAMPLE_PATHS.items():
        f = fetch(base, path)
        if f.error or f.status != 200:
            record("noindex-sample", label, False, f"GET {path} -> status={f.status} error={f.error}")
            continue

        m = ROBOTS_RE.search(f.body)
        content = m.group(1).strip().lower() if m else None
        ok = content is not None and content.startswith("noindex")
        record(
            "noindex-sample", label, ok,
            f"robots meta = {content!r}" if m else "no <meta name=\"robots\"> found",
        )

        c = CANONICAL_RE.search(f.body)
        canon_ok = c is not None and c.group(1).startswith(f"https://{APEX_HOST}")
        record(
            "canonicals", label, canon_ok,
            f"canonical = {c.group(1) if c else None!r}",
        )

        record("response-time", label, f.elapsed_s < 3.0, f"{f.elapsed_s:.2f}s")


def check_robots_txt(base: str) -> None:
    f = fetch(base, "/robots.txt")
    if f.error or f.status != 200:
        record("robots.txt", "reachable", False, f"status={f.status} error={f.error}")
        return

    # Cloudflare's own "Managed robots.txt" / AI Crawl Control zone feature
    # can serve ITS OWN content-signals robots.txt at the edge -- this is
    # NOT web/src/pages/robots.txt.ts's output, and it explicitly ALLOWS
    # general crawlers ("User-agent: * ... Allow: /"), only disallowing
    # named AI bots. If this is what's being served, the site-level
    # Disallow-all check below is checking the wrong document entirely --
    # flagged as its own finding rather than silently passing/failing.
    is_cf_managed = "Cloudflare Managed content" in f.body or "Content-Signal:" in f.body
    record(
        "robots.txt", "served by our origin, not a Cloudflare-managed fallback", not is_cf_managed,
        "body contains Cloudflare's own Content-Signal/managed-robots block, not robots.txt.ts's output"
        if is_cf_managed else "no Cloudflare-managed marker found",
    )

    # Our own robots.txt.ts emits exactly "User-agent: *\nDisallow: /\n"
    # while PUBLIC_INDEXING_ENABLED is off -- nothing else, no exceptions,
    # no Sitemap: line. Checked strictly (not just "contains a Disallow:
    # line somewhere") so a Cloudflare-managed document that mixes
    # Allow:/ for '*' with per-bot Disallow: lines is correctly failed,
    # not accidentally matched.
    disallows_all = re.search(r"^Disallow:\s*/\s*$", f.body, re.MULTILINE) is not None
    star_block_m = re.search(r"User-agent:\s*\*\s*\n(.*?)(?:\n\s*\n|\nUser-agent:|\Z)", f.body, re.IGNORECASE | re.DOTALL)
    allows_star = star_block_m is not None and re.search(r"^Allow:\s*/", star_block_m.group(1), re.MULTILINE | re.IGNORECASE) is not None
    has_sitemap_line = "Sitemap:" in f.body
    record(
        "robots.txt", "disallows everything for User-agent: *",
        disallows_all and not allows_star,
        f.body.strip().replace("\n", " | ")[:300],
    )
    record("robots.txt", "no Sitemap: line while indexing is off", not has_sitemap_line, f.body.strip()[:200])


def check_no_sitemap_exposed(base: str) -> None:
    for path in SITEMAP_PATHS:
        f = fetch(base, path)
        # sitemapResponse() (web/src/lib/sitemap.ts) returns a bare 404 with
        # an empty body while PUBLIC_INDEXING_ENABLED is off -- but since
        # that route then has NO file written to dist/ at all (Astro skips
        # writing output for a 404-status static response), the live edge
        # never actually serves that empty body: an unmatched path on
        # Cloudflare Pages goes through ITS OWN 404 handling instead --
        # our real 404.html (web/src/pages/404.astro) once one exists,
        # confirmed live 2026-09-09 after the platform incident settled.
        # So the real invariant is "404 status AND not actual sitemap
        # content" -- a real body (our 404 page) is fine, sitemap-shaped
        # XML content or a 200 is the leak this guards against.
        looks_like_sitemap = "<urlset" in f.body or "<loc>" in f.body or "<sitemapindex" in f.body
        ok = f.status == 404 and not looks_like_sitemap
        record(
            "no-sitemap-exposed", path,
            ok, f"status={f.status} body_len={len(f.body)} looks_like_sitemap={looks_like_sitemap}",
        )


def check_https_and_hsts(base: str) -> None:
    f = fetch(base, "/")
    hsts = f.headers.get("strict-transport-security")
    record("headers", "HSTS present", hsts is not None, f"Strict-Transport-Security = {hsts!r}")
    if hsts:
        max_age_ok = "max-age=" in hsts and not re.search(r"max-age=0\b", hsts)
        record("headers", "HSTS max-age set (>0)", max_age_ok, hsts)
        record("headers", "HSTS includes includeSubDomains", "includesubdomains" in hsts.lower(), hsts)

    xcto = f.headers.get("x-content-type-options")
    record("headers", "X-Content-Type-Options: nosniff", xcto == "nosniff", f"{xcto!r}")

    ref_pol = f.headers.get("referrer-policy")
    record("headers", "Referrer-Policy present", ref_pol is not None, f"{ref_pol!r}")

    perm_pol = f.headers.get("permissions-policy")
    record("headers", "Permissions-Policy present", perm_pol is not None, f"{perm_pol!r}")

    csp_ro = f.headers.get("content-security-policy-report-only")
    record("headers", "CSP-Report-Only present", csp_ro is not None, f"{csp_ro!r}")
    csp_enforced = f.headers.get("content-security-policy")
    record(
        "headers", "CSP not enforced yet (Report-Only stage only)", csp_enforced is None,
        f"Content-Security-Policy (enforced) = {csp_enforced!r}",
    )


def check_csp_report_only_violations(base: str) -> None:
    """No browser/report collector available -- statically diffs each
    sampled page's own inline <script> blocks against the shipped
    script-src policy, which is the actual thing script-src 'self' (no
    'unsafe-inline') would flag. style-src is intentionally
    'self' 'unsafe-inline' already (astro.config.mjs inlines 100% of CSS
    by design), so it is not re-flagged here."""
    f = fetch(base, "/")
    csp = f.headers.get("content-security-policy-report-only", "")
    if not csp:
        record("csp-violations", "policy fetched", False, "no CSP-Report-Only header on /")
        return
    script_src_strict = "script-src 'self'" in csp and "'unsafe-inline'" not in csp.split("script-src")[1].split(";")[0]
    if not script_src_strict:
        record("csp-violations", "script-src as shipped", True, "script-src already permits inline; nothing to report")
        return

    for label, path in SAMPLE_PATHS.items():
        page = fetch(base, path)
        if page.error or page.status != 200:
            continue
        inline_scripts = [
            m for m in INLINE_SCRIPT_RE.findall(page.body)
            if m.strip() and "application/ld+json" not in page.body[: page.body.find(m)][-200:]
        ]
        jsonld_blocks = re.findall(r'<script[^>]*type="application/ld\+json"[^>]*>', page.body, re.IGNORECASE)
        n_inline_js = len(re.findall(r"<script(?![^>]*\btype=\"application/ld\+json\")(?![^>]*\bsrc=)", page.body, re.IGNORECASE))
        if n_inline_js or jsonld_blocks:
            record(
                "csp-violations", label, False,
                f"{n_inline_js} inline <script> block(s) + {len(jsonld_blocks)} JSON-LD block(s) "
                "would be BLOCKED by script-src 'self' if enforced (Report-Only: logged, not blocked)",
            )
        else:
            record("csp-violations", label, True, "no inline script/JSON-LD on this page")


def check_404(base: str) -> None:
    f = fetch(base, "/this-path-does-not-exist-zzz-verify-prod")
    record("404", "nonsense path returns 404", f.status == 404, f"status={f.status}")


def check_redirects(base: str) -> None:
    apex = f"https://{APEX_HOST}"
    www = f"https://www.{APEX_HOST}"
    http_apex = f"http://{APEX_HOST}"
    http_www = f"http://www.{APEX_HOST}"

    f = fetch(www, "/", follow_redirects=False)
    loc = f.headers.get("location", "")
    ok = f.status in (301, 308) and loc.startswith(apex)
    record("redirects", "https www -> apex", ok, f"status={f.status} location={loc!r}")

    f = fetch(http_apex, "/", follow_redirects=False)
    loc = f.headers.get("location", "")
    ok = f.status in (301, 308) and loc.startswith(apex)
    record("redirects", "http apex -> https apex", ok, f"status={f.status} location={loc!r}")

    # Found 2026-09-09: http://www currently serves a 200 with an UNRELATED
    # OVHcloud "Site en construction" placeholder page -- not a redirect,
    # not our Cloudflare Pages deployment, not even the same origin as
    # https://www (which 521s like the apex). Checked separately from the
    # https-www case above because it's a genuinely different failure mode
    # (wrong content served, not "no content").
    f = fetch(http_www, "/", follow_redirects=False)
    loc = f.headers.get("location", "")
    is_wrong_origin = "ovhcloud" in f.body.lower() or "site en construction" in f.body.lower()
    ok = f.status in (301, 308) and loc.startswith(apex)
    detail = f"status={f.status} location={loc!r}"
    if is_wrong_origin:
        detail += " -- body looks like an OVHcloud placeholder page, not this site"
    record("redirects", "http www -> https apex", ok, detail)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    args = parser.parse_args()
    base = args.base_url

    check_page_samples(base)
    check_robots_txt(base)
    check_no_sitemap_exposed(base)
    check_https_and_hsts(base)
    check_csp_report_only_violations(base)
    check_404(base)
    check_redirects(base)

    by_task: dict[str, list[Check]] = {}
    for r in RESULTS:
        by_task.setdefault(r.task, []).append(r)

    n_fail = sum(1 for r in RESULTS if not r.ok)
    print(f"verify-prod against {base}\n")
    for task, checks in by_task.items():
        print(f"[{task}]")
        for c in checks:
            mark = "OK  " if c.ok else "FAIL"
            print(f"  {mark} {c.name}: {c.detail}")
        print()

    print(f"{len(RESULTS) - n_fail}/{len(RESULTS)} checks passed.")
    return 1 if n_fail else 0


if __name__ == "__main__":
    sys.exit(main())
