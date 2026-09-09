# `search_events` / `outbound_clicks` storage — options for owner decision

- **Date:** 2026-09-09 (night mission #3, Tache 4)
- **Status:** scaffolding built (`web/src/lib/events.ts`,
  `ANALYTICS_ENABLED` flag), **sending stays off regardless of the flag**
  — there is no storage destination configured yet. This report is what
  the flag being turned on should eventually mean.

## Why this needs a decision now, not later

`docs/STATE.md`'s Phase 4 commitment already depends on `search_events`
being real data from day 1 of indexing ("a rescue rule gets reconsidered
only against real demand data from that metric... wire this in from the
start"). `docs/data-and-costs.md §2` reserves `search_events` and
`outbound_clicks` as Supabase serving tables — but Supabase itself isn't
provisioned yet (`docs/STATE.md`, `src/hotelareascore/publication.py`'s
own docstring). Waiting for Supabase to exist before deciding where
events go means the first weeks of real indexing produce zero KPI data —
worth deciding independently of the Supabase timeline.

## Options

### (a) Wait for Supabase (the already-planned architecture)

Ship nothing until the serving DB exists; `search_events`/
`outbound_clicks` land there per the existing schema plan.

- **Cost:** $0 extra — reuses infrastructure already decided
  (`docs/data-and-costs.md §2`), free tier.
- **Consistency:** highest — one serving DB for everything (`hotels`,
  `scores`, `page_publication`, events), one place to query/join
  event data against which hotel/city it happened in.
- **Downside:** blocks on the Supabase provisioning timeline, which has
  no date attached yet.

### (b) Cloudflare Workers Analytics Engine

A Workers-native time-series datastore (`wrangler` binding, SQL-like
query via the Analytics Engine API), designed for exactly this kind of
high-volume, low-cardinality event logging.

- **Cost:** $0 on the free tier (generous default limits for this
  volume — `docs/strategy.md §3`'s Stage B ceiling is 2,000 visits/day).
- **Consistency:** already on Cloudflare (where Pages/Workers/DNS already
  live) — no new account, only a new binding on the existing account.
  Needs a Cloudflare Pages **Function** to write to it (client can't write
  directly) — the first Function this project would ever need; today
  everything is `output: 'static'` (`astro.config.mjs`, `docs/adr/001`).
- **Downside:** a real architecture change (static-first → one dynamic
  endpoint), and a second query surface separate from Supabase once that
  exists (can't easily JOIN an Analytics Engine dataset against
  `hotels`/`scores`).

### (c) Cloudflare D1 (SQL, serverless SQLite)

A real SQL table, free tier, also via a Pages Function.

- **Cost:** $0 on the free tier at this volume.
- **Consistency:** SQL, so closer in spirit to the eventual Supabase
  table shape (`src/hotelareascore/publication.py`'s local SQLite
  stand-in for `page_publication` is the same pattern already used
  elsewhere in this repo) — a `data/serving/`-style local file could even
  be the dev/CI equivalent.
- **Downside:** same Function requirement as (b); yet another datastore
  to eventually reconcile with Supabase.

### (d) Cloudflare Web Analytics only, no custom events table

Rely entirely on Cloudflare Web Analytics's own dashboard (visits, top
pages, referrers) and skip `search_events`/`outbound_clicks` as a custom
table entirely.

- **Cost:** $0.
- **Downside:** Cloudflare Web Analytics has no concept of "a search with
  zero results" or "which hotel got clicked toward which outbound link" —
  it cannot serve `docs/STATE.md`'s coverage-KPI commitment at all. Not a
  real option for that specific need, only for generic traffic/referrer
  numbers (which it should provide either way, independent of this
  decision — CLAUDE.md §5 already names it as the analytics stack).

## Recommendation

(a) if Supabase provisioning has a near-term date; (b) or (c) as a bridge
if indexing (`docs/reports/go-live-seo-checklist.md`) is expected to start
before Supabase exists, specifically so `search_events` data isn't lost
during that gap — pick whichever of (b)/(c) matches Supabase's eventual
Postgres shape more closely (leaning (c), SQL) to make the later
migration a data copy, not a rewrite. Either way, Cloudflare Web
Analytics itself ((d)'s script) is close to free and independent of this
decision — nothing here blocks turning that on alone once a site/token
exists, only the custom events table needs this decision.

## What's already built, independent of this decision

`web/src/lib/events.ts` — `recordSearchEvent`/`recordOutboundClick`
capture the right shape today (`search_event`: query, result_count,
timestamp; `outbound_click`: hotel_slug, target, tagged, timestamp) and
are already wired at the real call site (`SearchBox.astro`'s search
callback — the actual journey-A search, not the compare pickers). The
single `dispatch()` function is the one place that changes once a
destination from the list above is picked; no call site needs to change.
