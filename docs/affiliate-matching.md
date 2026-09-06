# affiliate-matching.md — hotel entity resolution ↔ affiliate inventory

> This is the missing link in the original plan. 100% of affiliate revenue
> depends on turning OUR hotel (from Overture, noisy) into a deep link to the
> PARTNER's hotel record (Tripadvisor / Expedia / other). Without a match, the
> CTA is at best a generic search link with worse conversion.

## 1. The problem

- Overture lodging POIs contain duplicates, stale/closed hotels, missing
  hotels, imprecise names ("Hilton" vs "Hilton London Bankside").
- Affiliate programs identify hotels by their own IDs; deep links require
  that ID (or a slug/URL containing it).
- There is no shared key. Matching = entity resolution on
  name + geo + address + brand.

## 2. Data model additions

### `affiliate_providers`
`id, name, program_type, deeplink_template, terms_url, active`

### `hotel_affiliate_links`
- `hotel_id` (FK hotels)
- `provider_id` (FK affiliate_providers)
- `provider_hotel_id`
- `provider_url`
- `match_method` — enum: exact_id / name_geo_high / name_geo_fuzzy / manual /
  search_fallback
- `match_confidence` 0–100
- `verified_at`, `last_checked_at`, `status` (active / broken / retired)
- unique `(hotel_id, provider_id)`

### CTA resolution rule (runtime, precomputed like everything else)
- match_confidence ≥ 85 → deep link "See rates at {provider}"
- 60–84 → deep link allowed only after manual spot-check (pilot cohort:
  always spot-check)
- < 60 or no match → fallback: provider search URL pre-filled with
  `hotel name + city` (still tagged, lower conversion) — or no CTA.
Never deep-link to the wrong hotel: a wrong-hotel CTA destroys trust and can
breach program terms. When in doubt, fall back to search link.

## 3. Matching pipeline (ETL, per provider)

Inputs: our canonical hotels; provider inventory (via feed, API, or — if
neither is offered at our tier — provider sitemap/search results within the
program's permitted usage; check terms first, log the method).

Cascade, stop at first success:
1. provider ID present in a licensed feed with coordinates → distance ≤ 150 m
   AND normalized-name similarity ≥ 0.9 → `exact_id`-class match (conf 95+).
2. normalized name similarity ≥ 0.85 AND distance ≤ 250 m AND same city →
   `name_geo_high` (conf 80–95, scaled by both signals).
3. brand + city + fuzzy name ≥ 0.7 AND distance ≤ 400 m → `name_geo_fuzzy`
   (conf 55–80) → queue for manual review, never auto-activate ≥ pilot.
4. else → `search_fallback` or none.

Normalization before comparison: lowercase, strip diacritics, drop stopwords
("hotel", "the", city name), expand brand aliases (map maintained in
`data/config/brand-aliases.yml`).

QA: weekly link-health check on active links (HTTP status + page still
resolves to a hotel entity); broken → status=broken, CTA falls back
automatically. Report match-rate per city in the monthly data report.

## 4. Success metric

`monetizable coverage` = % of pilot-cohort hotels with an active
conf-≥85 deep link. Target ≥ 80% for the cohort before enabling
`AFFILIATE_ENABLED`. If a city can't reach ~60% coverage across providers,
flag it — its commercial value assumption may be wrong.

## 5. Program eligibility & sequencing (chicken-and-egg)

Reality: Tripadvisor/Expedia-class programs typically review applicants and
favor live sites with traffic. Plan for rejection-then-retry:

1. Phase 4: launch WITHOUT affiliate (flag off). Site must be fully useful
   unmonetized — this is also our editorial-independence story.
2. Apply to programs at Phase 5 start, with the live site + traffic snapshot.
   Apply to 2–3 (one aggregator-style network as backup — e.g. Travelpayouts-
   class networks aggregate Booking/Agoda/etc. and accept smaller sites; terms
   to be validated at implementation time, do not hardcode any program).
3. If rejected everywhere: interim = untagged outbound links (still useful to
   users, measures CTR as if monetized) + reapply at higher traffic. The
   `outbound_clicks` table works identically with or without tags, so the
   funnel is measurable from day one.
4. Never let a program's content requirements dictate score content
   (independence rule in `docs/strategy.md`).

## 6. Explicit non-goals

No price display, no availability checking, no booking engine, no scraping of
provider inventory beyond permitted matching use. Prices/availability change
per-request and would violate both our cost rules and most program terms.
