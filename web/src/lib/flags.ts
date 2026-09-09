// Feature flags — CLAUDE.md §8: "default OFF for new/dangerous behavior."
// No `.env` exists yet (see ../../.env.example at the repo root), so every
// flag below resolves to false until an owner decision turns one on.
// Read at build time only — this is a static site, nothing re-checks these
// per request.

function flag(name: string): boolean {
  const raw = (import.meta.env as Record<string, string | boolean | undefined>)[name];
  return raw === 'true' || raw === true || raw === '1';
}

export const FLAGS = {
  PUBLIC_INDEXING_ENABLED: flag('PUBLIC_INDEXING_ENABLED'),
  HOTEL_PAGE_INDEXING_ENABLED: flag('HOTEL_PAGE_INDEXING_ENABLED'),
  AFFILIATE_ENABLED: flag('AFFILIATE_ENABLED'),
  AI_SUMMARIES_ENABLED: flag('AI_SUMMARIES_ENABLED'),
  MISSING_HOTEL_GEOCODING_ENABLED: flag('MISSING_HOTEL_GEOCODING_ENABLED'),
  MAP_ENABLED: flag('MAP_ENABLED'),
  DATA_REFRESH_ENABLED: flag('DATA_REFRESH_ENABLED'),
  SEO_AUTOMATION_ENABLED: flag('SEO_AUTOMATION_ENABLED'),
  // Night mission #3, Tache 4: gates BOTH the Cloudflare Web Analytics
  // beacon script (BaseLayout.astro) AND whether lib/events.ts's captured
  // search_events/outbound_clicks are even logged locally -- see that
  // file's comment for why "enabled" still sends nothing today.
  ANALYTICS_ENABLED: flag('ANALYTICS_ENABLED'),
} as const;
