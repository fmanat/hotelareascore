# ADR-007 — family_convenience v1.2.0: expand the green-space class filter

- **Status:** accepted
- **Date:** 2026-09-06 (overnight run, owner-authorized in advance)
- **Decision recorded from:** overnight mission order Bloc A; ADR-006;
  `docs/reports/phase-3-calibration-sensitivity-report.md` §6

## Context

ADR-006 (score_version 1.1.0) fixed family_convenience's most severe bug
(points-only scoring of an areal feature) but re-calibration against the
golden set only moved Spearman from wrong-signed (−0.22 to −0.33) to
correctly-signed but weak (+0.06 to +0.10) — short of the 0.6 target. The
owner ordered a diagnostic on 5 specific hotels before any further change:
list nearby `land_use` polygons and confirm whether real green space is
excluded by the filter or absent from the source.

Diagnostic (`docs/reports/family-v1.2.0-diagnostic.md`), run against the
live release, found both:

1. **A genuine filter gap for 3 of 5 hotels.** Hotel Gilinsky (Amsterdam)
   has 6 `managed`/`grass` polygons within 140m and forest within 213m,
   invisible to v1.1.0's park/playground-only filter. Crowne Plaza Rome St.
   Peter's has 5 `recreation`/`pitch` and `recreation`/`track` polygons
   within 150m — v1.1.0 only matched `recreation`/`playground`. Neither
   theme (`base/land_use`'s broader classes, or `base/land` at all) was
   being read.
2. **Genuine absence for 2 of 5 hotels.** Changi Lodge (Singapore) and the
   Holiday Inn Paris CDG corporate-entity pin (Charenton) have no real
   green space within radius even under an expanded filter — nearest
   candidates are farmland/meadow (private, correctly excluded) or a
   handful of street trees. Their labels don't correspond to any fixable
   data gap.
3. **A wrong assumption in ADR-006**, caught while checking `land_use`'s
   full taxonomy directly: `entertainment`/`zoo` **is** a land_use polygon
   (14 in London alone) — ADR-006 assumed zoo had no polygon footprint and
   left it as a points-only category. Corrected here.

## Decision

1. Ingest a second Overture theme, `base/land` (natural land-cover:
   forest, grass, sand, etc. — distinct from `base/land_use`'s human
   land-use categories), with the same fail-closed schema check as every
   other source (`overture.REQUIRED_LAND_COLUMNS`).
2. Expand the `land_use` filter (verified against a live extract of
   London's full subtype/class distribution, not guessed):
   - `subtypes: [park, protected]` (any class — adds `protected/
     nature_reserve` and friends alongside the existing `park/*`)
   - `recreation` classes: add `pitch`, `recreation_ground`, `track`
     alongside the existing `playground`
   - new `managed` class: `grass`
   - new `entertainment` class: `zoo` — moved off the points list
     (`aquarium` is now the only point-based category left; no polygon
     exists for it)
3. Add the `land` filter: `subtypes: [forest, grass]` (any class) plus
   `sand`/`beach` specifically (not `sand`/`sand`, which is generic/desert
   sand, not a recreational beach).
4. Explicitly excluded, checked and rejected rather than overlooked (see
   taxonomy-mapping.yml's comment block and the diagnostic report for the
   evidence): `horticulture` (private gardens/allotments — 28,030
   `horticulture/garden` polygons in London alone, almost all private back
   gardens), `golf` (private/members courses), `agriculture` (private
   farmland), `campground` (ambiguous, often the lodging property itself),
   `recreation/stadium` and `recreation/marina` (ticketed venue / boat
   marina), `tree`/`tree_row` (242,527 + 4,768 individual street trees in
   London alone — ubiquitous and meaningless as a "family amenity"
   signal), `shrub`/`wetland`/`rock`/`physical` (not usable leisure space).
5. `score_version` → 1.2.0 (minor: same formula shape and constants as
   1.1.0, broader input only). Full §5 protocol: re-ingest + re-score all
   12 cities, per-city diff report, re-run the golden-set calibration.
6. Re-calibrated against `tests/golden/family_strict.csv` (a fresh,
   narrower-definition re-labeling — "parks/playgrounds reachable on foot
   only" — provided by the owner as this ADR's acceptance test, see
   `tests/golden/LABELS-PROVENANCE.md` amendment).

## Rationale

- Every included/excluded class was checked against a live extract of
  Overture's own taxonomy for this release, per the owner's explicit "ne
  devine pas" instruction — not assumed from category names that sound
  plausible.
- The exclusion list is deliberately conservative: several excluded
  classes (golf, horticulture) are visually "green" but not a walkable
  public amenity a family can use, and including them would trade one
  false-negative problem (v1.1.0, missing real parks) for a false-positive
  one (counting a private members' golf course or someone's back garden as
  "family convenience").
- No constant's value changed — this stays a data-source/taxonomy
  expansion, consistent with ADR-006's precedent, not a weight-tuning
  exercise.

## Consequences

- New ETL dependency: `base/land`, same failure mode as every other theme
  (schema drift fails the run closed).
- `green_spaces.parquet` per city now unions two theme sources; scoring.py
  needed no change at all — `_family_convenience_dimension` already
  treated `green_spaces` as an opaque polygon source, so broadening what
  ingest.py puts into that table required zero scoring-logic changes.
- If the re-calibration in §4.2 still doesn't clear a defensible bar
  against `family_strict.csv`, per the owner's pre-authorized decision this
  ADR's scope stops here — no further class additions or constant tuning
  without another explicit owner review.

## Outcome (same night)

Recalibrated against `family_strict.csv`: Spearman = **0.209**, below the
owner's pre-authorized 0.5 threshold. Per that same instruction, stopped
here — no further class or constant changes. Full result and discussion:
`docs/reports/family-v1.2.0-recalibration.md`. Notably, the same class
expansion *did* meaningfully help the original, holistic
`park_family_convenience` label (0.095 → 0.239) while not helping the new
strict one (0.234 → 0.209) — evidence the two labels are measuring
different constructs, not that this ADR's diagnostic work was wrong. Phase
3's family_convenience gate stays open.
