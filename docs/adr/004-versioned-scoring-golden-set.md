# ADR-004 — Versioned scoring, golden-set regression, sensitivity-driven tuning

- **Status:** accepted (Phase 0)
- **Date:** 2026-09-06
- **Decision recorded from:** docs/scoring.md §1, §3–5; CLAUDE.md §2 (rule 5)

## Context

All v1 scoring constants (decay scales, hybrid weight 0.70/0.30, persona
weights, quietness penalties) are educated priors, not validated truths.
Published pages will show scores; silent changes would fake stability or fake
precision, both trust-killers.

## Decision

1. Every persisted score carries `score_version, source_release, computed_at,
   confidence` + inputs reference; `hotel_scores` unique on
   `(hotel_id, score_version, source_release)`; old rows retained.
2. Semver on `score_version`: patch = no expected ranking impact; minor =
   rankings may shift; major = dimension semantics change.
3. Any formula/weight/taxonomy change runs the **golden-set regression**
   (~50 owner-labeled hotels, ≥ 5 cities) + per-city diff report; minor/major
   require owner review of the diff before deploy.
4. **Sensitivity analysis before freezing v1.0:** perturb each major constant
   (±30% decay scales, hybrid 0.5→0.9, persona ±10 pts), measure Kendall-tau
   of per-city rankings vs baseline. τ ≥ 0.8 stable → freeze, no tuning.
   Only ranking-reordering constants get real calibration attention.
5. Indexable page whose balanced score moves > 15 points → explanation copy
   regenerated from new facts; `dateModified` updates (material change).

## Rationale

- Versioning + retained history is both a trust feature (public methodology,
  explainable changes) and part of the moat (score history).
- Sensitivity analysis spends tuning effort only where rankings actually
  depend on it — kills false precision cheaply.
- Acceptance bar (Spearman ≥ 0.6 per dimension vs owner labels, no city bias,
  no mapping disasters) targets "no obvious nonsense", not scientific truth.

## Consequences

- Owner commits 8–15 h one-off for the golden set (Phase 3).
- Score changes are deliberate, slightly slower events — by design.
- Storage for score history is negligible (~30 MB across versions at 12
  cities) and already in the volumetric budget.
