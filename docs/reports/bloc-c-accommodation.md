# Bloc C — accommodation types

Release 2026-08-19.0; all 12 city datasets after A/B. Metadata only: no rows re-ingested or removed, no scores/slugs changed. Only `hotel` may pass the type gate; every other type remains searchable and noindex. Category is not external reception verification.

| City | Total | hotel | aparthotel | serviced-apartment | whole-home | hostel | guesthouse-B&B | unknown |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| london | 4364 | 3120 | 25 | 193 | 151 | 238 | 436 | 201 |
| bangkok | 7517 | 5660 | 3 | 112 | 80 | 872 | 209 | 581 |
| paris | 3568 | 3198 | 55 | 85 | 45 | 58 | 114 | 13 |
| rome | 5030 | 2658 | 4 | 291 | 87 | 96 | 1827 | 67 |
| barcelona | 1704 | 1061 | 16 | 105 | 127 | 258 | 97 | 40 |
| amsterdam | 1065 | 780 | 6 | 3 | 36 | 54 | 168 | 18 |
| lisbon | 1282 | 869 | 7 | 12 | 104 | 182 | 102 | 6 |
| sydney | 1067 | 712 | 15 | 89 | 46 | 79 | 62 | 64 |
| tokyo | 2734 | 2234 | 5 | 24 | 4 | 160 | 138 | 169 |
| dubai | 2060 | 1462 | 129 | 54 | 260 | 41 | 18 | 96 |
| new_york | 2174 | 1788 | 1 | 30 | 8 | 56 | 111 | 180 |
| singapore | 1214 | 910 | 0 | 51 | 2 | 143 | 16 | 92 |
| **Total** | 33779 | 24452 | 266 | 1049 | 950 | 2237 | 3298 | 1527 |

## Rules and limitations

Explicit whole-unit names override generic hotel taxonomy. OYO Home is whole-home; OYO alone never changes type. Blueground furnished rentals are whole-home. Sonder/Domio without explicit property evidence are unknown; the JSON companion logs these cases. Apartments without service evidence are conservatively whole-home (this describes the available evidence, not a verified operating model). Hostel, B&B, serviced apartment and aparthotel are distinct. Home/House alone never changes hotel classification. Unknown is deliberately not guessed from lodge/inn/resort alone. Guesthouse/B&B remains noindex: the supplied data cannot establish staffed reception.

Sources: [OYO owner case](https://www.oyorooms.com/ae/192806/), [Blueground](https://www.theblueground.com/), [Overture taxonomy](https://docs.overturemaps.org/schema/reference/places/types/taxonomy/).

## Rejected lodging: report only, no re-ingestion

The classifier cannot establish that generic `lodging` entries are real hotels. Named/property-level review would be needed. Holiday rental home/cottage/cabin could become searchable whole homes after A/B and all ingestion QA, never automatically indexable hotels. Counts below are taxonomy-only upper bounds; they have NOT passed exclusions, deduplication or external verification.

| City | Rejected lodging | Generic unresolved lodging | Potential whole-home candidates |
|---|---:|---:|---:|
| london | 1096 | 749 | 257 |
| bangkok | 11265 | 11024 | 166 |
| paris | 565 | 326 | 216 |
| rome | 1649 | 521 | 1112 |
| barcelona | 363 | 178 | 166 |
| amsterdam | 134 | 94 | 24 |
| lisbon | 276 | 140 | 132 |
| sydney | 235 | 164 | 39 |
| tokyo | 554 | 477 | 38 |
| dubai | 656 | 486 | 144 |
| new_york | 1992 | 1831 | 80 |
| singapore | 1306 | 1238 | 38 |

No automatic recovery of the large Bangkok/NY/SG generic-lodging pool is justified. Zero recovered/ingested in this block.

## Validation

446 Python tests passed, one pre-existing xfail; 27 new C test cases plus a
Node build-guard test. Astro typecheck: zero errors/warnings. All 33,779 search
entries carry a type. SQL comparison preserved all original columns and rows
against the pre-C backups; no score files were written. The owner OYO 968 Home
case is whole-home. Fourteen mixed-operator records remain unknown (JSON log).
Full static build: 15,721 pages; SEO assertions passed. No deployment.
