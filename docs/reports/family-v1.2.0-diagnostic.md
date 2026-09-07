# family_convenience v1.2.0 — diagnostic (Bloc A step 1)

Owner ask: for 5 named hotels, list land_use polygons within ≤1km with
subtype/class, and confirm whether large green spaces (forest/nature/beach/
recreation) are excluded by the current (v1.1.0) filter or absent from the
source. Queried directly against the live Overture release
(`2026-08-19.0`), both `base/land_use` and `base/land` themes (the latter
not previously ingested — see below), sorted by approximate distance.

v1.1.0 filter recap: `land_use` polygons where `subtype = 'park'` (any
class) OR (`subtype = 'recreation'` AND `class = 'playground'`) — nothing
from `base/land` at all.

## Changi Lodge (Singapore, 1.31265, 103.99708)

| Source | Name | subtype/class | ~distance |
|---|---|---|---:|
| land_use | Changi Lodge 2 | residential/residential | 29 m |
| land_use | — | agriculture/meadow | 439 m |
| land_use | Sembcorp NEWater Plant | developed/industrial | 532 m |
| land_use | — | agriculture/meadow | 559 m |
| land_use | — | managed/grass | 635 m |
| land | — | forest/wood | 917 m |
| land | — | forest/wood | 1,071 m |

**Verdict: absent from the source, not excluded by the filter.** The
nearest genuinely green feature (managed/grass) is at 635m — already
outside family_convenience's 600m radius even under an expanded filter; the
nearest forest is at 917m. This hotel's `family_strict` label of 5 does not
correspond to any real nearby park/green polygon within radius, expanded
filter or not. Likely explanation: a labeling-construct issue (see the
calibration report's earlier hypothesis), not a data or filter gap for this
specific case.

> **Correction (owner review, v1.2.1 session):** this "labeling-construct
> issue" framing was wrong. 635 m is 35 m outside the 600 m radius — the
> real cause is the radius's hard cutoff, not the label. See
> `docs/reports/family-v1.2.1-recalibration.md`'s "known open limitation"
> section and `docs/scoring.md`.

## Crowne Plaza Rome St. Peter's (Rome, 41.88878, 12.42598)

| Source | Name | subtype/class | ~distance |
|---|---|---|---:|
| land_use | — | recreation/pitch | 100 m |
| land_use | — | recreation/pitch | 110 m |
| land_use | — | recreation/pitch | 127 m |
| land_use | — | recreation/track | 130 m |
| land_use | — | recreation/track | 146 m |
| land | — | shrub/scrub | 254 m |
| land | — | forest/wood | 263 m |
| land | — | forest/forest | 295-432 m (×2) |
| land | — | grass/grass | 389 m |

**Verdict: excluded by the current filter, not absent from the source.**
Five `recreation/pitch` and `recreation/track` polygons sit within 150m —
v1.1.0 only matches `recreation/playground`, so all of these are currently
invisible to the score. Forest and grass (base/land, not ingested at all)
add more real nearby green space. This is a genuine, fixable filter gap.

## Hotel Gilinsky (Amsterdam, 52.33923, 4.83038)

| Source | Name | subtype/class | ~distance |
|---|---|---|---:|
| land_use | — | managed/grass | 60-139 m (×6 within this range) |
| land | — | forest/forest | 112-213 m (×3) |
| land | — | tree/tree_row | 179-196 m (×3) |
| land | — | grass/grassland | 195 m |

**Verdict: absent from the current filter (both themes), not from the
source.** Six `managed/grass` polygons within 140m and forest within 213m —
substantial real green space immediately around this hotel that v1.1.0
cannot see at all (`managed/grass` isn't `park`, and `base/land` isn't
ingested). The single biggest fixable case of the five.

## Lisboa Camping & Bungalows (Lisbon, 38.72463, -9.20744)

| Source | Name | subtype/class | ~distance |
|---|---|---|---:|
| land_use | — | park/park | 78 m |
| land_use | Lisboa Camping | campground/camp_site | 142 m |
| land_use | — | recreation/pitch | 209-325 m (×4) |
| land_use | Parque Urbano do Alto da Cabreira | park/park | 318 m |
| land | — | tree/tree_row | 46-199 m (×several) |
| land | — | shrub/scrub | 136 m |
| land | — | forest/wood | 168 m |

**Verdict: already fixed by v1.1.0.** The `park/park` polygon at 78m is
already inside the v1.1.0 filter (`subtype = 'park'`, any class) —
`family_convenience` for this hotel is **44.1** in the v1.1.0 scores
(`tests/golden/joined-scores-1.1.0.csv`), not 0. Included here per the
owner's list for completeness; no further gap to close, though the nearby
`recreation/pitch` polygons would add a small amount more once the
recreation-class expansion (below) ships.

## Holiday Inn Paris CDG S.A.R.L. — Charenton pin (Paris, 48.83400, 2.39591)

| Source | Name | subtype/class | ~distance |
|---|---|---|---:|
| land_use | École primaire | education/school | 44 m |
| land_use | — | managed/grass | 98 m |
| land_use | École maternelle des Meuniers | education/school | 123 m |
| land_use | École primaire de Wattignies | education/school | 167 m |
| land_use | Cimetière de Bercy | cemetery/cemetery | 184 m |
| land_use | — | horticulture/flowerbed | 247 m |
| land | — | tree/tree | 10-47 m (×8, individual street trees) |

**Verdict: mostly absent from the source (as a *family-relevant* space),
one small fixable gap.** The one `managed/grass` polygon at 98m would newly
count once that class is added. Everything else nearby is schools, a
cemetery, a flowerbed, and individual street trees — correctly not
family-green-space by any reasonable definition, filter gap or not. This
hotel (already flagged in the entity-QA backlog as a likely corporate
records, pin at Porte de Charenton rather than CDG airport) is not going to
score well on family_convenience no matter how the filter is tuned, and
that's plausibly the right answer.

## Conclusion — filter expansion is justified by direct evidence, not guesswork

Queried the full, real subtype/class distribution for both themes against a
live extract (London bbox) rather than assuming category names:

- `base/land_use`: 60 distinct subtype/class pairs found, including
  `managed/grass` (34,290), `recreation/pitch` (13,154),
  `recreation/recreation_ground` (1,987), `recreation/track` (503),
  `protected/nature_reserve` (262), `entertainment/zoo` (14 — a real zoo
  **polygon**, contradicting v1.1.0/ADR-006's assumption that zoo has no
  land_use footprint).
- `base/land` (not previously ingested at all): `forest/wood` (17,324),
  `forest/forest` (1,667), `grass/grass` (1,159), `grass/grassland` (742),
  `sand/beach` (113, confirmed present in Sydney/Dubai too — the "plage
  aménagée" case).
- Deliberately **excluded**, with reasons: `horticulture/*` (28,030
  `garden` alone — almost certainly private residential gardens, would
  massively pollute the signal), `golf/*` (private/members courses, not a
  walkable public family amenity despite being green), `agriculture/*`
  (private farmland — explains Changi Lodge's nearby "meadow" correctly not
  counting), `campground/camp_site` (ambiguous, often the lodging property
  itself), `recreation/stadium`/`recreation/marina` (ticketed venue / boat
  marina, not general green space), `tree/tree`+`tree/tree_row` (242,527 +
  4,768 individual street trees in London alone — a tree-lined street is
  not a park), `shrub/*`, `wetland/*`, `rock/*`, `physical/*` (not usable
  leisure space).

See `docs/adr/007-family-convenience-v1.2.0-green-classes.md` for the
resulting taxonomy-mapping.yml change and `docs/scoring.md` for the updated
formula description.
