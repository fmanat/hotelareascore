import type { APIRoute } from 'astro';
import { sitemapIndexXml } from '../lib/sitemap';

// Sitemap index (docs/seo-policy.md §6: "split by type").
export const GET: APIRoute = () => new Response(
  sitemapIndexXml(['/sitemap-static.xml', '/sitemap-cities.xml', '/sitemap-hotels.xml']),
  { headers: { 'Content-Type': 'application/xml; charset=utf-8' } },
);
