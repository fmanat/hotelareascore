import type { APIRoute } from 'astro';
import { ALL_HOTELS } from '../lib/data';
import { sitemapResponse, urlsetXml } from '../lib/sitemap';

// docs/seo-policy.md §6: exactly the indexable set, nothing else --
// filtered on the recorded page_publication decision
// (hotel.publication_status), never "every hotel page that was built."
const paths = ALL_HOTELS.filter((h) => h.publication_status === 'indexable').map((h) => `/hotel/${h.slug}`);

export const GET: APIRoute = () => sitemapResponse(urlsetXml(paths));
