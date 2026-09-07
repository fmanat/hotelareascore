// docs/seo-policy.md §6: "Sitemap contains exactly the indexable set; split
// by type (sitemap-static/cities/hotels.xml); noindex URLs never
// included." Every URL here is filtered to `publication_status ===
// 'indexable'` (hotels) or an explicit indexable-static-page allowlist —
// never "every page that exists". scripts/seo_assertions.py's build-time
// CI check re-derives this same set from the JSON data and diffs it
// against the built XML, so a mismatch fails the build, not just a review.
import { FLAGS } from './flags';
import { SITE_URL } from './site';

// Found during the staycontext.com "invisible mode" preflight (2026-09-07):
// robots.txt already treats PUBLIC_INDEXING_ENABLED as the absolute kill
// switch (disallows everything, and omits the Sitemap: line, when it's
// off) -- but the 4 sitemap endpoints themselves had no such check, only
// filtering by each page's own recorded publication_status. That meant a
// direct request to /sitemap-static.xml or /sitemap-hotels.xml would still
// list real page URLs (home, methodology, the pilot-cohort hotel pages)
// even with every flag off and every page's robots meta correctly saying
// noindex -- reachable by direct URL guess, not just robots.txt discovery.
// Every sitemap response now goes through this: 404, nothing in the body,
// whenever the flag is off, regardless of what page_publication says --
// the same "flag overrides the recorded decision" rule robots.txt already
// enforces, just applied here too.
export function sitemapResponse(xml: string): Response {
  if (!FLAGS.PUBLIC_INDEXING_ENABLED) {
    return new Response(null, { status: 404 });
  }
  return new Response(xml, { headers: { 'Content-Type': 'application/xml; charset=utf-8' } });
}

export function urlsetXml(paths: string[]): string {
  const urls = paths
    .map((p) => `  <url><loc>${new URL(p, SITE_URL).toString()}</loc></url>`)
    .join('\n');
  return `<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n${urls}\n</urlset>\n`;
}

export function sitemapIndexXml(sitemapPaths: string[]): string {
  const entries = sitemapPaths
    .map((p) => `  <sitemap><loc>${new URL(p, SITE_URL).toString()}</loc></sitemap>`)
    .join('\n');
  return `<?xml version="1.0" encoding="UTF-8"?>\n<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n${entries}\n</sitemapindex>\n`;
}
