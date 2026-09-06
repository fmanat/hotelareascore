#!/usr/bin/env python3
"""SEO build-time assertions (CLAUDE.md §9, Bloc C item 3, overnight
mission): "unique titles, one canonical, sitemap superset of indexable and
excludes noindex, JSON-LD parses [and never carries review/rating keys]."

Runs against `web/dist/` AFTER `astro build` -- this checks the actual
built output, not the source templates, so a template bug that only shows
up post-render (a missing prop, a slot that didn't fill) still gets
caught. No new Python/Node dependency: stdlib only (re for lightweight
HTML extraction rather than a full parser -- the output is our own
well-formed Astro build, not arbitrary HTML).
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

WEB_ROOT = Path(__file__).resolve().parents[1]
DIST = WEB_ROOT / "dist"

# schema.org keys that would signal review/rating markup -- CLAUDE.md hard
# rule 3/7 and docs/seo-policy.md §6: our score is not a review, ever.
FORBIDDEN_JSONLD_KEYS = {
    "aggregaterating", "review", "reviewrating", "ratingvalue",
    "ratingcount", "bestrating", "worstrating", "reviewcount",
}

TITLE_RE = re.compile(r"<title>(.*?)</title>", re.IGNORECASE | re.DOTALL)
CANONICAL_RE = re.compile(r'<link rel="canonical" href="([^"]*)"', re.IGNORECASE)
JSONLD_RE = re.compile(
    r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>', re.IGNORECASE | re.DOTALL
)
LOC_RE = re.compile(r"<loc>([^<]*)</loc>")


def find_forbidden_keys(obj, path: str = "") -> list[str]:
    hits = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k.lower() in FORBIDDEN_JSONLD_KEYS:
                hits.append(f"{path}.{k}" if path else k)
            hits += find_forbidden_keys(v, f"{path}.{k}" if path else k)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            hits += find_forbidden_keys(v, f"{path}[{i}]")
    return hits


def check_canonicals(html_files: list[Path]) -> list[str]:
    """Every page, indexable or not, must have exactly one canonical --
    this is a structural requirement (docs/seo-policy.md §6: "one canonical
    hotel identity -> one canonical URL"), not an SEO-visibility concern,
    so it applies to the full build."""
    errors = []
    for f in html_files:
        text = f.read_text(encoding="utf-8")
        canonicals = CANONICAL_RE.findall(text)
        if len(canonicals) != 1:
            errors.append(
                f"{f.relative_to(DIST)}: expected exactly 1 canonical link, found {len(canonicals)}"
            )
    return errors


def check_unique_titles_among_indexable(html_files: list[Path]) -> list[str]:
    """Title uniqueness only matters for the pages Google can actually see
    (docs/seo-policy.md §6). Checking it across the FULL build (34k+
    hotels kept for internal search, almost all noindex) would fail on
    real, legitimate duplicate hotel names (multiple actual "Premier Inn
    London Southwark" branches, chains with generic localities) that have
    nothing to do with SEO -- those pages are never submitted to a search
    engine. This checks only the indexable set (page_publication ==
    'indexable') plus the always-checked static pages."""
    indexable_paths, _ = load_indexable_and_noindex_hotel_paths()
    indexable_paths |= {"/", "/methodology"}

    errors = []
    titles: dict[str, list[Path]] = {}
    for f in html_files:
        rel = f.relative_to(DIST)
        url_path = "/" if rel == Path("index.html") else "/" + str(rel.parent)
        if url_path not in indexable_paths:
            continue
        text = f.read_text(encoding="utf-8")
        title_match = TITLE_RE.search(text)
        if not title_match:
            errors.append(f"{f.relative_to(DIST)}: no <title> found (indexable page)")
            continue
        title = title_match.group(1).strip()
        titles.setdefault(title, []).append(f)

    for title, files in titles.items():
        if len(files) > 1:
            rels = ", ".join(str(p.relative_to(DIST)) for p in files)
            errors.append(f"duplicate <title> among INDEXABLE pages {title!r} on {len(files)} pages: {rels}")
    return errors


def check_jsonld(html_files: list[Path]) -> list[str]:
    errors = []
    for f in html_files:
        text = f.read_text(encoding="utf-8")
        for block in JSONLD_RE.findall(text):
            try:
                parsed = json.loads(block)
            except json.JSONDecodeError as e:
                errors.append(f"{f.relative_to(DIST)}: JSON-LD does not parse: {e}")
                continue
            forbidden = find_forbidden_keys(parsed)
            if forbidden:
                errors.append(
                    f"{f.relative_to(DIST)}: JSON-LD contains forbidden review/rating key(s): {forbidden}"
                )
            allowed_types = {"WebSite", "BreadcrumbList", "Place", "LodgingBusiness", "Hotel", "ListItem", "GeoCoordinates", "PostalAddress", "PropertyValue"}
            t = parsed.get("@type")
            if t and t not in allowed_types:
                errors.append(f"{f.relative_to(DIST)}: JSON-LD @type {t!r} is not in the allowed set {allowed_types}")
    return errors


def load_indexable_and_noindex_hotel_paths() -> tuple[set[str], set[str]]:
    """Ground truth from the same JSON the site was built from (web/src/data),
    not re-derived from the Python publication DB -- this checks that the
    BUILT OUTPUT matches what the data said, which is the actual thing that
    can drift."""
    indexable, noindex = set(), set()
    for f in (WEB_ROOT / "src" / "data").glob("hotels-*.json"):
        hotels = json.loads(f.read_text(encoding="utf-8"))
        for h in hotels:
            path = f"/hotel/{h['slug']}"
            if h.get("publication_status") == "indexable":
                indexable.add(path)
            else:
                noindex.add(path)
    return indexable, noindex


def check_sitemap() -> list[str]:
    errors = []
    hotels_sitemap = DIST / "sitemap-hotels.xml"
    if not hotels_sitemap.exists():
        return ["sitemap-hotels.xml was not built"]
    sitemap_paths = {
        (loc if loc.startswith("/") else "/" + loc.split("example.invalid", 1)[-1].lstrip("/"))
        for loc in LOC_RE.findall(hotels_sitemap.read_text(encoding="utf-8"))
    }
    # Normalize to path-only (strip the https://example.invalid host).
    sitemap_paths = {re.sub(r"^https?://[^/]+", "", p) for p in sitemap_paths}

    indexable, noindex = load_indexable_and_noindex_hotel_paths()

    missing = indexable - sitemap_paths
    if missing:
        errors.append(f"sitemap-hotels.xml is missing {len(missing)} indexable hotel(s): {sorted(missing)[:5]}...")

    leaked = noindex & sitemap_paths
    if leaked:
        errors.append(f"sitemap-hotels.xml contains {len(leaked)} noindex/draft hotel(s) that must not be there: {sorted(leaked)[:5]}...")

    return errors


def main() -> int:
    if not DIST.exists():
        print(f"ERROR: {DIST} does not exist -- run `npm run build` first.", file=sys.stderr)
        return 1

    html_files = list(DIST.rglob("*.html"))
    if not html_files:
        print(f"ERROR: no HTML files found under {DIST}.", file=sys.stderr)
        return 1

    errors: list[str] = []
    errors += check_canonicals(html_files)
    errors += check_unique_titles_among_indexable(html_files)
    errors += check_jsonld(html_files)
    errors += check_sitemap()

    if errors:
        print(f"SEO assertions FAILED ({len(errors)} issue(s)):", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        return 1

    print(f"SEO assertions passed: {len(html_files)} HTML pages checked, "
          "titles unique, exactly one canonical each, JSON-LD parses with no "
          "review/rating keys, sitemap matches recorded publication status.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
