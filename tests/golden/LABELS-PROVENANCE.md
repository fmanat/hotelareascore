# Golden-set labels — provenance note (MUST be committed alongside hotels.csv)

## Who labeled, and how

These 50 labels were produced by **Claude (AI), not by the owner**, at the
owner's explicit request (owner declined the labeling task, 2026-09-06).
Method: judgment of each pinned location from world knowledge of the 12
cities' geography (stations, arterials, districts, parks), **independent of
the project's Overture data, formulas, and constants** — the same task a
human labeler performs from the Google Maps link, minus fresh eyes.

Consequences to respect:
1. `docs/scoring.md §4.1` ("Owner labels each") must be amended to reflect
   reality, and the `/methodology` page must NEVER claim human or owner
   validation of the calibration. "Calibrated against a labeled reference
   set" is accurate; "human-verified" is not.
2. This is weaker evidence than owner labels. The §4.2 bar (Spearman ≥ 0.6
   per dimension) still applies; treat marginal passes with more suspicion
   than you would with human labels.

## Scale orientation (matches the tool exactly)

transit 1=very inconvenient→5=very convenient · restaurants 1=none→5=abundant
· major_road_exposure 1=none→5=heavily exposed (correlates NEGATIVELY with
quietness_proxy) · nightlife 1=very quiet→5=very lively · family 1=poor→5=excellent.

## Prior-exposure flags (anchoring risk — run calibration with AND without)

Claude had already seen the pipeline's computed scores for these hotels
during earlier audits in this conversation (inspection-18.json):
- `8bca5fde…` Hotel Amano (London)
- `a94d53cb…` สุขุมวิทซอย11 (Bangkok)
Report Spearman both including and excluding these 2 rows.

## Lower-confidence labels (robustness set — rerun excluding these 7)

Location identified, but distance-level precision weaker:
`8490d0c3…` Ardra Guest House (Coulsdon) · `fbae2641…` Airport Hotels Bangkok
Travel Service (Lat Krabang) · `a303b42c…` Suksawad Hotel (Bangkok Noi) ·
`66caa9ab…` ホテルCOCO (Katsushika) · `4a4ae738…` Guesthouse SAKAE (Adachi) ·
`4b3d8f70…` "Dusit Thani Dubai" (pin is in JVT, see below) ·
`0e2256c4…` ibis budget City South (pin south of usual address).

## Data-quality specimens noticed while labeling (for the entity-QA backlog)

- `2bf89f8c…` **桝本屋酒店** is almost certainly a **liquor shop** (酒店 =
  sake shop in Japanese; "hotel" only in Chinese) — a CJK false hotel the
  English-only heuristic cannot catch, exactly the documented limitation.
- `346a49c0…` **アクアプレイス旭湯** looks like a **bathhouse/sento** (旭湯),
  possibly with lodging — verify before it ever enters an indexable cohort.
- `a9b48284…` **Souq Madinat Jumeirah** is a souk/venue, not a hotel.
- `b2a1e3f4…` **"Holiday Inn Paris Charles de Gaulle S.A.R.L."**: the name
  says CDG, the pin is Porte de Charenton (SE Paris) — a corporate-entity
  record. Labeled on the PIN location, per the tool's own rule.
- `756a9130…` **SpringHill Suites** pin is in **Carlstadt, New Jersey** —
  inside the "New York" bbox; far-from-center disclosure applies.

These 5 stay IN the calibration (they are locations like any other; the
labels judge the pin), but each is a candidate for the entity-QA backlog.
