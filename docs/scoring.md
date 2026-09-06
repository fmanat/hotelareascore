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
contrast). Owner labels each 1–5 on: transit convenience, nearby restaurants,
major-road exposure, nightlife intensity, park/family convenience.
Stored at `tests/golden/hotels.csv`. Budget honestly: 8–15 owner-hours.
Goal is "no obvious nonsense", not scientific truth.

### 4.2 Acceptance
Direction matches human labels (Spearman rank correlation per dimension ≥ 0.6
as a working bar); no systematic city bias (per-city mean error inspected); no
category-mapping disasters; quietness proxy plausible; outliers explainable.

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
