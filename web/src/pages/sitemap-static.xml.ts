import type { APIRoute } from 'astro';
import { sitemapResponse, urlsetXml } from '../lib/sitemap';

// Mirrors compute_publication.py's STATIC_PAGES_INDEXABLE -- keep in sync
// by hand (same convention as lib/types.ts vs webdata.py). Home and
// methodology are the only static pages currently recorded as indexable;
// the 4 legal pages start in 'draft' (Bloc C item 5) and compare.astro is
// permanently noindex by design.
const INDEXABLE_STATIC_PATHS = ['/', '/methodology'];

export const GET: APIRoute = () => sitemapResponse(urlsetXml(INDEXABLE_STATIC_PATHS));
