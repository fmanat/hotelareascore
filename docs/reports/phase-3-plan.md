# Phase 3 plan — launch dataset (~12 cities), golden set, calibration

> **STALE STATUS LINE, kept for history — Phase 3 closed 2026-09-07**
> (`docs/STATE.md`, `docs/adr/009`). The line below ("awaiting owner
> approval, no ingest run") was true when this plan was written and is
> **not true today** — all 12 cities are ingested/scored/validated on
> score_version 1.2.1. Read this document as the original proposal that
> was approved and executed, not as current status.

**Status: proposal, awaiting owner approval. No `make ingest` has been run
for any new city — every number below comes from read-only research queries
against Overture (same mechanism as `make ingest`'s own bbox extraction),
not from the pipeline itself.**

Decision needed from the owner: (1) approve the 12-city list and ingestion
order below, or amend it; (2) confirm Phase 3 stays ETL/static-only — no
Supabase account provisioned yet (see §4); (3) approve the golden-set
protocol and labeling-tool plan in §5, so it can be built once real
candidate hotels exist to put in it.

---

## 1. City list — Launch City Score

`docs/strategy.md §4` scores candidates on 7 criteria: demand, hotel
density, affiliate value, data quality, competition, diversity,
differentiation usefulness. Two are **measured** below (real Overture
queries, release `2026-08-19.0`, same release already accepted for London +
Bangkok); five are **priors** — general-knowledge judgment calls, not
validated the way Phase 0bis validated the concept overall. Flagged
accordingly; not presented as more certain than they are.

| City | Hotels found¹ | Taxonomy noise²​ | Demand³ | Competition³ | Affiliate³ | Differentiation³ | Diversity role³ |
|---|---:|---:|---|---|---|---|---|
| London ✅ | 4,463 | 14.4% | — done — | — | — | — | — |
| Bangkok ✅ | 7,558 | 59.3% ⚠ | — done — | — | — | — | — |
| Paris | 4,055 | 8.8% | High | High | High | High | Major EU capital |
| New York | 2,287 | 45.3% ⚠ | High | Very high | High | High | Major US market |
| Rome | 5,219 | 9.8% | Med-High | Med | Med-High | Med | Southern EU |
| Barcelona | 1,792 | 9.5% | High | Med-High | High | Med-High | Mediterranean/beach |
| Amsterdam | 1,152 | 8.6% | Med-High | Med | Med-High | Med | N. Europe/canal city |
| Lisbon | 1,352 | 10.8% | Med | Low-Med | Med | Med | Iberian, lower competition |
| Tokyo | 3,093 | 16.6% | High | Med | High | Very High | Asia-Pacific, non-Latin script |
| Singapore | 1,244 | 49.9% ⚠ | Med-High | Med | Med-High | Med | SE Asia hub |
| Dubai | 2,246 | 20.0% | High | Med-High | High | Med | Middle East |
| Sydney | 1,232 | 13.8% | Med-High | Med | Med | Med | Native-English, S. hemisphere |

¹ `taxonomy.primary` in the included hotel-type set, within a rough metro
bbox — order-of-magnitude only, not the bbox we'd actually ship (that gets
tuned during ingestion, same as London/Bangkok's did implicitly).
² Overture's generic/unclassified `lodging` leaf ÷ (included hotels +
that leaf) — the exact metric that flagged Bangkok in the Phase 1 report.
³ **Prior, not measured** — general-knowledge judgment, same epistemic
status as any other unvalidated v1 assumption in this project. Not a
substitute for Phase 0bis-style validation; flagged so it isn't mistaken
for one.

**Real finding worth flagging on its own:** Bangkok's generic-`lodging`
data-quality problem is **not Bangkok-specific**. New York (45.3%) and
Singapore (49.9%) show the same pattern — dense, mixed-use global cities
where Overture's upstream sources under-classify lodging far more than they
do for London/Paris/Rome/etc. (8.6–16.6%). This directly motivates running
the entity-QA task (`docs/STATE.md`) before scoring these three, not after.

**Recommendation: keep the provisional 12**, nothing in the measured data
disqualifies any of them, but **sequence ingestion in two batches**:

- **Batch 1 (8 cities, low taxonomy noise):** Paris, Rome, Barcelona,
  Amsterdam, Lisbon, Sydney, Tokyo, Dubai.
- **Batch 2 (2 cities, run only after the entity-QA taxonomy fix lands):**
  New York, Singapore.

This is a sequencing call, not a scope cut — both batches ship in Phase 3.
It just means the entity-QA taxonomy-mapping fix (item a) gets applied and
spot-checked on Batch 1 data before it's relied on for the two cities where
it matters most.

## 2. Entity QA (prerequisite, already recorded)

Full scope in `docs/STATE.md` "Bounded pre-Phase-3 task: entity QA" — not
repeated here. Runs before Batch 2 at the latest; ideally before Batch 1 too
since (a) non-hotel entities and (d) nearby-facts category noise likely
affect every city, not just the three flagged for taxonomy-noise rate.

## 3. Volumetric estimate (12 cities)

Real counts, not the Phase-0 guess in `docs/data-and-costs.md §2`:

| Table | Rows | Basis |
|---|---:|---|
| hotels | ~35,700 | sum of measured per-city counts above (London+Bangkok actual, 10 candidates measured this session) |
| hotel_scores | ~35,700–53,500 | 1–1.5× hotels (1.5× allows for one calibration re-score during Phase 3) |
| nearby_facts | ~428,000 | 12/hotel — our actual cap in `webdata.py`, not the original doc's 30/hotel assumption |
| city_score_baselines | 12 | one per city |

Applying `data-and-costs.md §2`'s own per-row size assumptions (750 B/hotel,
375 B/hotel_scores row, 125 B/nearby_facts row) to these real counts:
**≈130 MB total** — comfortably inside Supabase Free (500 MB), with *more*
headroom than that doc's original ~285 MB estimate, because our nearby_facts
cap (12/hotel) is less than half of what it assumed (30/hotel).

## 4. Scope decision for this phase: still no Supabase

Phase 2 stayed fully static (no live backend) because there was no public
site yet. Phase 3's job — build the 12-city dataset and calibrate — doesn't
need one either: it's an ETL-side scaling exercise (`make ingest/score` ×
10 new cities) plus the golden set, both of which run against local/CI
Parquet exactly like Phase 1 did. **Recommendation: defer creating the
Supabase project to Phase 4** (SEO launch — the first phase that needs a
live, queryable backend for real page views). This also sidesteps a
practical constraint: creating third-party accounts is something I can't do
on your behalf, so that step needs you regardless of when it happens — no
reason to pull it earlier than Phase 4 actually requires it.

## 5. Cost estimate

- **ETL/CI compute:** real Phase 1 timing was ~75–80 s ingest + ~25–39 s
  score per city. 12 cities ≈ 20–25 minutes/month total. This repo's CI is
  free for public repositories — **€0**.
- **Storage:** ETL world (local/CI Parquet, `docs/adr/002`) has no hosting
  cost until it lands in R2, which isn't planned before Phase 4. **€0**.
- **Serving DB:** not provisioned this phase (§4) — **€0**.
- **At 10,000 visits/day** (CLAUDE.md hard rule 1's required forward
  estimate): that traffic level implies a live site, which is Phase 4+
  scope. Deferred to the Phase 4 plan, where it can be estimated against an
  actual Supabase/Cloudflare configuration instead of a hypothetical one.
- **Total Phase 3 marginal cost: €0**, all free tiers, same as Phases 1–2.

## 6. Golden-set protocol (`docs/scoring.md §4`)

**Sampling (50 hotels, ≥5 cities — spec allows 5, this plan uses all 12 for
better city-bias coverage):** 4 hotels per city × 12 cities = 48, plus 2
extra hotels chosen for being interesting edge cases (e.g. a low-confidence
or high-taxonomy-noise example) = 50. Within each city, stratify by
balanced_score (low/mid/high spread) and by confidence (mostly High, a
couple of Medium) — the same selection method already used for the
18-hotel Phase 2 inspection sheet, reusable once real Phase 3 hotel data
exists.

**Labels (exactly the 5 in scoring.md §4.1, 1–5 scale each):** transit
convenience · nearby restaurants · major-road exposure · nightlife
intensity · park/family convenience.

**Fastest labeling format for your time (8–15 h for 250 individual
ratings):** the bottleneck isn't clicking buttons, it's recalling or
looking up each hotel's real surroundings. Proposed tool (built once Batch 1
is ingested and candidates are selected — not yet, since it needs real
hotels to hold):

- One hotel at a time, not a long scrolling form — less context-switching.
- Each screen: hotel name, city, address/locality, coordinates, and a
  **direct "Open in Google Maps" link** (a plain hyperlink — no embedded
  map, no map-provider cost) so you can drop into Street View in one click
  when you don't already know the area.
- Five 1–5 button rows (not dropdowns — one click each), number-key
  shortcuts (`1`–`5` for the focused dimension), `Enter`/`N` to advance.
  Full keyboard flow so a confident rating takes a few seconds once you've
  looked at the map.
- Progress bar (`n/50`), autosave as you go (so closing the tab mid-session
  costs nothing), export to the `tests/golden/hotels.csv` schema
  `docs/scoring.md §4.1` already specifies.
- Built as a small tool once there's real data to load into it — same
  approach as the Phase 2 inspection sheet, just interactive this time.

## 7. If approved — sequence

1. Entity-QA task (STATE.md) — taxonomy exclusion rules, name sanity checks
   in `validate.py`, bbox/locality honesty, nearby-facts category filter.
2. Ingest + score Batch 1 (8 cities), spot-check entity-QA fixes against
   real data.
3. Ingest + score Batch 2 (New York, Singapore) with the fixed taxonomy
   rules.
4. Build the golden-set labeling tool against real Batch 1+2 candidates;
   owner labels 50 hotels.
5. Sensitivity analysis (`docs/scoring.md §4.3`) — perturb constants, only
   tune where rankings actually move; freeze `score_version` for launch.
6. Report back before Phase 4 (SEO launch) work starts.
