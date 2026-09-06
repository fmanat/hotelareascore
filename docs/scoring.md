# scoring.md — scoring model, calibration, and change protocol

> Supersedes §8–10, 31, 41–42 of the original. Adds what was missing: an
> honest statement that all v1 constants are priors, a sensitivity-analysis
> requirement, and a versioning/migration protocol for published pages.

## 1. Philosophy

No single "truth score". Expose: dimension scores, data confidence, persona
fit, optional balanced score. Never let one number hide trade-offs. All
computation deterministic and reproducible; every persisted score carries
`score_version, source_release, computed_at, confidence` + inputs reference.

## 2. Dimensions (MVP, 6)

Walkability/useful density · Transit access (no travel-time claims without
routing data) · Food & essentials (diversity + proximity over raw counts) ·
Quiet-surroundings **proxy** (roads/rail/nightlife/airport — mandatory copy:
"estimates environmental noise exposure from nearby infrastructure and
activity; not an in-room noise measurement") · Family convenience (never
"safe for children") · Nightlife access (positive only for that persona).

## 3. Model v1 — priors, explicitly

Distance decay `exp(-d/scale)` per nearby POI, summed to a weighted count.
Density dimensions (walkability, food & essentials, family, nightlife)
normalize that weighted count with a saturating curve,
`absolute = 100·(1 − exp(−weighted_count/saturation))`, then hybridize with
where the hotel ranks in its own city, `hybrid = 0.70·absolute +
0.30·city_percentile` (docs/adr/004 §5 versioning applies to any change to
either formula — corrected 2026-09-06 from an earlier `log(1+weighted_count)`
description that no longer matched `src/hotelareascore/scoring.py`; the code
was always the saturating-curve version). Transit access is proximity-only
(nearest stop per mode, small multi-mode bonus), never density-based — no
travel-time claims without routing data. Quietness penalty weights/scales in
`data/config/score-weights.yml` (config, never hardcoded in UI); see §4.3 for
a known simplification in that formula.

**Family convenience v2 (score_version 1.1.0, docs/adr/006):** the same
weighted-count formula above, but from two combined sources instead of one:
`zoo`/`aquarium` stay points (Overture `places`, no polygon exists for
these), while `park`/`playground` now score from Overture's `base/land_use`
polygon footprints, distance measured to the **polygon's own boundary**
(`ST_Distance`, 0 if the hotel is inside it) — never a centroid. v1 scored
all four categories as `places`-theme points, which measurably undercounted
real nearby parks with no correspondingly-placed point
(`docs/reports/phase-3-family-surface-vs-point.json`: 9/11 golden-set
zero-scores had a real polygon within 600-900m). No constant changed —
same decay scale, saturation, and hybrid weight as before this version.

**Status of every constant above: educated prior, not validated.** They exist
to get to calibration, and calibration (§4) may change any of them. The
`/methodology` page must be able to explain the formula in plain language.

Confidence 0–100 from geolocation certainty, POI coverage, source
completeness/age, observation counts, mapping confidence, dedupe quality, city
baseline sample size. High ≥ 80, Medium 60–79, Low < 60. Low-confidence hotels
stay searchable, never indexable.

## 4. Calibration protocol (Phase 3, before public launch)

### 4.1 Golden set
~50 hotels across ≥ 5 cities (include London + Bangkok for urban-pattern
contrast), all 12 launch cities in practice for Phase 3. Each hotel labeled
1–5 on: transit convenience, nearby restaurants, major-road exposure
(correlates NEGATIVELY with quietness_proxy — a plausibility check in
§4.2, not just a sign convention), nightlife intensity, park/family
convenience. Stored at `tests/golden/hotels.csv`. Goal is "no obvious
nonsense", not scientific truth.

**Blind labeling, mandatory (added 2026-09-06, owner instruction):** the
labeling tool never shows our computed scores, verdict sentence, or reason
codes while a hotel is being rated — name, map/coordinates, address, and the
5 rating questions only. Showing our own output during labeling would let it
anchor the very labels meant to check it, silently inflating the apparent
agreement in §4.2. A hotel that can't be confidently judged gets no label
(an explicit "can't judge" skip) rather than a guessed one — a missing label
is honest signal, a guessed one is noise that looks like data.

**Actual provenance (2026-09-06, must stay accurate — see
`tests/golden/LABELS-PROVENANCE.md`, committed alongside the CSV):** these
50 labels were produced by **Claude, not the owner** — the owner declined
the labeling task and asked Claude to do it instead, from world knowledge of
each pinned location (station proximity, arterials, districts, parks),
independent of this project's Overture data and formulas, but **not
independently verified on the ground and not owner-reviewed**. This is
weaker evidence than owner or third-party human labels: apply §4.2's bar
with more suspicion than the bar itself implies, and do not describe this
set anywhere as "human-verified" — "calibrated against a labeled reference
set" is accurate, a claim of human or owner validation is not. `docs/STATE.md`
records this as a standing caveat on every result derived from this golden
set until it is replaced or independently spot-checked.

### 4.2 Acceptance
Direction matches the labeled reference set (Spearman rank correlation per
dimension ≥ 0.6 as a working bar — read with the §4.1 provenance caveat in
mind, this set is Claude-labeled, not owner- or independently-verified); no
systematic city bias (per-city mean error inspected); no category-mapping
disasters; quietness proxy plausible; outliers explainable.

### 4.3 Sensitivity analysis (new, required)
Before freezing v1.0: perturb each major constant (±30% on decay scales,
hybrid weight 0.5→0.9, persona weights ±10 pts) and measure Kendall-tau of the
resulting hotel ranking per city vs baseline.
- Rankings stable (τ ≥ 0.8) under most perturbations → constants are not
  load-bearing → freeze and move on, no further tuning.
- A constant whose perturbation reorders rankings heavily → THAT constant gets
  actual attention (compare both settings against golden labels, pick, and
  document in an ADR).
This spends tuning effort only where it matters and kills false precision.

**Priority candidate flagged 2026-09-06 (owner audit), not tuned yet:** the
quietness_proxy nightlife penalty looks only at the *nearest* nightlife venue
(`min(distance)`), not density — a hotel with 25 bars within 250 m and one
with a single bar at the same distance get the same penalty, capped at the
configured max weight (25 pts, `score-weights.yml` quietness.penalties.
nightlife). Repro: a hotel with `nightlife_access` ≈ 95 (many nearby venues)
can still show `quietness_proxy` ≈ 85. This is a plausible real effect (one
loud bar next door vs. a whole street of them are not the same), but the
current formula can't tell them apart — put it at the top of the §4.3
perturbation list (try a density term, e.g. `count(venues within radius)`,
alongside the pure-nearest version, and compare both against golden labels).
Do not change the constant or formula outside that calibration pass.

**Resolved 2026-09-06 (full sensitivity pass,
`docs/reports/phase-3-calibration-sensitivity-report.md`): kept as-is, not
tuned.** Every constant tested (decay scales, hybrid weight, all 4 quietness
penalty weights, persona weights, and the density-term variant above) left
per-city rankings stable (Kendall-tau ≥ 0.85 everywhere). The density-term
nightlife-penalty variant was built and tested against the golden labels as
instructed: no improvement (Spearman vs `major_road_exposure` −0.338 vs
baseline −0.357, i.e. not better, within noise for n=50). **Known
limitation, accepted rather than fixed:** `quietness_proxy`'s agreement with
independent judgment of road/rail/nightlife exposure is directionally
correct but only moderate (−0.36 to −0.40 vs the road-exposure label across
sample variants, short of the 0.6 working bar) — it is an explicitly-labeled
**proxy**, not a validated measurement, and `/methodology` says so. The
nearest lead for a future improvement is modeling road *severity* (a
motorway and a two-lane primary road currently get an identical penalty),
not the nightlife term tested here.

**family_convenience: real anomaly, root cause found, fixed twice, still
open — see docs/adr/006, docs/adr/007.** Wrong-signed against its label in
all 3 calibration variants; traced to the v1 formula scoring point
representations of an inherently areal feature (park/playground). v2
(score_version 1.1.0) scores from Overture's polygon land-use footprints
instead, distance to the polygon boundary rather than a point or centroid —
this fixed the sign but not the magnitude. v1.2.0 expanded the green-space
class list further (verified against a live extract, `docs/adr/007`) and
was recalibrated against a fresh, stricter re-labeling
(`tests/golden/family_strict.csv`, "reachable on foot only"): Spearman
0.209, still short of the owner's 0.5 bar. Per the owner's own
pre-authorized rule, no further tuning without another explicit review —
see `docs/reports/family-v1.2.0-recalibration.md` for the full result and
candidate next steps. **Phase 3's calibration gate stays open on this
dimension**; the rest of the gate (§4.2 above) is unaffected.

## 5. Score-version change protocol

1. Any formula/weight/taxonomy-mapping change → new `score_version` (semver:
   patch = no ranking impact expected; minor = rankings may shift; major =
   dimension semantics change).
2. Run golden-set regression + per-city diff report (biggest movers, mean
   shift). A change that improves one city but breaks another must not ship
   unnoticed.
3. Minor/major versions: owner sees the diff report before deploy.
4. Published pages: scores update in place with the new version shown;
   `dateModified` updates (this IS a material change); if the balanced score
   of an indexable page moves > 15 points, the page's explanation copy must be
   regenerated from the new facts, not left stale.
5. Old score rows are retained (unique key includes version) — history is part
   of the moat.

## 6. Reason codes & taxonomy

Internal stable taxonomy (`lodging.hotel`, `food.restaurant`, …) mapped from
source taxonomies in one package; every mapping change requires tests. Human
explanations derive from reason codes (`HIGH_RESTAURANT_DENSITY`,
`VERY_CLOSE_METRO`, `NEAR_PRIMARY_ROAD`, …) → deterministic templates first,
LLM phrasing optional, multilingual later becomes cheap.
