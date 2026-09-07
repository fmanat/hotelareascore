# Pilot cohort proposal v2 (Bloc D, overnight mission; revised 2026-09-07)

> **200 hotels proposed** across 12 cities. Report only -- no page_publication change, no indexing flag touched. Full detail: [pilot-cohort-proposal.csv](pilot-cohort-proposal.csv).

> **v2 changes from v1 (owner audit, 2026-09-07):** added gate 12 (Latin-script name -- v1 had 19/200 non-Latin-script entries, several non-hotels); excluded 3 known-bad-geocode records (entity_qa.KNOWN_BAD_GEOCODE) that were never valid candidates in the first place -- full detail in [destination-name-mismatch-audit.md](destination-name-mismatch-audit.md) and `docs/STATE.md`'s entity-QA specimens.

## Method

Gates 1 (confidence >= 80), 2 (identity reliable -- no dedupe merge needed), 3 (all 6 dimensions present), 4 (>=1 nearby fact), 6 (not a numeric-name record), 8 (no unresolved duplicate-coordinate cluster), 12 (Latin-script name -- added 2026-09-07 after an owner audit found 19/200 v1 candidates in non-Latin scripts, several of them non-hotels; see docs/seo-policy.md §2 and docs/STATE.md's entity-QA specimens) from docs/seo-policy.md §4 were computed per hotel and used to filter candidates. Gates 5, 9, 10 are structurally true for every city in this dataset (baseline exists, >=1000 hotels means comparison content always exists, scores are never keyword-stuffed prose by design). Gate 7 (demonstrated demand OR editorial selection) is the editorial branch for all 200 -- no live traffic exists yet to demonstrate demand. Gate 11 (affiliate resolvable OR consciously published without CTA) is the "without CTA" branch for all 200, per this run's explicit instruction -- no affiliate program exists yet.

Within gate-passing candidates: ~70/30 independent/chain weighting (139 independent, 61 chain -- 70%/30%), picked by "distinctiveness" (max absolute deviation from the city's own median across the 6 dimensions -- docs/seo-policy.md §2: "a hotel where our data tells a story beats a generic one"), spread across all 12 cities within the 12-25/city range from docs/seo-policy.md §2.

## Per-city breakdown

| City | Selected | Independent | Chain | Candidate pool (gates 1-8) |
|---|---:|---:|---:|---:|
| london | 25 | 18 | 7 | 4092 |
| bangkok | 25 | 18 | 7 | 4048 |
| paris | 25 | 18 | 7 | 3435 |
| rome | 25 | 18 | 7 | 4680 |
| barcelona | 12 | 8 | 4 | 1660 |
| amsterdam | 12 | 8 | 4 | 1012 |
| lisbon | 12 | 8 | 4 | 1211 |
| sydney | 12 | 8 | 4 | 983 |
| tokyo | 12 | 8 | 4 | 1030 |
| dubai | 13 | 9 | 4 | 1703 |
| new_york | 15 | 10 | 5 | 2051 |
| singapore | 12 | 8 | 4 | 1079 |

## Top 5 most distinctive picks per city

**london**

| Hotel | Chain? | Confidence | Balanced | Distinctiveness |
|---|---|---:|---:|---:|
| Darent Hulme Barn | independent | 81 | 22 | 83.5 |
| Laxton Hall | independent | 83 | 37 | 83.4 |
| Fosters Bed and Breakfast | independent | 92 | 32 | 83.4 |
| The Marriot Hotel | independent | 82 | 25 | 83.4 |
| Ritz Hotel London | independent | 82 | 27 | 83.4 |

**bangkok**

| Hotel | Chain? | Confidence | Balanced | Distinctiveness |
|---|---|---:|---:|---:|
| H2DO Hotel | independent | 82 | 17 | 84.9 |
| Chai Na Resort | independent | 82 | 16 | 83.6 |
| Narisa. Villege | independent | 80 | 24 | 82.6 |
| Inkgold Hotel & Cafe | independent | 81 | 20 | 81.5 |
| Coconut Lane Bangkok | independent | 88 | 24 | 81.3 |

**paris**

| Hotel | Chain? | Confidence | Balanced | Distinctiveness |
|---|---|---:|---:|---:|
| Les Bouvreuils | independent | 82 | 17 | 85.0 |
| Chatou Île des Impressionnistes | independent | 84 | 27 | 85.0 |
| Club des Loges | independent | 86 | 29 | 85.0 |
| Mount St Michel | independent | 87 | 25 | 85.0 |
| Le Relais de la Malmaison | independent | 88 | 22 | 85.0 |

**rome**

| Hotel | Chain? | Confidence | Balanced | Distinctiveness |
|---|---|---:|---:|---:|
| Hotel Zone | independent | 94 | 31 | 84.5 |
| Hotel Villa Maria Regina | independent | 82 | 20 | 84.5 |
| Hotel Romulus | independent | 94 | 17 | 84.5 |
| Giardino Degli Aranci b&b - Bed and Breakfast Roma | independent | 81 | 16 | 84.5 |
| B&B Maru Shelter | independent | 89 | 34 | 84.5 |

**barcelona**

| Hotel | Chain? | Confidence | Balanced | Distinctiveness |
|---|---|---:|---:|---:|
| Gran Hotel La Florida | independent | 87 | 22 | 85.0 |
| METT Barcelona | independent | 82 | 20 | 85.0 |
| Hotel Torre Barcelona | independent | 87 | 20 | 85.0 |
| GRACIAS PACO | independent | 90 | 36 | 83.8 |
| Hotel Campanile | independent | 87 | 51 | 83.8 |

**amsterdam**

| Hotel | Chain? | Confidence | Balanced | Distinctiveness |
|---|---|---:|---:|---:|
| Hotel Campanile Amsterdam | independent | 82 | 21 | 84.6 |
| Boathouse Amsterdam | independent | 81 | 22 | 84.6 |
| BB Noord en Park | independent | 88 | 28 | 84.6 |
| The Lake Hotel Amsterdam Airport | independent | 82 | 23 | 84.6 |
| Amsterdam Farm Lodge | independent | 87 | 24 | 84.6 |

**lisbon**

| Hotel | Chain? | Confidence | Balanced | Distinctiveness |
|---|---|---:|---:|---:|
| Alvalade Palace | independent | 84 | 20 | 85.0 |
| Lisboa Camping & Bungalows | independent | 88 | 20 | 80.4 |
| Casa do Presidente | independent | 87 | 25 | 79.0 |
| StayUpon Hotels | independent | 90 | 52 | 76.3 |
| Grupo Pestana Pousadas | independent | 92 | 50 | 76.3 |

**sydney**

| Hotel | Chain? | Confidence | Balanced | Distinctiveness |
|---|---|---:|---:|---:|
| The Kilns | independent | 81 | 24 | 84.2 |
| Nesuto Parramatta Sydney Apartment Hotel | independent | 84 | 21 | 84.2 |
| Bondi Hotel | independent | 85 | 29 | 84.2 |
| The Wem Hotel | independent | 81 | 24 | 84.2 |
| Ashfield Boarding House | independent | 84 | 26 | 84.2 |

**tokyo**

| Hotel | Chain? | Confidence | Balanced | Distinctiveness |
|---|---|---:|---:|---:|
| Eurasian | independent | 81 | 44 | 85.0 |
| Family Resort Fifty's Tokyo | independent | 87 | 48 | 84.5 |
| The Royal Park Hotel Maihama Resort Tokyo-Bay | independent | 89 | 47 | 84.5 |
| Tokyo Ariake Bay Hotel | independent | 92 | 41 | 84.5 |
| J's Backpackers | independent | 93 | 33 | 84.5 |

**dubai**

| Hotel | Chain? | Confidence | Balanced | Distinctiveness |
|---|---|---:|---:|---:|
| Le Méridien Fairway | independent | 84 | 12 | 81.3 |
| Ecos Dubai Hotel at Al Furjan, Managed by HMH | independent | 88 | 18 | 81.2 |
| OYO 968 Home 2005A Sobha creek Vistas 1BR | chain | 82 | 23 | 81.2 |
| OYO 1008 Home OYO The Nook-1 | chain | 82 | 22 | 81.0 |
| OYO HOME 1560 Furnished 1bed Apartment At Azizi Aliyah | chain | 82 | 21 | 80.1 |

**new_york**

| Hotel | Chain? | Confidence | Balanced | Distinctiveness |
|---|---|---:|---:|---:|
| Howard Johnson | independent | 82 | 15 | 84.9 |
| Alpha Lodge | independent | 92 | 26 | 84.9 |
| The Sagamore Resort | independent | 80 | 30 | 84.9 |
| Hampton Inn Ridgefield Park | independent | 82 | 14 | 84.9 |
| Comfort Suites | independent | 88 | 29 | 84.9 |

**singapore**

| Hotel | Chain? | Confidence | Balanced | Distinctiveness |
|---|---|---:|---:|---:|
| Cooliv | independent | 86 | 26 | 84.8 |
| S11 Dormitory at Punggol | independent | 83 | 23 | 84.8 |
| Cassia | independent | 86 | 24 | 84.8 |
| Changi Coast Adventure Centre | independent | 88 | 24 | 84.8 |
| Singapore Boys' Home | independent | 82 | 27 | 84.8 |

## What this is not

- Not a page_publication change -- that table doesn't exist yet (Bloc C). This is the candidate list for whoever builds the Phase 4 publication step.
- Not a demand signal -- gate 7's "editorial selection" branch means this list reflects data quality and distinctiveness, not measured interest. The 90-day measurement protocol (docs/seo-policy.md §5) starts only once these are actually indexed.
- Not final -- the owner should sanity-check a sample before Phase 4, same as every other automated selection in this project.
- **Worth a second look before Phase 4:** "distinctiveness" here is *undirected* (max absolute deviation from the city median, either way) -- a hotel that scores unusually LOW on a dimension (e.g. very poor transit access) counts as just as "distinctive" as one that scores unusually HIGH, and some low-balanced-score hotels are in this list for exactly that reason (see the per-city tables above). That is a defensible reading of docs/seo-policy.md §2's "tells a story" language (a clearly-quiet-but-far-from-transit hotel is a real, useful story), but it's an interpretation, not the only one -- if the owner wants the pilot cohort biased toward hotels that look good rather than merely distinctive, that's a one-line change to this script's distinctiveness formula (e.g. weight positive deviations only, or gate on balanced_score as well).