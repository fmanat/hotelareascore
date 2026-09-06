// docs/seo-policy.md §6. Inert while FLAGS.PUBLIC_INDEXING_ENABLED is off
// (overnight mission Bloc C: "tout inerte tant que PUBLIC_INDEXING_ENABLED
// est OFF") -- this is the actual kill switch: when the flag is off,
// EVERY crawler is disallowed from EVERYTHING, which makes the sitemap's
// content moot regardless of what page_publication says. When the flag is
// on, this defers entirely to each page's own robots meta tag (already
// correct per-page — see BaseLayout.astro) and only points crawlers at the
// sitemap index.
import type { APIRoute } from 'astro';
import { FLAGS } from '../lib/flags';
import { SITE_URL } from '../lib/site';

export const GET: APIRoute = () => {
  const body = FLAGS.PUBLIC_INDEXING_ENABLED
    ? `User-agent: *\nAllow: /\nSitemap: ${new URL('/sitemap.xml', SITE_URL).toString()}\n`
    : `User-agent: *\nDisallow: /\n`;
  return new Response(body, { headers: { 'Content-Type': 'text/plain; charset=utf-8' } });
};
