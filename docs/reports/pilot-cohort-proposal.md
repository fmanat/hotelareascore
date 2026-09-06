# Pilot cohort proposal (Bloc D, overnight mission)

> **200 hotels proposed** across 12 cities. Report only -- no page_publication change, no indexing flag touched. Full detail: [pilot-cohort-proposal.csv](pilot-cohort-proposal.csv).

## Method

Gates 1 (confidence >= 80), 2 (identity reliable -- no dedupe merge needed), 3 (all 6 dimensions present), 4 (>=1 nearby fact), 6 (not a numeric-name record), 8 (no unresolved duplicate-coordinate cluster) from docs/seo-policy.md §4 were computed per hotel and used to filter candidates. Gates 5, 9, 10 are structurally true for every city in this dataset (baseline exists, >=1000 hotels means comparison content always exists, scores are never keyword-stuffed prose by design). Gate 7 (demonstrated demand OR editorial selection) is the editorial branch for all 200 -- no live traffic exists yet to demonstrate demand. Gate 11 (affiliate resolvable OR consciously published without CTA) is the "without CTA" branch for all 200, per this run's explicit instruction -- no affiliate program exists yet.

Within gate-passing candidates: ~70/30 independent/chain weighting (138 independent, 62 chain -- 69%/31%), picked by "distinctiveness" (max absolute deviation from the city's own median across the 6 dimensions -- docs/seo-policy.md §2: "a hotel where our data tells a story beats a generic one"), spread across all 12 cities within the 12-25/city range from docs/seo-policy.md §2.

## Per-city breakdown

| City | Selected | Independent | Chain | Candidate pool (gates 1-8) |
|---|---:|---:|---:|---:|
| london | 25 | 18 | 7 | 4110 |
| bangkok | 25 | 18 | 7 | 6294 |
| paris | 22 | 15 | 7 | 3450 |
| rome | 25 | 18 | 7 | 4684 |
| barcelona | 12 | 8 | 4 | 1666 |
| amsterdam | 12 | 8 | 4 | 1012 |
| lisbon | 12 | 8 | 4 | 1213 |
| sydney | 12 | 8 | 4 | 990 |
| tokyo | 17 | 12 | 5 | 2663 |
| dubai | 12 | 8 | 4 | 1783 |
| new_york | 14 | 9 | 5 | 2057 |
| singapore | 12 | 8 | 4 | 1106 |

## Top 5 most distinctive picks per city

**london**

| Hotel | Chain? | Confidence | Balanced | Distinctiveness |
|---|---|---:|---:|---:|
| The Hindes Hotel | independent | 94 | 50 | 85.0 |
| Lindal Hotel | independent | 87 | 47 | 85.0 |
| The Central Hotel | independent | 87 | 54 | 85.0 |
| Darent Hulme Barn | independent | 81 | 24 | 83.5 |
| The Canopy | independent | 81 | 23 | 83.4 |

**bangkok**

| Hotel | Chain? | Confidence | Balanced | Distinctiveness |
|---|---|---:|---:|---:|
| H2DO Hotel | independent | 82 | 17 | 84.9 |
| ท่าเริอพูลพิพัฒ | independent | 80 | 16 | 84.9 |
| The Grand Rama II. เดอะแกรนด์ พระราม2 | independent | 80 | 18 | 83.7 |
| หมู่บ้านนวธานี | independent | 83 | 17 | 83.6 |
| Chai Na Resort | independent | 82 | 16 | 83.6 |

**paris**

| Hotel | Chain? | Confidence | Balanced | Distinctiveness |
|---|---|---:|---:|---:|
| Les Bouvreuils | independent | 82 | 21 | 85.0 |
| Le Relais de la Malmaison | independent | 88 | 22 | 85.0 |
| Club des Loges | independent | 86 | 29 | 85.0 |
| Mount St Michel | independent | 87 | 27 | 85.0 |
| Chatou Île des Impressionnistes | independent | 84 | 28 | 85.0 |

**rome**

| Hotel | Chain? | Confidence | Balanced | Distinctiveness |
|---|---|---:|---:|---:|
| Hotel Meeting | independent | 88 | 26 | 85.0 |
| Hotel Zone | independent | 94 | 31 | 84.5 |
| Happy at Rome | independent | 87 | 43 | 84.5 |
| Nataly's House | independent | 89 | 27 | 84.5 |
| Aurelia House And Loft | independent | 86 | 25 | 84.5 |

**barcelona**

| Hotel | Chain? | Confidence | Balanced | Distinctiveness |
|---|---|---:|---:|---:|
| Gran Hotel La Florida | independent | 87 | 24 | 85.0 |
| METT Barcelona | independent | 82 | 22 | 85.0 |
| Hotel Torre Barcelona | independent | 87 | 21 | 85.0 |
| GRACIAS PACO | independent | 90 | 38 | 83.8 |
| Hotel Campanile | independent | 87 | 53 | 83.8 |

**amsterdam**

| Hotel | Chain? | Confidence | Balanced | Distinctiveness |
|---|---|---:|---:|---:|
| Hotel Campanile Amsterdam | independent | 82 | 21 | 84.6 |
| The Lake Hotel Amsterdam Airport | independent | 82 | 24 | 84.6 |
| Boathouse Amsterdam | independent | 81 | 22 | 84.6 |
| BB Noord en Park | independent | 88 | 28 | 84.6 |
| Amsterdam Farm Lodge | independent | 87 | 25 | 84.6 |

**lisbon**

| Hotel | Chain? | Confidence | Balanced | Distinctiveness |
|---|---|---:|---:|---:|
| Alvalade Palace | independent | 84 | 20 | 85.0 |
| Lisboa Camping & Bungalows | independent | 88 | 19 | 80.4 |
| Casa do Presidente | independent | 87 | 24 | 79.0 |
| Grupo Pestana Pousadas | independent | 92 | 50 | 76.3 |
| Chelas zona N2 | independent | 86 | 37 | 76.3 |

**sydney**

| Hotel | Chain? | Confidence | Balanced | Distinctiveness |
|---|---|---:|---:|---:|
| The Kilns | independent | 81 | 26 | 84.2 |
| Q Station Sydney Harbour National Park | independent | 81 | 23 | 84.2 |
| Lyrebird Bed & Breakfast | independent | 85 | 29 | 84.2 |
| Medina Serviced Apartments | independent | 81 | 22 | 84.2 |
| Horizon Sands Resort, Dee Why Beach  NSW | independent | 82 | 27 | 84.2 |

**tokyo**

| Hotel | Chain? | Confidence | Balanced | Distinctiveness |
|---|---|---:|---:|---:|
| Eurasian | independent | 81 | 44 | 85.0 |
| 舞濱歐亞溫泉飯店 | independent | 83 | 43 | 85.0 |
| The Royal Park Hotel Maihama Resort Tokyo-Bay | independent | 89 | 48 | 84.5 |
| セミナーハウスフォーリッジ | independent | 93 | 42 | 84.5 |
| ファミリーロッジ旅籠屋東京新木場店 | independent | 88 | 27 | 84.5 |

**dubai**

| Hotel | Chain? | Confidence | Balanced | Distinctiveness |
|---|---|---:|---:|---:|
| Le Méridien Fairway | independent | 84 | 12 | 81.3 |
| Ecos Dubai Hotel at Al Furjan, Managed by HMH | independent | 88 | 18 | 81.2 |
| OYO 968 Home 2005A Sobha creek Vistas 1BR | chain | 82 | 25 | 81.2 |
| OYO 1008 Home OYO The Nook-1 | chain | 82 | 23 | 81.0 |
| OYO HOME 1560 Furnished 1bed Apartment At Azizi Aliyah | chain | 82 | 23 | 80.1 |

**new_york**

| Hotel | Chain? | Confidence | Balanced | Distinctiveness |
|---|---|---:|---:|---:|
| Howard Johnson | independent | 82 | 18 | 84.9 |
| Alpha Lodge | independent | 92 | 28 | 84.9 |
| The Sagamore Resort | independent | 80 | 32 | 84.9 |
| Hampton Inn Ridgefield Park | independent | 82 | 16 | 84.9 |
| SpringHill Suites | independent | 82 | 18 | 84.9 |

**singapore**

| Hotel | Chain? | Confidence | Balanced | Distinctiveness |
|---|---|---:|---:|---:|
| Holi 1Medini Suite | independent | 81 | 23 | 84.8 |
| Singapore Boys' Home | independent | 82 | 27 | 84.8 |
| S11 Dormitory at Punggol | independent | 83 | 24 | 84.8 |
| Cooliv | independent | 86 | 27 | 84.8 |
| Estuary Singapore | independent | 83 | 24 | 84.8 |

## What this is not

- Not a page_publication change -- that table doesn't exist yet (Bloc C). This is the candidate list for whoever builds the Phase 4 publication step.
- Not a demand signal -- gate 7's "editorial selection" branch means this list reflects data quality and distinctiveness, not measured interest. The 90-day measurement protocol (docs/seo-policy.md §5) starts only once these are actually indexed.
- Not final -- the owner should sanity-check a sample before Phase 4, same as every other automated selection in this project.
- **Worth a second look before Phase 4:** "distinctiveness" here is *undirected* (max absolute deviation from the city median, either way) -- a hotel that scores unusually LOW on a dimension (e.g. very poor transit access) counts as just as "distinctive" as one that scores unusually HIGH, and some low-balanced-score hotels are in this list for exactly that reason (see the per-city tables above). That is a defensible reading of docs/seo-policy.md §2's "tells a story" language (a clearly-quiet-but-far-from-transit hotel is a real, useful story), but it's an interpretation, not the only one -- if the owner wants the pilot cohort biased toward hotels that look good rather than merely distinctive, that's a one-line change to this script's distinctiveness formula (e.g. weight positive deviations only, or gate on balanced_score as well).