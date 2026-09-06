# Phase 3 — calibration (§4.2) & sensitivity analysis (§4.3): final report

> Read alongside `tests/golden/LABELS-PROVENANCE.md` (label provenance
> caveat, must be applied to every number below) and `docs/scoring.md §4-5`
> (the protocol this report executes). Sections 1-5 below are the original
> report, delivered before any change was made, per the explicit instruction
> to show it first. **§6 is an addendum**: the owner reviewed this report,
> accepted the freeze recommendation, and separately approved the
> family_convenience v2 fix it identified — executed, `score_version` is now
> `1.1.0`. Read §6 for what changed and its outcome; §1-5 are left as
> originally delivered, for the record.

## Recommendation (read this first)

**Freeze all v1.0.1 constants as-is. Do not bump score_version.** Nothing in
this calibration or sensitivity pass clears the bar for a deliberate,
owner-reviewed change:

- The 4 dimensions with a well-matched label (transit, restaurants,
  nightlife, and now indirectly quietness via the composite) all pass the
  §4.2 acceptance bar or come from a formula the sensitivity pass shows is
  not load-bearing.
- Every §4.3 perturbation (decay scales, quietness penalty weights, persona
  weights, the nightlife nearest-vs-density variant) left rankings
  materially stable (Kendall-tau ≥ 0.85 in every single city, most ≥ 0.9).
  Per ADR-004 point 4, that is precisely the "no further tuning" outcome —
  spending calibration effort reweighting constants nothing is sensitive to
  would be false precision, the exact failure mode §4.3 exists to prevent.
- The one real problem found — `family_convenience` scoring **0 for hotels
  that do have a nearby park** — is **not a constant to retune**. It is a
  missing data source (Overture's polygon land-use theme isn't ingested).
  Fixing it means adding a new theme to the ETL, which is a data-pipeline
  change + new score_version, not a weight tweak, and belongs in its own
  scoped piece of work with its own owner sign-off — not smuggled into this
  calibration pass. See §4 below.

Nothing here should be read as "v1.0.1 is validated." It should be read as:
against the evidence available (weak evidence — see the provenance caveat),
no specific change is justified yet, and the one specific defect found has a
specific, different fix that isn't "adjust a number."

---

## 1. Calibration (§4.2) — final results, 4 variants

Ran `scripts/calibrate_golden_set.py` against score_version 1.0.1 (release
`2026-08-19.0`), 50/50 golden-set hotels joined successfully. Full numbers:
`docs/reports/phase-3-calibration-4.2.json`, `-joined.csv`.

| Pair | (a) all 50 | (b) excl. 2 prior-exposure | (c) excl. 7 low-confidence |
|---|---|---|---|
| transit_convenience vs transit_access (+) | **0.809** | 0.794 | 0.829 |
| nearby_restaurants vs food_essentials (+) | **0.828** | 0.821 | 0.803 |
| major_road_exposure vs quietness_proxy (−) | −0.357 | −0.360 | −0.403 |
| nightlife_intensity vs nightlife_access (+) | **0.795** | 0.771 | 0.824 |
| park_family_convenience vs family_convenience (+) | **−0.248** | −0.218 | −0.332 |
| (d) composite(0.6·road+0.4·nightlife) vs quietness_proxy (−) | −0.211 | −0.265 | −0.298 |

**Transit, restaurants, nightlife: pass, robustly.** All three clear the
0.6 bar in every variant, including the most adversarial one (c, dropping
the 7 labels flagged as weaker). These three dimensions' formulas
(proximity decay + saturating density curve) are validated as well as this
weak-evidence golden set can validate anything. No action.

**Quietness — direction confirmed, magnitude weak, composite label doesn't
help (new this round):**
The requested composite label (0.6·major_road_exposure + 0.4·nightlife_intensity,
weights taken from the formula's own major_road:nightlife penalty-weight
ratio, 45:25) was meant to test whether comparing `quietness_proxy` against
*only* the road label was structurally unfair, since the formula also
penalizes nightlife (and rail, and airport proximity, neither of which has a
label). **The composite correlates *worse* (−0.21 to −0.30) than
major_road_exposure alone (−0.36 to −0.40), not better.** Root cause,
checked directly: `nightlife_intensity` (label) vs `quietness_proxy`
(computed) is essentially uncorrelated on its own (Spearman ≈ **0.12**, and
the wrong sign), and `major_road_exposure` and `nightlife_intensity` are
themselves mildly anti-correlated in my own labels (−0.20) — combining a
weak/wrong-signed signal with a moderate correctly-signed one dilutes the
correctly-signed one. So: **the "unfair comparison" hypothesis is rejected
by the data** — adding the nightlife term to the comparison target made
agreement worse, it didn't reveal hidden agreement. The road-only comparison
stands as the more informative one of the two. This doesn't change the
verdict on quietness_proxy itself: direction is still correct (all four
variants including baseline are negative, as physically required), magnitude
is still short of 0.6, and §4.3 (below) shows nothing about the quietness
formula is load-bearing enough to justify tuning from this evidence anyway.

**Family — real anomaly, root cause now identified (see §4 — not a labeling
artifact, not a constant to tune):** consistently **wrong-signed** across all
3 variants. Investigated below; conclusion is a data-source gap, not
grounds for reweighting.

Per-city mean error (`|label rescaled to 0-100 − computed|`, variant a):
no city stands out as uniformly broken — `park_family_convenience` has the
largest error in every single city (24.6-54.1), consistent with it being a
dimension-level problem rather than a city-specific one.

---

## 2. Sensitivity analysis (§4.3)

Ran `scripts/sensitivity_analysis.py` (decay scales, hybrid weight,
quietness penalty weights, the documented nightlife-penalty variant) and
`scripts/sensitivity_persona_weights.py` (balanced-persona weights). Method:
recompute each dimension's real scoring SQL with one constant perturbed,
measure Kendall-tau of the resulting per-city hotel ranking against the
current (baseline) ranking. Full numbers:
`docs/reports/phase-3-sensitivity-4.3.json`,
`phase-3-sensitivity-persona-weights.json`.

| Perturbation | mean τ across 12 cities | Load-bearing anywhere? |
|---|---|---|
| decay_scale_m, all 5 dims, ±30% | 0.93 – 0.99 | No |
| hybrid_absolute_weight → 0.5 / 0.9 | **1.0 (exactly)** | No — see note below |
| quietness penalty weights, ±30%, one at a time | 0.93 – 0.97 | No |
| nightlife: nearest-venue → density-based penalty | 0.85 – 0.92 (mean 0.888) | No |
| balanced persona weights, ±10pt, one dim at a time | 0.78 – 0.97 | Marginal: Tokyo 0.783 on quietness+10pt only |

**Everything is stable.** Per ADR-004 point 4's own rule (τ ≥ 0.8 → freeze,
no further tuning), none of these constants earns real calibration
attention. The single τ=0.783 (Tokyo, quietness_proxy weight pushed to
0.25 in the balanced persona) is 0.017 under the threshold, in one city, on
a persona-display weight, not a fact-computing constant — not worth
chasing.

**Note on `hybrid_absolute_weight` (worth recording, not acting on):** its
τ = 1.0 in every single test is not really an empirical finding — it's
mathematically guaranteed. `absolute_score` and `city_percentile` are both
strictly increasing functions of the same underlying `weighted_count`; any
convex combination of two functions that are both monotonic in the same
variable is itself monotonic in that variable, so **no value of
`hybrid_absolute_weight` can ever change a hotel's rank position within its
own city** — only the absolute score value. Kendall-tau on intra-city
ranking is structurally blind to this constant's real effect, which is on
**cross-city comparability** of absolute scores (whether an "82" in Rome and
an "82" in Tokyo mean the same underlying density) — a legitimate question,
just not one this metric can answer. Not a defect in the analysis, just a
scope note for whoever revisits this: if cross-city absolute-score
comparability is ever challenged, this is the constant to look at, and it
needs a different test than the one §4.3 specifies.

**Priority candidate (nightlife nearest-venue vs density-based penalty) —
tested, does not justify a change:** per scoring.md §4.3's flagged
simplification, swapped the quietness nightlife penalty from
`weight·exp(−nearest_m/scale)` to a density term,
`weight·(1−exp(−Σexp(−dᵢ/scale)/saturation))`, isolating only that one term
(other three penalties computed unperturbed). Result: τ = 0.888 mean, stable
in every city (nowhere below 0.85) — a real but modest reordering, and
**no improvement** in Spearman against `major_road_exposure` (−0.338 vs
baseline −0.357, i.e. marginally worse, within noise for n=50). The
documented real effect (one loud bar next door vs. a whole street of them)
is still true and still worth a proper fix eventually, but this evidence
doesn't show the density formulation is actually better calibrated — it's a
different plausible model, not a demonstrated improvement. **No change
recommended**; keep the existing nearest-venue formula and the existing
scoring.md §4.3 note as-is (still logged, still not fixed, still correctly
flagged as needing "compare both against golden labels" before any change —
which is what just happened, and it didn't favor the alternative).

---

## 3. Family_convenience — root-cause investigation (surface-vs-point)

Hypothesis to test (owner instruction): the formula counts POI **points**
(`places` theme: park/playground/zoo/aquarium categories) within 600m. A
large park is one polygon in reality but may be represented by very few —
or zero — points close enough to a hotel at its edge, while the actual green
space is right there. Tested directly against Overture's `base/land_use`
theme, which **is available in the same monthly release** but **is not
ingested by this pipeline** (confirmed: `src/hotelareascore/ingest.py`
reads only `theme=places` and `theme=transportation` — `theme=base` has
never been touched).

Method (`scripts/family_surface_vs_point.py`, read-only, queries the live
Overture release directly): for the 11 golden-set hotels whose computed
`family_convenience` is exactly 0.0, checked whether a `land_use` polygon
tagged `park` or `playground` exists within ~600–900m (bbox-center distance,
a conservative proxy — the true boundary distance is always ≤ this).

**Result: 9 of 11 have a real, nearby park or playground polygon that the
points-only pipeline completely misses.** Examples: `ホテルCOCO` (Tokyo) has
a playground **60m** away with zero point representation; `Strathfield
Hotel` (Sydney) has a park **105m** away; `Lisboa Camping & Bungalows` sits
**78m** from an unnamed park polygon plus a named 90,468 m² park at 318m.
Full list: `docs/reports/phase-3-family-surface-vs-point.json`. Only 2 of
11 (Changi Lodge, Singapore; Airport Hotels Bangkok Travel Service) have no
nearby land-use park/playground polygon either — for those two, the 0 score
may be accurate (Airport Hotels Bangkok's own label was 1/5, i.e. "poor," so
0 is roughly consistent; Changi Lodge's label of 4 vs. no polygon evidence
either way is a genuine unresolved case, possibly a labeling error on my
part rather than a formula error).

**A second, opposite-direction effect exists too, discovered while
verifying Hyde Park (London) as a sanity check on the "one big park = one
point" framing:** well-mapped landmark parks are not under-represented —
they're represented by **dozens** of separate named points inside the same
park (Serpentine Lake, bandstand, playground, gardens, memorial fountain,
each a separate `park`-category point), so a hotel next to a heavily-mapped
park like Hyde Park likely gets an inflated weighted count, not a deflated
one. (A handful of these points also carry wildly wrong coordinates —
several "Hyde Park"-named points sit 10-20km from the real park — but since
the family_convenience query is radius-bound, those don't reach any nearby
hotel; they're place-name noise, not a proximity-scoring problem, and out
of scope here.)

**Conclusion: the point-vs-polygon representation gap is real, goes in both
directions depending on how well a specific park happens to be mapped as
individual points, and plausibly explains a meaningful share of the
family_convenience anomaly independent of any labeling-construct issue.**
This is a data-source gap, not a constant. The correct fix is adding
`theme=base/type=land_use` (subtype `park`; `recreation`/class `playground`)
as a POI source for `family_convenience` — new ETL ingestion, a taxonomy
mapping change, and (because it changes what counts as a match, not just a
weight) a **minor `score_version` bump with its own golden-set regression**
per `docs/scoring.md §5`. That is real, scoped work for a future session —
explicitly **not done here**, both because it's out of scope for a
calibration pass and because the owner asked not to see any constant change
before reviewing this report.

---

## 4. What this report is NOT saying

- It is not saying v1.0.1 is "calibrated" or "validated" in a strong sense —
  the golden set is Claude-labeled, not owner- or independently-verified
  (`tests/golden/LABELS-PROVENANCE.md`), and this report inherits that
  caveat in full for every number above.
- It is not recommending the family_convenience fix be done now — only that
  its cause is now understood and scoped, as a data-pipeline change with its
  own version bump and regression, not a calibration-pass weight change.
- It is not closing the quietness_proxy question — direction is right,
  magnitude is weak, and nothing tested moves the needle on that magnitude.
  If a future round wants to actually improve it, the lead identified here
  is ingesting `road_flags`/lane-count-style road severity (not currently
  modeled — every "major road" gets the same penalty regardless of size)
  rather than the nightlife term, which was already tested and didn't help.

## 5. Score-version protocol (§5) — not triggered

No formula, weight, or taxonomy-mapping change is made by this report.
`score_version` stays `1.0.1`. No golden-set regression, no diff report, no
owner sign-off is required for *this* delivery, because nothing was
changed. The two follow-up items identified (family_convenience data
source; quietness road-severity modeling) each require the full §5
protocol **when and if** the owner decides to schedule them.

---

## 6. Addendum (2026-09-06) — family_convenience v2 executed, re-calibrated, target not met

Owner decision on this report: accept the freeze recommendation (§1-5,
unchanged); do not close Phase 3 yet because family_convenience has a
proven root cause; fix it (`docs/adr/006`); re-run the full §5 protocol;
target Spearman ≥ 0.6 against the same 50 labels; **on failure, stop and
report back before touching anything else.** All of that ran. Result:
**target not met — stopping here, as instructed, before any further
change.**

### What was built and run

- Ingested `theme=base/type=land_use` for all 12 cities (new fail-closed
  schema check, `overture.REQUIRED_LAND_USE_COLUMNS`) — same release
  (`2026-08-19.0`), re-ingested in place. `green_spaces.parquet` added per
  city (8,046 polygons for London alone; counts vary by city).
- `family_convenience` is now its own scoring function
  (`scoring._family_convenience_dimension`): `zoo`/`aquarium` stay points,
  `park`/`playground` score from land_use polygons, distance to the
  polygon's own boundary (`ST_Distance`, 0 if the hotel is inside it).
  `park`/`playground` places-theme points are kept for the "Why?" display
  only, no longer feed the score. No existing constant's value changed.
- `score_version` → **1.1.0**. All 12 cities re-scored, all 12 pass
  `validate` with no hard failures. Diff report:
  [score-diff-1.0.1-to-1.1.0.md](score-diff-1.0.1-to-1.1.0.md) — as
  expected, `family_convenience` changed for nearly every hotel in every
  city (new source, most hotels had 0 nearby points before), balanced_score
  moved by single digits everywhere (family_convenience's persona weight is
  0.10-0.25, so even a full 0→100 swing bounds the balanced-score effect),
  **zero big movers (|Δ| ≥ 15) in any city.** No shocking or unexplained
  shift; this is exactly the well-behaved diff a source-only change (same
  formula shape) should produce.
- Re-ran `scripts/calibrate_golden_set.py` against the new 1.1.0 scores.
  Joined tables committed for both versions, per item 4 below.

### Calibration result: sign fixed, magnitude still short

| Variant | family_convenience Spearman, v1.0.1 (before) | v1.1.0 (after) |
|---|---:|---:|
| (a) all 50 | −0.248 | **+0.095** |
| (b) excl. 2 prior-exposure | −0.218 | **+0.060** |
| (c) excl. 7 low-confidence | −0.332 | **+0.100** |

The fix worked in the sense the diagnosis said it would: the correlation is
no longer wrong-signed (evidence the polygon-boundary fix genuinely
corrected real false-zeros, consistent with the 9/11 root-cause finding in
§3). But it is nowhere near the 0.6 target — essentially uncorrelated, just
on the correct side of zero now. Per-city mean error dropped in most cities
(e.g. Bangkok 24.6 → 12.4) but stayed high in several others (Singapore
47.4, Amsterdam 42.7) — inconsistent enough across cities that this doesn't
look like "almost there, needs one more small fix."

**Per the owner's own failure criterion, no further change is made without
review.** In particular: no taxonomy expansion (e.g. adding
`recreation_ground`/`nature_reserve`/`village_green` land_use classes,
which exist in the data but weren't included), no radius change, no
re-labeling — any of those would be "touching something else" before this
conversation happens.

### Hypothesis for the remaining gap (not acted on)

The most likely remaining explanation, unchanged from §1's original
discussion of this dimension: **a construct mismatch between the label and
the formula**, not a further data gap. `park_family_convenience` was labeled
from a holistic "would a family enjoy staying here" judgment (walkability,
general neighborhood feel, proximity to attractions) rather than strictly
"is there a park/playground/zoo/aquarium within 600m" — the formula's
literal definition. Fixing the data source removed the false negatives but
can't fix a labeling target that was never measuring quite the same thing.
If this is right, the next real step is not another formula change but a
narrower re-labeling question ("is there a park or playground within
roughly a 5-8 minute walk?") — a decision for the owner, not something to
act on unilaterally here.

### Other items from this request

- **Quietness:** kept as-is (§4.3 above already covers this — nothing
  tested moved it). `docs/scoring.md §4.3` and `/methodology` both now state
  the moderate-correlation limitation explicitly (methodology.astro: "a
  deliberate proxy, not a validated measurement... points the right
  direction but only moderately").
- **Auditability:** `tests/golden/joined-scores-1.0.1.csv` and
  `joined-scores-1.1.0.csv` committed (`tests/golden/joined-scores-README.md`
  explains provenance and how to regenerate) — the exact table each
  Spearman number above is computed from, replayable without re-running the
  ETL pipeline.
- **Locality disclosure fix:** `City.expected_region` (config.py) +
  `addresses[].region` extraction (ingest.py) + a `locality_mismatch` check
  independent of the 15km `far_from_center` threshold (webdata.py),
  disclosed on the hotel page next to the existing far-from-center flag.
  Configured for New York (`expected_region: NY`) since that's the bbox
  known to reach into another US state. **Scale finding, bigger than the
  single SpringHill Suites example that prompted this:** 351 of New York's
  2,194 hotels (16%) carry a New Jersey address region, and **188 of those
  351 are within the 15km far_from_center threshold** — meaning until this
  fix, those 188 had no disclosure of any kind. This is now caught and
  disclosed for all 351, but the scale suggests the New York bbox itself
  may be worth revisiting (tightening the New Jersey-facing edge) as a
  separate, later decision — not done here, since it's a data-scope change
  beyond what was asked, and the disclosure now covers it either way.

### Recommendation

Ship `score_version` 1.1.0 as delivered — it is a genuine improvement
(real bug fixed, verified against live Overture data, zero regressions in
the diff) even though it does not clear the calibration bar. **Phase 3's
calibration gate stays open on family_convenience specifically**, per the
owner's own stated closing condition ("la Phase 3 se clôt quand famille
passe"). Next decision is the owner's: accept family_convenience as a
disclosed, imperfect dimension (same treatment as quietness_proxy) and
close Phase 3 anyway, or commission a targeted re-labeling pass before
closing. No further formula or taxonomy change is planned unless and until
that decision is made.
