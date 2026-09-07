# family_convenience v1.2.1 — pre-registered predictions + result

> Owner instruction (this session): last authorized iteration on
> family_convenience. Predictions below are recorded **before** running the
> new scoring pipeline, per instruction, so the result section can't be
> retrofitted to look better than it is.

## Pre-registered predictions (recorded before running v1.2.1 scoring)

1. Golden-50 median `family_convenience` drops from **82.3** (v1.2.0,
   `tests/golden/joined-scores-1.2.0.csv`) to roughly **60-65**.
2. The 5 hotels named in the Bloc A diagnostic stay high (**≥ 55**): Changi
   Lodge (Singapore), Crowne Plaza Rome St. Peter's, Hotel Gilinsky
   (Amsterdam), the Holiday Inn Paris CDG / Charenton pin, Lisboa Camping &
   Bungalows.
3. Spearman(`family_strict`, `family_convenience`) ≥ 0.5.

## The one fix applied (docs/adr/009)

Per-class weight on `family_convenience`'s green-space polygons (SQL CASE
in `taxonomy.family_convenience_land_weight_sql`, wired into
`scoring._family_convenience_dimension`) — nothing removed from v1.2.0's
class list, only re-weighted:

- **1.0** (unchanged): `park/*`, `protected/*`, `entertainment/zoo`,
  `recreation/playground` — designed public leisure space.
- **0.4**: `recreation/pitch`, `recreation/track`, `recreation/
  recreation_ground`, `sand/beach` — real built infrastructure, but often
  restricted-access (school/club pitches) or not itself a "walk to a park"
  amenity.
- **0.4, only if polygon area ≥ 2,000 m²; 0.0 (doesn't count) below it**:
  `managed/grass`, `grass/*`, `forest/*` — raw land cover with no designed
  leisure purpose. Chosen from the real per-city median areas (all 12
  cities, queried directly against the live v1.2.0 `green_spaces` extract,
  not guessed): `managed/grass` medians 106-2,858 m² across cities but sits
  under 300 m² in 9 of 12 — consistent with the diagnostic's own finding
  ("a patch of managed grass behind a building") — while real
  `park/park` polygons median 2,000-5,500 m² in the same cities. 2,000 m²
  is the low end of that park range, chosen to exclude slivers (street
  verges, traffic islands, small lawns) without excluding a genuinely
  sizeable grass area or copse.

Full data behind the threshold choice: area distributions queried live
against `data/etl/2026-08-19.0/*/green_spaces.parquet` for all 12 cities
(subtype/class × count × median area), not assumed from category names.
`score_version` → **1.2.1** (patch: same two-theme source and class list as
1.2.0, only the per-polygon weight changed).

## Result

Ran the full protocol: `python3 -m hotelareascore.cli score --city all`
(score_version 1.2.1, all 12 cities), `validate --city all` (all 12 pass),
`scripts/calibrate_family_strict.py`.

| Prediction | Predicted | Actual | Verdict |
|---|---|---|---|
| Golden-50 median `family_convenience` | ~60-65 | **74.3** | **wrong** — direction right (dropped from 82.3), magnitude overshot: the 0.4 partial weight still credits most hits, it doesn't zero them out, so the drop was gentler than expected |
| 5 named hotels stay ≥ 55 | all 5 | **4/5** — Charenton pin 73.6, Crowne Plaza Rome 86.6, Hotel Gilinsky 95.1, Lisboa Camping 83.4, **Changi Lodge 33.4** | **wrong for 1/5** — Changi Lodge fell below 55. Not a new problem: the Bloc A diagnostic already flagged Changi Lodge's `family_strict` label of 5/5 as very likely a labeling-construct mismatch (no real green space within radius even under the expanded v1.2.0 filter, nearest usable candidate 635m+, outside the 600m radius) — this hotel was already a known label/data disagreement, not a fix regression |
| Spearman(`family_strict`, `family_convenience`) ≥ 0.5 | ≥ 0.5 | **0.5052** | **correct, but barely** — a 0.005 margin above the threshold |

**Full-dataset impact** (`docs/reports/score-diff-1.2.0-to-1.2.1.md`, all
33,970 hotels, recomputed live since the v1.2.0 parquet was already
overwritten before this diff was written — see that report's note):
28.3% of hotels moved more than 15 points, mean shift negative in every
city (−3.6 to −15.7). This is a **minor** change by `docs/scoring.md §5`'s
own definition ("rankings may shift"), not a patch, despite the version
string.

**Per-city Spearman stays as volatile as at v1.2.0**
(`docs/reports/phase-3-family-strict-calibration.json`): Rome 1.0,
Amsterdam 0.949, Lisbon 0.949, Dubai 0.894 vs. Singapore −0.632, Barcelona
−0.258, Paris −0.2, Tokyo −0.031 — each city has only 3-5 golden hotels, so
individual label noise dominates at that sample size. **The aggregate
crossed the 0.5 line; the underlying instability did not go away.** This
is reported as a **thin, technical pass**, not a robustly validated fix.

## Decision

Per the owner's pre-authorized rule and this session's explicit "last
authorized iteration" instruction: **Phase 3 closes on this result.**
family_convenience passed its gate (0.5052 ≥ 0.5) — closure is not
conditional on the margin being comfortable, only on clearing the bar. The
thinness of the pass and the per-city noise are recorded here and in
`docs/scoring.md` as a known characteristic of this dimension going
forward (same treatment as quietness_proxy's documented proxy-limitation
note), not as a reason to keep the gate open or to tune further.

No further class, weight, or area-threshold changes to family_convenience
without another explicit owner review — this ADR (docs/adr/009) is the
last one authorized for Phase 3.
