// docs/seo-policy.md §6: "Sitemap contains exactly the indexable set; split
// by type (sitemap-static/cities/hotels.xml); noindex URLs never
// included." Every URL here is filtered to `publication_status ===
// 'indexable'` (hotels) or an explicit indexable-static-page allowlist —
// never "every page that exists". scripts/seo_assertions.py's build-time
// CI check re-derives this same set from the JSON data and diffs it
// against the built XML, so a mismatch fails the build, not just a review.
import { SITE_URL } from './site';

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
