# ADR-001 — Astro static-first on Cloudflare Pages/Workers

- **Status:** accepted (Phase 0)
- **Date:** 2026-09-06
- **Decision recorded from:** CLAUDE.md §5, docs/data-and-costs.md §6

## Context

The product is a read-heavy content/tool site: hotel result pages, city pages,
a search box, a compare view. Traffic ambition (up to 10k visits/day at Stage
C) must be served within a ≤ €50/month budget, ideally ≤ €35 steady-state.
The runtime budget forbids per-view external calls; pages are rebuildable from
precomputed data.

## Decision

- **Astro + TypeScript**, static-first output. React islands only where
  interactivity is genuinely needed (autocomplete, persona switcher, compare,
  map). Minimal client JS everywhere else.
- **Cloudflare Pages** for static hosting, **Workers** for the two runtime
  queries (search, result), **R2** for snapshots/PMTiles. Start on free tiers.

## Rationale

- Static pages make the marginal cost of a page view ≈ 0 and keep us honest
  about the runtime budget (no accidental server dependency creep).
- Astro's islands model matches the "mostly content, few interactive spots"
  shape; a full SPA framework would invert the cost/complexity profile.
- Cloudflare free tier covers Stage A/B volumes; the paid escalation path
  (Workers ~$5/mo) is documented and cheap (docs/data-and-costs.md §2).

## Alternatives considered

- **Next.js on Vercel:** heavier default JS, pricing less predictable at
  10k/day, SSR temptation works against the precompute rule.
- **Pure SSG (Hugo/Eleventy) + separate API:** cheap, but autocomplete/compare
  need a thin dynamic layer anyway; Astro gives both in one build system.
- **SvelteKit:** viable, but islands + ecosystem maturity on Astro fits better
  and the team standard is TypeScript/React idioms.

## Consequences

- Framework migration requires a new ADR (CLAUDE.md §5).
- Build pipeline must regenerate changed pages on data refresh (monthly) —
  build time is a watched cost, not a runtime one.
- E2E tests target the static output + Workers endpoints (CLAUDE.md §9).
