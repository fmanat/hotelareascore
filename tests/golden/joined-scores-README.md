# Joined golden-set scores — provenance and reproduction

`joined-scores-<score_version>.csv` is the exact table
`scripts/calibrate_golden_set.py` computes its §4.2 Spearman correlations
from: the 50 `tests/golden/hotels.csv` labels, one row per hotel, joined
against that score_version's computed dimension scores
(`data/etl/<release>/<city>/hotel_scores.parquet`) and `balanced_score`/
`confidence`. Committed so the reported Spearman numbers are replayable
without re-running the ETL pipeline — read the CSV, compute Spearman
yourself, get the same numbers in the report.

- `joined-scores-1.0.1.csv` — the v1.0.1 formula (points-only
  family_convenience). Backs the calibration numbers in
  `docs/reports/phase-3-calibration-sensitivity-report.md`.
- `joined-scores-1.1.0.csv` — the v1.1.0 formula (family_convenience v2,
  land_use polygons — docs/adr/006). Backs the re-calibration numbers in
  the same report's addendum.

Columns: the 5 label columns from `hotels.csv` (`transit_convenience`,
`nearby_restaurants`, `major_road_exposure`, `nightlife_intensity`,
`park_family_convenience`), then the corresponding computed dimension
scores (`transit_access`, `food_essentials`, `quietness_proxy`,
`nightlife_access`, `family_convenience`), plus `balanced_score` and
`confidence`. Release `2026-08-19.0` for both files — only score_version
differs.

To regenerate for a new score_version after a re-score: run
`python3 scripts/calibrate_golden_set.py`, then copy
`docs/reports/phase-3-calibration-joined.csv` here as
`joined-scores-<new version>.csv`.
