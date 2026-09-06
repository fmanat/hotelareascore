import type { APIRoute } from 'astro';
import { urlsetXml } from '../lib/sitemap';

// Empty today: every city page is recorded noindex
// (compute_publication.py, docs/seo-policy.md §3 "not yet measured
// against real search demand"). Still generated as its own typed sitemap
// so the machinery is real and testable, not stubbed -- Bloc C item 4.
export const GET: APIRoute = () => new Response(urlsetXml([]), {
  headers: { 'Content-Type': 'application/xml; charset=utf-8' },
});
