# STATE.md — project state tracker

> Claude Code: read this first every session; update it whenever phase,
> decisions, or blockers change. Keep it under ~150 lines — this is a
> dashboard, not a journal. Move resolved history to `docs/adr/` or delete it.

## Current phase

**Phase 3 — launch dataset (~12 cities), golden set, calibration** (see
`docs/strategy.md §5`). Plan **approved by owner 2026-09-06** with 3
amendments (2-batch ingestion, 2-wave golden set, blind/mobile-first
labeling tool) — see [`docs/reports/phase-3-plan.md`](reports/phase-3-plan.md).

**All 12 launch cities now ingested/scored/validated** (Batch 1 + Batch 2,
see sections below). Golden-set labeling tool source at
`tools/golden-labeler/` (blind, mobile-first, CSV export,
`db`+`downloads` capabilities), full 50-hotel selection versioned at
`tests/golden/selection.json`; published Artifact link in chat, not
reproduced here. **Owner is labeling now.** Next: collect the 50 labels
(export or `read_db`), run the sensitivity analysis (`docs/scoring.md §4.3`),
freeze `score_version` for launch.

Phase 2 gate: ✅ closed 2026-09-06. Phase 1 Data Proof Report: accepted
2026-09-06 ([report](reports/data-proof-report-2026-08-19.0.md)).

## Phase gate status

| Phase | Gate | Status |
|---|---|---|
| 0 — repo & ADRs | ADR-001…005 merged, CI green | ✅ committed & pushed 2026-09-06 (github.com/fmanat/hotelareascore) |
| 0bis — demand validation | Kill criteria evaluated, owner GO recorded | ✅ **GO recorded 2026-09-06** (see decision log below) |
| 1 — data proof (2 cities) | Data Proof Report accepted by owner | ✅ **accepted 2026-09-06** |
| 2 — product proof | Owner inspected 15–20 hotel outputs | ✅ **closed 2026-09-06** |
| 3 — launch dataset (~12 cities) | Golden set built, calibration done | ▶ current — all 12 cities ingested, golden set (50 hotels) selected, owner labeling in progress |
| 4 — SEO launch (incl. pilot hotel cohort) | Pilot cohort live, GSC connected | ☐ |
| 5 — commercial test | First affiliate integrated, clicks measured | ☐ |
| 6 — growth automation | Weekly GSC loop producing PRs | ☐ |

## Open owner decisions

- [ ] Domain/brand name (blocking public launch, not blocking Phases 1–2)
- [ ] Legal vehicle & jurisdiction for the site and affiliate revenue
      (`docs/strategy.md §8` — owner homework)

## Entity QA — done this session (items a-d)

All 4 items from the bounded pre-Phase-3 task are implemented and live in
Batch 1's data (full detail: `docs/reports/phase-3-batch-1-ingestion-report.md`):

- **(a)** `src/hotelareascore/entity_qa.py` — name-pattern non-hotel
  exclusion, wired into `ingest.py`. Took 3 iterations against real Batch 1
  data (see module docstring for the false-positive history — "tower"/
  "design" markers wrongly excluded real hotels, up to 3.3% of Dubai's
  candidates, before removal). **Known limitation: effectively English-market
  only** — near-zero recall on French/Italian/Japanese/Arabic business
  names. Every exclusion logged in full per city (`manifest.json`).
- **(b)** `validate.py` flags purely-numeric and empty hotel names
  (`n_numeric_name`).
- **(c)** Every hotel now carries `distance_from_center_km` +
  `far_from_center` (>15 km, `webdata.py`); result pages show an honest
  disclosure instead of implying "in London" etc. Batch 1 bboxes also
  deliberately tightened (`cities.yml`). London itself: 928 hotels (20.8%)
  are >15 km from center — not re-ingested (Phase 2 closed), but now
  disclosed.
- **(d)** `nearby_facts_display_exclude` in `taxonomy-mapping.yml` — pet
  services, personal coaching, delivery services no longer clutter the
  "Why?" section; walkability_density's SCORE predicate is unchanged.

**Blind-labeling rule** added to `docs/scoring.md §4.1` per owner
instruction: the labeling tool never shows our scores/verdict/reason codes.

## Entity QA backlog — not started (5 specimens, from golden-set labeling)

Found while Claude labeled the golden set (`tests/golden/LABELS-PROVENANCE.md`
§"Data-quality specimens"), left IN the calibration (labels judge the pin,
per the tool's own rule) but each needs a real fix before any indexable
cohort:

- **`2bf89f8c…` 桝本屋酒店 (Tokyo)** — almost certainly a **liquor shop**, not
  a hotel (酒店 = "sake shop" in Japanese, "hotel" only in Chinese). Textbook
  case of the documented English-only limitation (item a above): the current
  heuristic has no CJK vocabulary at all, so this is a false *inclusion* the
  existing exclusion logic structurally cannot see. Any CJK-market fix needs
  its own language-specific marker list, not a patch to the English one.
- **`346a49c0…` アクアプレイス旭湯 (Tokyo)** — looks like a **bathhouse/sento**
  (旭湯), possibly with lodging attached. Same CJK-blind-spot family as above;
  verify on the ground before it enters any indexable cohort.
- **`a9b48284…` Souq Madinat Jumeirah (Dubai)** — a souk/venue, not a hotel.
  English name, in scope for the existing heuristic, but genuinely not
  caught: **confirmed by reading `entity_qa.py` — "souq"/"souk" is simply
  absent from `_NON_HOTEL_MARKER_TERMS`**, not a matching bug. A coverage gap
  from Batch 1's mostly-European city mix; add it as a marker (with the
  Batch-1-lesson word-boundary discipline) before Middle-East cities get any
  indexable cohort.
- **`b2a1e3f4…` "Holiday Inn Paris Charles de Gaulle S.A.R.L." (Paris)** — a
  corporate-entity record; the name says CDG airport, the pin is at Porte de
  Charenton (SE Paris, ~25 km away). Looks like a legal-entity/HQ record
  Overture attached hotel-adjacent taxonomy to, not a bookable property.
- **`756a9130…` SpringHill Suites (New York)** — pin is in Carlstadt, New
  Jersey, inside the "New York" bbox (5-borough box is wide enough to catch
  nearby NJ). **Confirmed by direct measurement: 13.6 km from the New York
  center point — under the 15 km `far_from_center` threshold (item c above),
  so today's disclosure would NOT catch it.** A real gap: "far from center"
  and "wrong state/metro area entirely" are different failure modes: the
  same 13.6 km can be an outer borough (expected, fine) or a different U.S.
  state (not what a "New York hotel" listing should show without a much
  louder flag). Needs its own check, not a smaller radius.

## Batch 2 (New York, Singapore) — DONE 2026-09-06

Owner green-lit Batch 2 off the coverage report's recommendation. Ingested,
scored, validated (bboxes tightened per the Batch 1 lesson —
`data/config/cities.yml`) —
[ingestion report](reports/phase-3-batch-2-ingestion-report.md). **All 12
Phase 3 launch cities are now ingested; cumulative volumetry (~131 MB) landed
within 0.5% of the plan's ~130 MB estimate.** A 4th entity-QA false-positive
class surfaced and was fixed (see next section). Golden-set wave 2 (8
New York/Singapore hotels, `tests/golden/selection.json`) added and the
labeling tool republished — **owner's wave-1 labels confirmed preserved**
(verified via `read_db` before/after: `state/order` unchanged, still 42
ids, until the next page load merges in the new 8 automatically).

## Phase 4 commitment: `search_events` as the coverage KPI (owner decision, 2026-09-06)

No automatic "rejected lodging" rescue rule will be built off blind sampling
(Bangkok's 58% noise rate makes that too risky — `docs/reports/phase-3-coverage-bangkok-nyc.md`).
**In exchange:** once the live site is up (Phase 4), `search_events`
(searches with no matching hotel) becomes the per-city coverage KPI. If it
shows real user demand concentrated on specific missing hotels, the rescue
rule gets reconsidered against that actual-demand data — not another
sampling pass. Whoever picks up Phase 4 SEO-launch work: wire this metric
in from the start, it's a decision input, not an afterthought.

## Decisions taken (pointers, not prose)

- 2026-09-06 — **Phase 0bis GO** (owner: Jean; `rapport-decision-phase-0bis.md`);
  ADR-001…005 drafted; Phase 1 pipeline built and run (4,463 London + 7,558
  Bangkok hotels, €0 cost) — **report accepted**; Phase 2 Astro site built
  (`web/`, static-first). **Owner code audit** then found and fixed a real
  `transit_access` bug (DuckDB `least()` swallowing NULL, scoring 100
  instead of 0 — `score_version` → `1.0.1`, 414/1,960 hotels moved exactly
  −20 pts, [diff report](reports/score-diff-1.0.0-proof-to-1.0.1.md)) plus a
  self-contradictory-verdict bug and a scoring.md doc/code drift — **Phase 2
  gate closed**. Phase 3 plan researched (10 candidates, no ingestion) and
  presented ([plan](reports/phase-3-plan.md)).
- 2026-09-06 — **Owner approved the Phase 3 plan** with 3 amendments
  (2-batch ingestion, 2-wave golden set, blind/mobile-first tool). Entity QA
  (a)-(d) implemented (see section above). Batch 1 (8 cities) ingested,
  scored, validated — [ingestion report](reports/phase-3-batch-1-ingestion-report.md).
  Golden-set tool built (`db` capability, blind, mobile-first, keyboard
  shortcuts, shuffled order, "can't judge" skip) and published with 42
  Batch-1 candidates loaded, stratified by score/confidence/chain-vs-
  independent plus 2 deliberate calm-vs-nightlife tension cases (Tokyo). Not
  yet reviewed by owner.
- 2026-09-06 — **Owner audit round 2** (before labeling starts): (1) tool
  export + source committed — CSV export (`downloads` capability, copy-paste
  fallback), `tools/golden-labeler/` source + `tests/golden/selection.json`
  committed and versioned, Artifact republished with `db`+`downloads`. (2)
  Coverage check (the real Batch 2 precondition, not the entity-QA fix) —
  hand-classified 100 rejected-lodging records (50 Bangkok + 50 New York):
  ~10-16% look like real miscategorized lodging, ~46-58% genuine noise
  (public housing, real-estate agencies, street-address artifacts), rest
  ambiguous. Recommendation: Batch 2 OK to proceed as-is; a rescue rule is a
  scoped follow-up, not a blocker. (3) Logged (not fixed): brand-allowlist
  short-circuit lets 33 hotel sub-venues (restaurant/spa/bar/parking/
  ballroom sharing a parent brand name, e.g. "Royal Princess Dusit
  Restaurant") through across the 10 ingested cities.
- 2026-09-06 — **Owner green-lit Batch 2** off the coverage report. New
  York + Singapore ingested/scored/validated (tightened bboxes) —
  [report](reports/phase-3-batch-2-ingestion-report.md); **all 12 cities
  done**, cumulative volumetry ~131 MB (within 0.5% of the ~130 MB
  estimate). Found and fixed a 4th entity-QA bug in the process: "union"/
  "mosque"/"bank"/"church"/"temple" collided with real street/square names
  ("W New York – Union Square", "Wink @ Mosque Street") — now guarded
  against a following street-type word, "union" dropped outright. Owner
  decision: no automated "rejected lodging" rescue rule now; `search_events`
  becomes the Phase 4 coverage KPI instead (see section above). Golden-set
  wave 2 (8 hotels) added, tool republished with wave-1 labels confirmed
  intact (verified via `read_db`).
- **Scope decision, not asked to the owner (ordinary engineering):** `web/`
  is NOT wired into CI — its build needs the gitignored, network-fetched ETL
  output, which would make CI slow and non-reproducible across monthly
  Overture releases. Add web CI (fixture-data-based `astro check` + build) as
  its own task before Phase 4 deployment work.

## Blockers / risks being watched

- **AI Overviews (unmeasured):** validation could not observe whether Google
  AI Overviews already answer cluster-2 queries. Mitigation: owner spot-check
  when convenient; mandatory AI-Overview column in the day-90 cohort
  measurement (`docs/seo-policy.md §5`). If AI Overviews cleanly answer the
  majority of tracked cluster-2 queries → execute PIVOT path
  (`docs/validation.md §3`).
- No search-volume data was available in Phase 0bis (SERP composition only);
  treat all traffic projections as unvalidated priors.
- Affiliate program eligibility likely requires a live site with traffic —
  sequencing in `docs/affiliate-matching.md §5`.
- Supabase free-tier fit depends on keeping POIs out of the serving DB —
  `docs/data-and-costs.md §2`.

## Cost tracker (update monthly)

| Month | Est. recurring € | Main driver | Notes |
|---|---:|---|---|
| 2026-09 | 0 | — | validation + Phases 1–3, all 12 launch cities, all free tiers (docs/reports/phase-3-batch-2-ingestion-report.md) |

## Last session summary

- 2026-09-06 — Phase 0bis → Phase 1 → Phase 2 (owner audit fixed a real
  scoring bug, `score_version 1.0.1`) → **gate closed**. Phase 3 plan
  approved with 3 amendments. Entity QA (a)-(d) implemented (3 iterations to
  get item (a) safe). Batch 1 (8 cities) ingested/scored/validated — real
  volumetry within 6% of estimate. Golden-set tool built.
- Same day, before labeling started: **owner audit round 2** required (1)
  CSV export + committed tool source (`tools/golden-labeler/`,
  `tests/golden/selection.json`) before any labels could safely leave the
  Artifact, and (2) a coverage check on Bangkok/New York's rejected-lodging
  buckets as the *real* Batch 2 precondition (not the entity-QA fix, which
  only cleans the included set). Both done: tool republished with
  `db`+`downloads`, [coverage report](reports/phase-3-coverage-bangkok-nyc.md)
  recommends Batch 2 is OK to proceed as-is. Also logged: the brand-allowlist
  short-circuit lets ~33 hotel sub-venues through (not fixed).
- Same day: **owner green-lit Batch 2**. New York + Singapore ingested,
  scored, validated (tightened bboxes) — **all 12 launch cities now done**,
  cumulative volumetry ~131 MB (within 0.5% of the ~130 MB estimate). Found
  and fixed a 4th entity-QA bug along the way ("union"/"mosque"/"bank"/
  "church"/"temple" colliding with real street/square names — see
  `entity_qa.py` and the Batch 2 report). Owner decision: no automated
  rescue rule for rejected-lodging now; `search_events` becomes the Phase 4
  coverage KPI instead. Golden-set wave 2 (8 hotels) added to the 50-hotel
  selection; tool republished with wave-1 labels verified intact via
  `read_db` before and after. **Owner is labeling now.** Next: collect the
  50 labels when ready (export, or `read_db` next session), run the
  sensitivity analysis (`docs/scoring.md §4.3`), freeze `score_version`.
