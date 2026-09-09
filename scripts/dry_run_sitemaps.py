#!/usr/bin/env python3
"""Dry-run sitemaps for the go-live package (night mission #2, Tache 3).

Generates what sitemap-static/cities/hotels.xml WOULD contain if the
staged 'draft' set (home, methodology, all 12 cities, the 200-hotel pilot
cohort v2 -- scripts/compute_publication.py) were flipped to 'indexable',
WITHOUT touching any served path, any flag, or the real page_publication
decisions. Output goes to docs/reports/dry-run-sitemaps/ -- not under
web/public or web/dist, never built, never served, never crawlable.

Also writes a consistency report (docs/reports/go-live-sitemap-dry-run-report.md):
every URL this would put in a sitemap must resolve to an ACTUAL built page
in the committed data snapshot (docs/adr/013's static subset) -- a cohort
hotel staged for go-live with no real page would be a broken canonical the
moment PUBLIC_INDEXING_ENABLED flips, so this is checked here, before that
ever happens, not discovered after.

Run: python3 scripts/dry_run_sitemaps.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from hotelareascore import publication  # noqa: E402

SITE_URL = "https://staycontext.com"
WEB_SRC_DATA = ROOT / "web" / "src" / "data"
OUT_DIR = ROOT / "docs" / "reports" / "dry-run-sitemaps"
REPORT_PATH = ROOT / "docs" / "reports" / "go-live-sitemap-dry-run-report.md"

# Mirrors web/src/pages/sitemap-static.xml.ts's hand-maintained
# INDEXABLE_STATIC_PATHS -- kept in sync by hand, same convention, same
# caveat: if that file's array ever changes, this one needs updating too.
STATIC_PATHS = ["/", "/methodology"]


def urlset_xml(paths: list[str]) -> str:
    urls = "\n".join(f"  <url><loc>{SITE_URL}{p}</loc></url>" for p in paths)
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"{urls}\n</urlset>\n"
    )


def sitemap_index_xml(sitemap_paths: list[str]) -> str:
    entries = "\n".join(f"  <sitemap><loc>{SITE_URL}{p}</loc></sitemap>" for p in sitemap_paths)
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"{entries}\n</sitemapindex>\n"
    )


def load_static_hotel_ids_by_id() -> dict[str, dict]:
    """id -> full hotel record, from the COMMITTED static-subset export
    (web/src/data/hotels-*.json, docs/adr/013) -- this is the actual set
    of hotels with a real built page today, independent of what
    page_publication currently says."""
    by_id: dict[str, dict] = {}
    for f in WEB_SRC_DATA.glob("hotels-*.json"):
        for h in json.loads(f.read_text(encoding="utf-8")):
            by_id[h["id"]] = h
    return by_id


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    report_lines: list[str] = []
    issues: list[str] = []

    with publication.connect() as con:
        draft_hotel = publication.list_by_status(con, "draft", "hotel")
        cohort_rows = [r for r in draft_hotel if r["decided_by"] == "system:pilot_cohort_selection"]
        draft_city = publication.list_by_status(con, "draft", "city")
        draft_static = publication.list_by_status(con, "draft", "static")

    static_by_id = load_static_hotel_ids_by_id()

    # --- hotels: cohort id -> real slug, only if a real page exists ---
    hotel_paths: list[str] = []
    for r in cohort_rows:
        rec = static_by_id.get(r["page_id"])
        if rec is None:
            issues.append(
                f"Cohort hotel {r['page_id']} has NO record in the committed static-subset "
                "export (web/src/data/hotels-*.json) -- would be a broken canonical if flipped "
                "to indexable without a built page."
            )
            continue
        if not rec.get("has_static_page"):
            issues.append(
                f"Cohort hotel {r['page_id']} ({rec.get('slug')}) is in the export but "
                "has_static_page is false -- inconsistent with docs/adr/013's guarantee."
            )
            continue
        hotel_paths.append(f"/hotel/{rec['slug']}")

    # --- cities: id is already the slug/route segment ---
    city_pages_path = WEB_SRC_DATA / "city-pages.json"
    city_pages = json.loads(city_pages_path.read_text(encoding="utf-8")) if city_pages_path.exists() else {}
    city_paths: list[str] = []
    for r in draft_city:
        if r["page_id"] not in city_pages:
            issues.append(f"City {r['page_id']} is staged draft but has no entry in city-pages.json.")
            continue
        city_paths.append(f"/city/{r['page_id']}")

    # --- static: home/methodology only (compare/legal are not sitemap
    # candidates -- compare is permanently noindex by design, legal pages
    # are draft for a different reason, docs/STATE.md open decision (a)) ---
    staged_static_ids = {r["page_id"] for r in draft_static}
    static_paths = [p for p in STATIC_PATHS if (p.strip("/") or "home") in (staged_static_ids | {"home"})]
    if set(STATIC_PATHS) - set(static_paths):
        issues.append(f"Static paths {set(STATIC_PATHS) - set(static_paths)} are not staged draft; check compute_publication.py.")

    (OUT_DIR / "sitemap-static.xml").write_text(urlset_xml(static_paths), encoding="utf-8")
    (OUT_DIR / "sitemap-cities.xml").write_text(urlset_xml(city_paths), encoding="utf-8")
    (OUT_DIR / "sitemap-hotels.xml").write_text(urlset_xml(hotel_paths), encoding="utf-8")
    (OUT_DIR / "sitemap.xml").write_text(
        sitemap_index_xml(["/sitemap-static.xml", "/sitemap-cities.xml", "/sitemap-hotels.xml"]), encoding="utf-8"
    )

    total_urls = len(static_paths) + len(city_paths) + len(hotel_paths)

    report_lines.append("# Go-live sitemap dry run — consistency report\n")
    report_lines.append(
        "Generated by `scripts/dry_run_sitemaps.py` (night mission #2, Tache 3). "
        f"Output XML: `docs/reports/dry-run-sitemaps/` -- not served, not built, not crawlable.\n"
    )
    report_lines.append("## Counts\n")
    report_lines.append(f"- Static pages: {len(static_paths)} (expected 2: home, methodology)")
    report_lines.append(f"- City pages: {len(city_paths)} (expected 12)")
    report_lines.append(f"- Hotel pages: {len(hotel_paths)} (staged cohort: {len(cohort_rows)})")
    report_lines.append(f"- **Total sitemap URLs if flipped today: {total_urls}**\n")
    report_lines.append("## Consistency issues\n")
    if issues:
        for i in issues:
            report_lines.append(f"- **ISSUE:** {i}")
    else:
        report_lines.append("None. Every staged URL resolves to a real built page in the committed snapshot.")
    report_lines.append("")
    report_lines.append("## Caveat: sitemap route files are hand-maintained, not auto-derived\n")
    report_lines.append(
        "`web/src/pages/sitemap-static.xml.ts` hardcodes its path list by hand "
        "(same convention this script mirrors above) -- `sitemap-cities.xml.ts` was "
        "fixed this session to read `CITY_PAGES` dynamically instead (it previously "
        "hardcoded `[]`), matching `sitemap-hotels.xml.ts`'s existing pattern. "
        "If the go-live cohort or static-page list ever changes, update "
        "`sitemap-static.xml.ts` and this script together."
    )
    REPORT_PATH.write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    print(f"Wrote {OUT_DIR}/sitemap-{{static,cities,hotels}}.xml + sitemap.xml")
    print(f"Wrote {REPORT_PATH}")
    print(f"\n{len(static_paths)} static + {len(city_paths)} city + {len(hotel_paths)} hotel = {total_urls} URLs")
    if issues:
        print(f"\n{len(issues)} consistency issue(s) found -- see {REPORT_PATH}", file=sys.stderr)
        return 1
    print("No consistency issues.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
