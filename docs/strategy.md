# strategy.md — product thesis, phases, commercial model, owner matters

> Condensed from the original §1–7, 22–23, 35–39, 45, 53–54, with the phase
> plan amended (Phase 0bis inserted) and an owner legal checklist added.

## 1. Thesis & promise

Booking sites answer price/rooms/service/availability; they answer poorly:
**"Is this hotel actually in the right location for the kind of stay I
want?"** We are an independent hotel-location intelligence layer — "before you
book, understand the surroundings." Mental models: credit score for a hotel
location; nutrition label for surroundings. Useful in < 15 seconds.

We complement Booking/Expedia (discover there → verify here → click out to
book). Acquisition targets **verification intent**, narrower and more
defensible than "hotel booking" — IF demand validation (docs/validation.md)
confirms it exists.

**Not:** an affiliate listicle blog, review scraper, travel magazine, thin
programmatic directory, fake noise product, safety/crime rater (MVP), price
comparator (MVP).

Brand language: surroundings, location fit, area score, walkability, transit
access, quietness proxy, nearby essentials, data confidence. Never: safe,
silent, best, perfect, guaranteed, exact noise level.

## 2. Journeys

A. Check a hotel (home → autocomplete on OUR index → result: identity, map,
scores, verdict, confidence, facts, city comparison, persona fit, CTA).
B. Compare 2–4 hotels (major conversion page).
C. Choose an area (city pages from aggregate data, not AI travel prose).
D. Personas: Quiet Sleep / First-Time Tourist / Car-Free / Family / Nightlife /
Balanced — reweighting presentation, never changing facts.

Result-page order: identity → verdict sentence ("Excellent for walking and
restaurants; strong transit; active surroundings" beats "82/100") → six scores
→ persona selector → why-facts → map → city comparison → comparable hotels →
CTA → methodology/confidence. Value before affiliate buttons, always.

## 3. Metrics

North star: **useful hotel-location checks completed per day** (valid hotel +
sufficient-confidence report + successful view). Traffic is not the north
star. Business: visits, searches, success rate, outbound CTR, EPC/RPM,
returns, shares, compare usage, cost per 1k checks. SEO: per
`docs/seo-policy.md §5` plus standard GSC set.

Trajectory (planning model, never forced): Stage A validation 10–15 cities /
30–70 indexable URLs + pilot hotel cohort; Stage B 20–30 cities, 500–2,000
visits/day; Stage C 40–80 cities, 2,000–10,000 visits/day. Reality check: the
10k/day ambition assumes the pilot cohort works AND link acquisition happens;
treat Stage B as the success bar, Stage C as upside.

## 4. Launch scope

English only; locales strictly on evidence. ~12 seed cities (London, Paris,
New York, Rome, Barcelona, Amsterdam, Lisbon, Tokyo, Bangkok, Singapore,
Dubai, Sydney — provisional), finalized by a Launch City Score (demand, hotel
density, affiliate value, data quality, competition, diversity,
differentiation usefulness). 12 strong cities > 100 mediocre ones.

MVP must-haves: home, autocomplete, 10–15 cities, precomputed metrics, 6
scores + confidence, persona switcher, result page, 2-hotel compare, city page
template, methodology, data sources, about, analytics, SEO controls, monthly
refresh pipeline, tests, Cloudflare deploy, Supabase/PostGIS, CI.
Explicit not-MVP: accounts, app, reviews, prices, booking, routing, safety
score, measured noise, AI chat, 20 languages, 100 cities, mass hotel
indexing, crowdsourcing.

## 5. Phase plan (amended)

- **0 — repo & ADRs** (scaffold, ADR-001…005, CI, env template)
- **0bis — demand validation** ← NEW, gate before everything heavy
  (`docs/validation.md`; kill/pivot/go recorded in STATE.md)
- **1 — data proof**: 2 cities (London + Bangkok — contrasting urban
  patterns), full pipeline to scores, CLI (`make ingest/score/validate`),
  Data Proof Report (cities, hotels, POIs, rejects, dupe rate, median
  confidence, anomalies, top-10 suspicious, est. monthly cost, next action).
- **2 — product proof**: home/autocomplete/result/persona/methodology on 2
  cities; owner inspects 15–20 outputs.
- **3 — launch dataset**: ~12 cities, golden set, calibration + sensitivity
  (`docs/scoring.md §4`).
- **4 — SEO launch**: city pages, sitemap/canonicals/robots/structured data,
  GSC, **pilot hotel cohort indexable** (`docs/seo-policy.md §2`), affiliate
  flag OFF.
- **5 — commercial test**: apply to programs, one provider first, measure
  result→click; matching coverage gate (`docs/affiliate-matching.md §4`).
- **6 — growth automation**: weekly GSC loop, cohort expansion rules, page
  retirement, city-expansion scoring, localization detection.

Go/no-go checkpoints: ~8 weeks post-Phase-4 (indexing normal? impressions
growing? checks completed? if impressions ≈ 0: diagnose, don't generate);
~3 months (expand cities only if usage + impressions + stable data + cost
controlled); ~6 months (traffic without revenue → intent/CTA work, compare
flow, provider test, B2B widget, ads last).

## 6. Commercial model & future options

Priority: hotel affiliate clickouts → relevant travel affiliate → B2B
API/widget → ads only after meaningful traffic → sponsored placements only if
visually separate from scores. Never gate the score behind a click. Max 1–2
monetization experiments at once (track CTA copy/position, provider, city,
persona).

Moat (in order of realism): normalized hotel/POI dataset; versioned
methodology + score history; city baselines; internal demand data; comparison
graph; topical authority; embeddable scores/API.
Future: neighborhood intelligence API (`lat,lng,persona → scores`), embeddable
hotel widget, browser extension, white-label — all post-fit only. If Phase
0bis lands on PIVOT, the API/widget path may move forward in priority.

## 7. Trust & ethics (non-negotiable)

Public methodology; scores cannot be bought; sponsored content visually
separate; corrections accepted; no fabricated precision; quietness clearly a
proxy; no safety claims without a separate validated methodology; no
discrimination via sensitive demographic proxies. Transparency pages
(`/methodology`, `/data-sources`) exist from Phase 2; every score page shows
version, data date, confidence, dimension meanings, limitations, and the
standard disclosure ("Scores are calculated automatically from geospatial
data… They describe the surrounding area, not hotel rooms or service
quality."). Link acquisition: data studies (substantive, methodology,
downloadable data, owner-approved) and a branded embeddable badge later —
never hidden keyword-rich links, never link schemes.

## 8. Owner legal checklist (owner homework — not Claude's decisions)

Decide before public launch (Phase 4); none of it blocks Phases 0–3:
1. ~~**Legal vehicle** for the site and its revenue~~ — **decided
   2026-09-07: FrenchSquare Ltd** (existing UK Ltd), `docs/adr/011`. The 4
   legal-page templates below already name it; items 2-5 still need real
   placeholder values (company number, address, contact, dates) filled in.
2. **Mentions légales / imprint** — an FR-based publisher of a worldwide site
   needs editor identity, host, contact (French LCEN requirements apply to the
   publisher regardless of audience language).
3. **Privacy & cookies (GDPR/ePrivacy)** — MVP design avoids accounts and
   unnecessary cookies; Cloudflare Web Analytics is cookieless; BUT affiliate
   outbound tagging and any future consent-requiring tech must be reviewed
   before enabling. Privacy page required at launch.
4. **Affiliate disclosure** page/notice (also a program requirement).
5. **Terms of use** incl. score-accuracy disclaimer and correction mechanism.
6. Data-source attribution page (already in product scope).
Claude's role: draft templates for 2–5 for owner review; flag anything that
requires professional advice rather than answering it.
