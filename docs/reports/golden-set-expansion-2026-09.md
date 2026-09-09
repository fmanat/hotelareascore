# Golden-set expansion — non-urban hotel types (Bloc G)

- **Date:** 2026-09-10
- **Prompted by:** the same "Hilton Bangkok Suvarnabhumi Golf Resort &
  Spa" case that led to `docs/adr/015` — the original 50-hotel golden set
  (`tests/golden/selection.json`) is 100% conventional urban hotels; no
  golf resort, beach resort, stadium hotel, airport hotel, or countryside
  hotel was ever in the calibration reference set. If any dimension's
  formula has a systematic blind spot for these types, the existing
  Spearman checks (`docs/scoring.md §4.2`) could never have caught it —
  there was nothing in the set to catch it against.
- **Scope: selection only.** Per explicit instruction, these 6 hotels are
  **not labeled** — `tests/golden/hotels.csv` is untouched. They're added
  to `tests/golden/selection.json` (the tool's single source of truth,
  `tools/golden-labeler/README.md`), ready for the next labeling pass via
  `tools/golden-labeler/build.py`.

## Selection method

Real hotels, found by querying live Overture data (release `2026-08-19.0`)
across the 12 city bboxes, not picked from memory:

- **Golf/beach**: reused the adjacency analysis from
  `docs/reports/destination-type-detection-feasibility.md` (hotel ↔
  nearest `golf_course`/`sand`/`beach` polygon distance).
- **Stadium**: `land_use` `recreation`/`stadium` polygons (222 across the
  12 bboxes, confirmed via direct query) ↔ nearest hotel, ≤1,200m.
- **Airport**: `places` `taxonomy.primary = 'airport'` (already the exact
  category `quietness_proxy`'s penalty term uses, `taxonomy-mapping.yml`)
  ↔ nearest hotel, ≤3,000m. **Found real Overture data-quality noise
  here**: several "airport" points in this theme are mislabeled or
  misplaced (e.g. a point named "Thailand International Airport
  (Bangkok)" inside the **Sydney** bbox) — candidates from this category
  were cross-checked against real-world knowledge before selection, not
  taken from raw nearest-distance alone.
- **Countryside**: reused `destination-type-detection-feasibility.md`'s
  "isolated, no qualifying amenity nearby" bucket, hand-picked for a case
  that's genuinely rural/quiet by character (not a highway motel — the
  bucket also contains those, and they're a different type, not wanted
  here).

**Bug found and fixed while doing this**: `hotels.parquet`'s `confidence`
column is on a **0–1 scale**; `selection.json`'s existing 50 entries store
confidence on a **0–100 scale** (compare `hotels.parquet`'s raw
`0.954` to `selection.json`'s existing convention of `95.4`). An
early version of the search script filtered on the wrong scale (`>= 60`
against 0–1 values) and silently returned zero candidates for every
category. New entries below are converted to the 0–100 scale, matching
the existing 50.

## The 6 selected

| Name | City | Type | balanced_score | Why it's isolated (measured) |
|---|---|---|---:|---|
| Hilton Bangkok Suvarnabhumi Golf Resort & Spa | Bangkok | golf resort | 19.0 | 237m from a golf course; walkability_density 10.8 |
| Burj Al Arab Jumeirah Beach | Dubai | beach hotel | 31.7 | 21m from beach; walkability_density 33.7 |
| The Elton John Suite Watford Football Club | London | stadium hotel | 52.0 | 59m from Vicarage Road (Watford FC) |
| YOTELAIR Singapore Changi | Singapore | airport hotel | 54.1 | 12m from Jewel Changi; quietness_proxy 1.2 (correct — right next to an airport) |
| Les Etangs de Corot | Paris (Ville-d'Avray) | countryside hotel | 28.1 | walkability_density 24.0, no qualifying amenity within range — genuinely quiet/rural, not a destination case |
| Corporate Box - SCG | Sydney | stadium hotel (2nd example) | 59.0 | 28m from Sydney Cricket Ground |

Two stadium examples deliberately — a brand-new type with only one
exemplar is a thin base; a second, independently-verified case (different
city, different sport) reduces the risk of one mislabeled/misidentified
record skewing whatever the eventual label signal shows for this type.

Full rationale per hotel is in `selection.json`'s `selection_reason`
field — this report is a summary, not the source of truth.

## Explicitly not done here (per instruction)

- No labels assigned (`tests/golden/hotels.csv` unchanged, 50 rows).
- No calibration re-run against these 6 (nothing to calibrate against
  without labels).
- `tools/golden-labeler/dist/golden-labeler.html` was rebuilt locally to
  confirm all 56 hotels embed correctly (blind fields only — id, name,
  city, locality, lat, lon; `dist/` stays gitignored per the tool's own
  README) — publishing it as an Artifact for the owner to actually label
  is a separate, later action, not done in this pass.
