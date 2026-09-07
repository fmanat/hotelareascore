// Brand/domain decided 2026-09-07 (docs/adr/012): StayContext,
// staycontext.com (owned). This is the ONLY place a base URL is defined —
// update here, once, if it ever changes. Sitemap/canonical/JSON-LD all
// read this constant, but it stays inert in practice regardless of its
// value: with PUBLIC_INDEXING_ENABLED off, nothing referencing this URL is
// ever served with an index,follow robots tag or listed in a submitted
// sitemap.
export const SITE_URL = 'https://staycontext.com';
