# ADR-005 — Indexability as a recorded decision; pilot hotel cohort experiment

- **Status:** accepted (Phase 0)
- **Date:** 2026-09-06
- **Decision recorded from:** docs/seo-policy.md §2, §4–6; CLAUDE.md §2 (rule 2)

## Context

The acquisition thesis targets `{hotel} location` long-tail queries, but a
blanket "hotel pages noindex" default would forfeit exactly those queries,
while blanket indexing of ~40k hotel pages is the scaled-content pattern
Google's spam systems exist to bury. The original plan carried this
contradiction unresolved.

## Decision

- **Indexability is a recorded decision** in `page_publication`
  (draft / noindex / indexable / retired) — never a side effect of a route
  existing. Sitemap = exactly the indexable set.
- Hotel pages default **noindex**, EXCEPT a **pilot cohort of 150–300 pages**
  (≈ 12–25 per launch city) promoted at Phase 4, selected only among pages
  passing all 11 gates (confidence ≥ 80, identity reliability, unique facts,
  QA, canonical integrity, … , affiliate-link-or-deliberate-no-CTA).
- Cohort composition: ~70/30 weighted toward independent/boutique hotels
  (winnable SERPs), spread across cities, biased to hotels whose data tells a
  distinctive story.
- **90-day measurement decides expansion** (docs/seo-policy.md §5):
  ≥ 20% pages with impressions and ≥ 5% with clicks → expand same-size;
  < 5% with any impressions → do NOT add pages; diagnose, and if demand
  mismatch is confirmed, execute the PIVOT path (docs/validation.md §3).

## Rationale

- The cohort converts an ideological question ("index hotel pages or not?")
  into a cheap, bounded, measurable experiment with pre-committed decision
  rules — no post-hoc rationalization.
- Independent-hotel weighting maximizes the chance of observing any signal
  within 90 days on a new domain.
- Pre-registering the < 5% failure branch protects against the classic SEO
  failure mode: generating more pages to fix pages that don't rank.

## Consequences

- Build-time SEO assertions (unique titles, one canonical, sitemap ⊇
  indexable ∧ ∌ noindex, robots, JSON-LD) become CI gates from Phase 4.
- GSC integration and per-cohort-page tracking are launch requirements, not
  nice-to-haves.
- Expansion capacity is irrelevant; only measured results move the footprint.
