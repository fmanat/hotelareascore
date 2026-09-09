import type { APIRoute } from 'astro';
import { CITY_PAGES } from '../lib/data';
import { sitemapResponse, urlsetXml } from '../lib/sitemap';

// Fixed night mission #2 Tache 3: this used to hardcode `[]` with a comment
// claiming every city was noindex -- true when written, but it never would
// have responded to a future page_publication change, the same gap
// city/[id].astro had until 2026-09-07 (see that file's comment). Reads
// CITY_PAGES's recorded publication_status directly, same pattern as
// sitemap-hotels.xml.ts's `ALL_HOTELS.filter(...)` -- exactly the indexable
// set, nothing else, never "every city page that exists" (CLAUDE.md hard
// rule 2).
const paths = Object.values(CITY_PAGES)
  .filter((c) => c.publication_status === 'indexable')
  .map((c) => `/city/${c.city_id}`);

export const GET: APIRoute = () => sitemapResponse(urlsetXml(paths));
