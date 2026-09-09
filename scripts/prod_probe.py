#!/usr/bin/env python3
"""One probe cycle for the Cloudflare Pages intermittent-outage incident
(night mission #3, Tache 1) -- appends one CSV row per checked URL to
docs/reports/incident-2026-09-09-cloudflare-pages/probe.log. Meant to be
run in a loop (`scripts/prod_probe_loop.sh`), not directly in normal use.

Checks exactly the 4 URLs the mission specified: the two "does the origin
answer at all" signals (home, a path that has never existed), the one
sitemap endpoint (also proves robots/indexing state hasn't flipped), and
the *.pages.dev URL (proves whether an issue is custom-domain-specific or
platform-wide, per Cloudflare's own dashboard note: "if the Cloudflare
support message told you every Pages project on this account returns 503
on its own *.pages.dev URL, then zone configuration is not involved").

Read-only GETs, no state change, no auth, no dashboard interaction --
measure and log only, per this session's explicit instruction not to
"fix" anything that depends on the platform being down.
"""
from __future__ import annotations

import csv
import ssl
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

try:
    import certifi

    SSL_CONTEXT = ssl.create_default_context(cafile=certifi.where())
except ImportError:
    SSL_CONTEXT = ssl.create_default_context()

ROOT = Path(__file__).resolve().parents[1]
LOG_PATH = ROOT / "docs" / "reports" / "incident-2026-09-09-cloudflare-pages" / "probe.log"

URLS = [
    "https://staycontext.com/",
    "https://staycontext.com/chemin-inexistant-probe",
    "https://staycontext.com/sitemap-static.xml",
    "https://staycontext.pages.dev/",
]


def probe_one(url: str) -> tuple[int, str, str]:
    """Returns (status, cf_ray, error). status=0 means the request itself
    failed (DNS/TLS/connect/timeout) -- distinct from a real HTTP status
    the server chose to send back."""
    req = urllib.request.Request(url, headers={"User-Agent": "stayconext-incident-probe/1.0"})
    opener = urllib.request.build_opener(urllib.request.HTTPSHandler(context=SSL_CONTEXT))
    try:
        with opener.open(req, timeout=10) as resp:
            return resp.status, resp.headers.get("cf-ray", ""), ""
    except urllib.error.HTTPError as e:
        return e.code, (e.headers or {}).get("cf-ray", ""), ""
    except Exception as e:  # noqa: BLE001 -- log anything as a probe failure, never crash the loop
        return 0, "", str(e)[:200]


def main() -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    is_new = not LOG_PATH.exists()
    ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    with open(LOG_PATH, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if is_new:
            w.writerow(["timestamp_utc", "url", "status", "cf_ray", "error"])
        for url in URLS:
            status, cf_ray, error = probe_one(url)
            w.writerow([ts, url, status, cf_ray, error])
    print(f"{ts} probed {len(URLS)} URLs")


if __name__ == "__main__":
    sys.exit(main())
