// Client-side capture for the two events docs/data-and-costs.md §2 already
// reserves serving-DB tables for (`search_events`, `outbound_clicks`) and
// docs/STATE.md commits to (`search_events` as the Phase 4 per-city
// coverage KPI) -- night mission #3, Tache 4. Scaffolding only: the shapes
// below are what the eventual Supabase tables would receive, but there is
// nowhere real to send them yet.
//
// SENDING IS ALWAYS OFF TODAY, independent of FLAGS.ANALYTICS_ENABLED:
// `dispatch()` never makes a network request -- there is no
// `search_events`/`outbound_clicks` endpoint to send to (Supabase isn't
// provisioned, docs/STATE.md; the storage destination itself is an open
// owner decision, docs/reports/analytics-storage-options.md). The flag
// only controls whether a captured event is even logged to the console
// for local-dev visibility. When a storage decision is made and a real
// endpoint exists, `dispatch()` is the one function that needs to change
// -- every call site (recordSearchEvent/recordOutboundClick) stays the
// same, same pattern as publication.py's `_upsert` (single seam for the
// eventual backend swap).
import { FLAGS } from './flags';

export interface SearchEvent {
  kind: 'search_event';
  query: string;
  result_count: number;
  ts: string;
}

export interface OutboundClickEvent {
  kind: 'outbound_click';
  hotel_slug: string;
  target: string;
  tagged: boolean;
  ts: string;
}

type CapturedEvent = SearchEvent | OutboundClickEvent;

function dispatch(event: CapturedEvent): void {
  if (!FLAGS.ANALYTICS_ENABLED) return;
  // TODO(docs/reports/analytics-storage-options.md): once the owner picks
  // a storage destination, replace this with the real send (fetch/beacon
  // to that destination). Never add a network call here without that
  // decision being made first -- CLAUDE.md hard rule 1 (new dependency
  // needs cost documented) and this session's explicit "no active
  // sending" instruction.
  // eslint-disable-next-line no-console
  console.debug('[events] (not sent -- no storage destination configured yet)', event);
}

/** docs/STATE.md "Phase 4 commitment: search_events as the coverage KPI"
 * -- a search with result_count === 0 is exactly what that KPI counts. */
export function recordSearchEvent(query: string, resultCount: number): void {
  dispatch({ kind: 'search_event', query, result_count: resultCount, ts: new Date().toISOString() });
}

/** docs/data-and-costs.md §2 "outbound_clicks... works identically with or
 * without tags" (docs/affiliate-matching.md §5) -- `tagged` records which
 * case this was, once real (affiliate or not) outbound links exist
 * (AFFILIATE_ENABLED, still off -- CtaSection.astro has no real link to
 * attach this to yet). */
export function recordOutboundClick(hotelSlug: string, target: string, tagged: boolean): void {
  dispatch({ kind: 'outbound_click', hotel_slug: hotelSlug, target, tagged, ts: new Date().toISOString() });
}
