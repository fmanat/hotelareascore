# ADR-009 — family_convenience v1.2.1: per-class weight on green-space polygons

- **Status:** accepted
- **Date:** 2026-09-07 (overnight run, owner-authorized in advance as the
  last authorized iteration on this dimension for Phase 3)
- **Decision recorded from:** overnight mission order, task 1; ADR-007;
  `docs/reports/family-v1.2.0-recalibration.md`;
  `docs/reports/family-v1.2.1-recalibration.md`

## Context

ADR-007 (v1.2.0) expanded family_convenience's green-space class filter to
include `managed/grass`, `recreation/pitch`/`track`/`recreation_ground`,
and the new `base/land` theme (`forest`, `grass`, `sand/beach`). Every
included polygon counted equally toward the same decay-weighted sum used
before the expansion. Recalibration against `tests/golden/
family_strict.csv` (a fresh, narrower "reachable on foot" re-labeling)
landed at Spearman **0.209**, below the 0.5 threshold — worse, on this
label, than the pre-expansion 0.234. The recalibration report's own
diagnosis: several hotels the strict label rated 1-2/5 score 77-99/100
computed, because a large sports pitch or a patch of managed grass behind a
building was counting the same as a real park.

## Decision

Weight each green-space polygon by how directly it matches "a park a
family would walk to," instead of counting every included class equally.
Nothing is removed from v1.2.0's class list — every class that counted
before still counts — only the per-polygon weight changes:

| Weight | Classes | Area floor |
|---|---|---|
| **1.0** | `park/*` (any class), `protected/*` (any class), `entertainment/zoo`, `recreation/playground` | none |
| **0.4** | `recreation/pitch`, `recreation/track`, `recreation/recreation_ground`, `sand/beach` | none |
| **0.4** | `managed/grass`, `grass/*` (any class), `forest/*` (any class) | **≥ 2,000 m²**; below it, weight 0 (doesn't count) |

The 2,000 m² floor and the 0.4/1.0 split are not guessed: queried directly
against the live `green_spaces.parquet` extract for all 12 cities
(subtype/class × count × median polygon area). `managed/grass` medians
range 106-2,858 m² but sit under 300 m² in 9 of 12 cities — consistent
with the recalibration report's own finding ("a patch of managed grass
behind a building") — while real `park/park` polygons median 2,000-5,500
m² in the same cities. 2,000 m² sits at the low end of that park range:
high enough to exclude street verges/traffic-island/lawn slivers, not so
high that it would exclude a genuinely sizeable lawn or copse.
`recreation/pitch`/`track`/`recreation_ground` get the reduced weight but
no area floor — a single pitch is already a real, self-limiting feature;
an area filter on top would just re-exclude legitimate small facilities,
which isn't the problem this ADR is fixing.

Implementation: `taxonomy.family_convenience_land_weight_sql` builds a SQL
`CASE` expression from `taxonomy-mapping.yml`'s new `family_convenience.
land_weights` config; `scoring._family_convenience_dimension` multiplies
each green-space hit's distance-decay contribution by this weight before
summing (aquarium, the one point-based category, stays weight 1.0,
unaffected). `score_version` → **1.2.1**.

## Outcome (same night)

Full protocol run: all 12 cities re-scored (score_version 1.2.1) and
re-validated (all 12 pass, `make validate`). Diff report — recomputed both
formulas live against the unchanged `green_spaces` source, since
`data/etl/` is gitignored and the v1.2.0 parquet was already overwritten
before this diff was written (a process gap, noted for next time; the
recomputation is exact, not approximate, since the source data itself
didn't change) — [score-diff-1.2.0-to-1.2.1.md](
../reports/score-diff-1.2.0-to-1.2.1.md): **28.3% of all 33,970 hotels
(9,628) moved more than 15 points**, mean shift strongly negative in every
city (−3.6 to −15.7). Per `docs/scoring.md §5`, this is a **minor** change
(rankings shift materially), not a patch, despite the version string's
third digit — consistent with how 1.0.1 and 1.1.0 were both classified by
real impact rather than by which digit changed.

Recalibrated against `family_strict.csv`:
**Spearman = 0.5052 — PASSES the pre-authorized 0.5 threshold**, by a
0.005 margin. Full result, including the pre-registered predictions this
was checked against and the per-city breakdown (which stays as volatile as
before: −0.632 to +1.0 across cities with 3-5 hotels each), is in
[family-v1.2.1-recalibration.md](../reports/family-v1.2.1-recalibration.md)
— this is reported as a **thin, technical pass**, not a robustly validated
fix: the aggregate crossed the line, the underlying per-city noise did not
go away, and the 50-hotel golden set (Claude-labeled twice over, per
`tests/golden/LABELS-PROVENANCE.md`) remains weak evidence throughout.

Per the owner's explicit instruction, this is the **last authorized
iteration** on family_convenience for Phase 3 — no further class, weight,
or threshold tuning without another explicit review, regardless of this
result. **Phase 3 gate closes** on this outcome (see `docs/STATE.md`).
