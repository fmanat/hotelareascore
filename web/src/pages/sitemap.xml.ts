import type { APIRoute } from 'astro';
import { sitemapIndexXml, sitemapResponse } from '../lib/sitemap';

// Sitemap index (docs/seo-policy.md §6: "split by type"). 404s while
// PUBLIC_INDEXING_ENABLED is off -- see sitemapResponse's comment.
export const GET: APIRoute = () => sitemapResponse(
  sitemapIndexXml(['/sitemap-static.xml', '/sitemap-cities.xml', '/sitemap-hotels.xml']),
);
