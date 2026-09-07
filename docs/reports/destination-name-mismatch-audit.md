# Destination-name mismatch audit (Bora Bora investigation + systematic search)

> Owner audit finding, this session: "Bora Bora Nui Hilton Resort And Spa"
> classified in Sydney's dataset. Investigated the root cause, fixed it,
> and searched systematically for the same pattern across all 12 cities.

## Bora Bora: root cause

```
id: a89707ca-d74e-43f7-a6bb-4c9026608941
name: Bora Bora Nui Hilton Resort And Spa
lat/lon: -33.847172, 151.109802   (Sydney Harbour — inside Sydney's bbox)
address_locality: Sydney
address_region: NSW
address_country: AU
address_freeform: "BP 502 Vaitape, Bora Bora, 98730, French Polynesia"
confidence: 88.0
```

**Cause: an Overture source-data geocoding error, not a dedupe or entity-QA
bug on our side.** The record's own `address_freeform` field — which we
don't currently read for anything except display — correctly identifies a
real Bora Bora Nui Resort & Spa (a genuine Hilton property in French
Polynesia), but the record's `lat`/`lon` and its structured
`address_locality`/`address_region`/`address_country` fields all place it
in Sydney, Australia — roughly 14,000 km away. The existing
`_locality_mismatch` disclosure (`webdata.py`) could not catch this: it
compares `address_country`/`address_region` against the city's expected
values, and both fields say `AU`/`NSW` — consistent with Sydney, even
though the freeform text contradicts them. The bug is upstream, in
whichever Overture source contributed this specific record's coordinates;
nothing we do can correct the true coordinates without inventing data we
don't have, so the only honest fix is exclusion.

## Systematic search for the same pattern

Searched all 12 cities' `hotels.parquet` for names containing a famous,
geographically distinctive destination word (bora bora, maldives,
santorini, bali, tahiti, zanzibar, seychelles, mykonos, fiji, phuket,
ibiza, cancun, goa) — **21 hits**, then verified each one against its own
`address_freeform` (or, where absent, its recorded confidence and
locality) before deciding anything. Most hits were not genuine mismatches.

### Per-city hit count

| City | Hits | Confirmed mismatch (excluded) | Substring false positive | Ambiguous / not acted on |
|---|---:|---:|---:|---:|
| London | 2 | 1 | 1 | 0 |
| Bangkok | 5 | 0 | 1 | 4 |
| Rome | 2 | 0 | 1 | 1 |
| Lisbon | 2 | 0 | 1 | 1 |
| Sydney | 3 | 2 | 0 | 1 |
| Tokyo | 4 | 0 | 0 | 4 |
| Singapore | 3 | 1 | 1 | 1 |
| **Total** | **21** | **4** | **5** | **12** |

### Confirmed mismatches — excluded (`entity_qa.KNOWN_BAD_GEOCODE`)

Each has its own `address_freeform` directly contradicting its extraction
city — not inferred from the name alone:

| Hotel | Extracted as | Real address (per its own record) |
|---|---|---|
| Bora Bora Nui Hilton Resort And Spa | Sydney | "BP 502 Vaitape, Bora Bora, 98730, French Polynesia" |
| Sheraton Fiji Resort | Sydney | "Danareu Island, Fiji" |
| Villa Uma Nina Bali | London | "Jalan Goa Tegeh, Banjar Kampial Jimbaran, Jimbaran, South Kuta, Badung Regency" (all real Bali sub-districts) |
| Kartika Plaza Hotel, Bali, Indonesia | Singapore | Name self-declares Bali; address_freeform says "Singapore Botanic Gardens, 1 Cluny Rd" — internally contradictory either way |

All 4 re-ingested out of their cities entirely (not just made
cohort-ineligible) — a wrongly-located record showing up as "a hotel in
Sydney" at all is actively misleading, independent of indexing status.
`london`, `sydney`, `singapore` re-ingested, re-scored, re-validated (all
pass); `pilot-cohort-proposal.md`/`.csv` regenerated afterward.

### Substring false positives (not real hits, not acted on)

The marker search itself matches substrings, so 5 of the 21 hits are
unrelated words that happen to contain a marker: "**Goa**t Kensington
High Street" / "Hotel **Bali**lla" (an Italian name, unrelated to Bali) /
"Madra**goa** House Apartments" (Madragoa is a real Lisbon neighborhood) /
"Baha**bali** Restaurant" (an Indian-film-reference restaurant name) /
"Go**goa**l Latkrabang". No exclusion needed — the search over-matches by
design (better to over-flag and triage than miss a real case).

### Ambiguous — checked, evidence insufficient to act

Same-pattern name, but no contradicting `address_freeform` to confirm a
real mismatch (excluding on name alone would risk the exact
false-exclusion failure mode `entity_qa.py`'s own history warns against):

- **Tokyo: "Petit Bali", "Petit Bali Ikebukuro" (×2), "Bali An Resort
  Forest Ikebukuro"** — all have real, specific Tokyo addresses (Kabukicho,
  Ikebukuro block/lot numbers). Exotic-destination theme names (Bali,
  Hawaii, etc.) are a well-documented real pattern in Japanese
  "love hotel"/theme-hotel naming — treated as likely genuine Tokyo
  businesses, not mislocated.
- **Lisbon: "Pensão Nova Goa"** — "Nova Goa" was the Portuguese colonial-era
  name for Panaji, Goa; a Lisbon guesthouse referencing Portugal's
  historical ties to Goa is a plausible genuine local name, not a
  geocoding error. No contradicting address found.
- **Rome: "Geo Zanzibar Resort"** — "Zanzibar" is a common Italian bar/venue
  theme name; no contradicting address found.
- **Bangkok: "มัลดีฟส์ Maldives"** — non-Latin name, so already excluded
  from pilot-cohort candidacy by gate 12 regardless; not independently
  verified as a geocoding error one way or the other.
- **Bangkok: "Sri-Panwa Phuket", "Aleenta Phuket"** — both real,
  well-known specific Phuket resort brands; geographically implausible in
  Bangkok (same country, ~700 km apart) but confidence is 62.7 and 56.6,
  both already below the pilot-cohort gate-1 threshold (80) — not
  cohort-relevant either way, logged here for a future data-quality pass
  rather than acted on now.
- **Bangkok: "Hotels in Phuket"** — reads like a directory/listing page
  name rather than one specific hotel (a different bug class: a possible
  non-hotel entity, not a location error). Confidence 55.4, already below
  gate 1. Logged, not investigated further.
- **Sydney: "Bali Villas Group"** — has a real, verifiable Sydney address
  (Alexandria, Maddox St) — not a geocoding error. Reads like a
  villa-rental booking agency rather than a hotel itself (a possible
  non-hotel entity, same family as the "Hotels in Phuket" case). Confidence
  77.0, below gate 1. Not acted on.
- **Singapore: "Bali Rani Hotel"** — a real, known Kuta-Bali hotel name;
  no `address_freeform` on this record to confirm or deny a mismatch, and
  confidence (72.5) is already below the pilot-cohort gate. Left
  unresolved rather than guessed at.

## What changed in the data

- `src/hotelareascore/entity_qa.py`: new `KNOWN_BAD_GEOCODE` dict (4
  entries, each documented with its evidence) + `is_known_bad_geocode()`,
  wired into `ingest.py` alongside (but tracked separately from) the
  existing `is_likely_non_hotel` entity-QA exclusion.
- Re-ingested, re-scored, re-validated: London (4397 hotels, was 4398),
  Sydney (1078, was 1080), Singapore (1237, was 1238).
- `docs/STATE.md`'s entity-QA specimens section updated with this fix
  (distinct from the still-open CJK/Thai non-hotel backlog, which remains
  unfixed).
