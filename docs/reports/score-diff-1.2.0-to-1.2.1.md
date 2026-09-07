# family_convenience 1.2.0 -> 1.2.1 diff (all 12 cities, all hotels)

> docs/scoring.md §5 point 2. Recomputed both formulas live from the
> unchanged green_spaces source (see script docstring for why this
> isn't a snapshot diff) -- only family_convenience changes; every
> other dimension and the golden-set labels are untouched by this ADR.

| City | n hotels | mean shift | hotels moved >15pts | % |
|---|---:|---:|---:|---:|
| london | 4398 | -8.2 | 1100 | 25.0% |
| bangkok | 7546 | -14.3 | 3095 | 41.0% |
| paris | 3582 | -5.7 | 576 | 16.1% |
| rome | 5040 | -10.4 | 1559 | 30.9% |
| barcelona | 1720 | -3.6 | 197 | 11.5% |
| amsterdam | 1071 | -7.9 | 282 | 26.3% |
| lisbon | 1289 | -11.4 | 508 | 39.4% |
| sydney | 1080 | -3.6 | 126 | 11.7% |
| tokyo | 2745 | -5.8 | 636 | 23.2% |
| dubai | 2067 | -15.7 | 910 | 44.0% |
| new_york | 2194 | -6.3 | 353 | 16.1% |
| singapore | 1238 | -8.1 | 286 | 23.1% |
| **all 12** | **33970** | | **9628** | **28.3%** |

## Largest movers across all 12 cities

| City | Hotel | old (1.2.0) | new (1.2.1) | delta |
|---|---|---:|---:|---:|
| dubai | Ramada Downtown Burj Dubai Hotel | 99.0 | 0.0 | -99.0 |
| bangkok | โตเกียวรีสอร์ท | 91.9 | 0.0 | -91.9 |
| bangkok | บ้านเนตรนิธิอนันต์ | 91.8 | 0.0 | -91.8 |
| bangkok | Golden Tulip Sovereign Hotel, Bangkok | 99.7 | 9.1 | -90.6 |
| bangkok | Banyan Tree Hotel - Bangkok, Tayland | 99.9 | 13.1 | -86.8 |
| dubai | Emirates Grand Hotel | 96.6 | 10.0 | -86.6 |
| dubai | Flat 208 Room 1,Radisson Blu Hotel Ladies Staff Accommodation | 99.1 | 14.0 | -85.0 |
| bangkok | Bandara Don Moeng Bangkok | 99.0 | 14.3 | -84.7 |
| dubai | The Spa at Four Seasons Hotel Dubai International Financial Centre | 90.5 | 8.4 | -82.1 |
| dubai | Kempinski Hotel and Residences Palm Jumeirah | 96.2 | 16.7 | -79.5 |
| new_york | Hampton Inn & Suites Newark Airport Elizabeth | 90.8 | 12.8 | -78.0 |
| new_york | Embassy Suites by Hilton Newark Airport | 90.5 | 16.9 | -73.6 |
| new_york | Extended Stay America | 87.8 | 15.1 | -72.8 |
| rome | OC Hotel | 91.4 | 18.9 | -72.5 |
| paris | Nevillisation Hôtels & Resorts | 97.5 | 25.1 | -72.4 |
