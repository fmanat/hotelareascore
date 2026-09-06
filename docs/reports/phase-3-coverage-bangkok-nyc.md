# Coverage check: Bangkok + New York "rejected lodging" — Batch 2 precondition

**Purpose:** the real precondition for Batch 2 (New York, Singapore) was
never "did the entity-QA exclusion heuristic ship" — that only removes
false hotels from the *included* set. It says nothing about whether real
hotels are missing from the *excluded* set. This report is that check:
a hand-classified sample of Bangkok's and New York's "rejected lodging"
places (Overture's `lodging`-hierarchy entries outside our v1 included
types — `docs/reports/data-proof-report-2026-08-19.0.md` "Rejects", and
`docs/reports/phase-3-batch-1-ingestion-report.md`).

**Do not start Batch 2 based on the entity-QA work alone** — this report
is the actual gate.

## Method

50 records sampled at random (seed fixed for reproducibility) from each
city's full rejected-lodging set (Bangkok: 50 of 11,265; New York: 50 of
2,065 — read-only Overture queries, no ingestion), then classified by hand
into: **legitimate lodging** (should probably be scored as a hotel),
**hospitality-adjacent** (a real hospitality company, but the record itself
reads as a corporate/brand entity rather than a specific bookable
property), **deliberately out of scope** (`holiday_rental_home`/
`campground` — working as designed, not a data-quality issue), **noise**
(not lodging-related at all), or **ambiguous** (a human reviewer without
local knowledge or a map lookup genuinely can't tell).

**Caveat on the numbers below:** 50 records is 0.4% of Bangkok's 11,265 and
2.4% of New York's 2,065 — small samples with real sampling variance,
adequate for a go/no-go read on Batch 2, not a precise rate. Treat every
percentage as ±5-10 points, not exact.

## Bangkok (n=50)

| Category | Count | % |
|---|---:|---:|
| Legitimate lodging | 5 | 10% |
| Noise | 29 | 58% |
| Ambiguous | 16 | 32% |

Bangkok's noise is dominated by one pattern: **residential housing-estate
names** ("หมู่บ้าน..." — "...Village") and **bare street/lane fragments**
("ซอย...") that carry no business identity at all — these look like
address-level geocoding artifacts, not lodging businesses, legitimate or
otherwise. The 5 legitimate misses follow a different pattern: Thai-language
lodging terms our (English-only) taxonomy vocabulary doesn't recognize —
"อพาร์ทเมนท์" (apartment), "แมนชั่น" (used in Thai for a long/short-stay
rental building, not literally "mansion"), "รีสอร์ท" (resort). Examples:

- **Legitimate:** "ปรีดา อพาร์ทเมนท์" (Preeda Apartment), "เกาะคู่รีสอร์ท เมียนม่าร์" (a resort), "วสันต์ แมนชั่น" (Wasan Mansion — a rental building)
- **Noise:** "หมู่บ้านนันทวัน" (Nanthawan Village — a housing estate), "ซอยรามคำแหง 33" (a street name, not a business), "บริษัท ปรีดา เรียล เอสเตส จำกัด" (Preeda Real Estate Co., Ltd.), "อำเภอเมือง จ.นนทบุรี" (a district name)
- **Ambiguous:** personal/family names with only a street address and no other identifying text — could be an informal short-term rental listing or could be nothing (e.g. "Inthapanya Family", "บ้านหนองพะอง")

## New York (n=50)

| Category | Count | % |
|---|---:|---:|
| Legitimate lodging (miscategorized) | 6 | 12% |
| Hospitality-adjacent (brand/management entity) | 2 | 4% |
| Deliberately out of scope (`holiday_rental_home`/`campground`) | 4 | 8% |
| Noise | 19 | 38% |
| Ambiguous | 19 | 38% |

New York's pattern is more actionable than Bangkok's: the legitimate misses
are almost all **`"[Name] Hotel" + LLC/Corp/Inc`** — the property's legal
ownership-entity name, carrying "Hotel" explicitly, e.g. "Surrey Hotel
Associates Llc" (The Surrey, a well-known Manhattan hotel), "Brittania 54th
Hotel Corp", "Granite Qp Hotel Llc", "Phoenix 39 St Hotel Inc". New York's
noise is dominated by a *different* pattern than Bangkok's: **NYCHA public
housing** ("Baruch Houses", "NYCHA - McKinley Houses", "St Mary Park
Houses"), **university dormitories** ("Weinstein Hall" — an NYU
residence), and **unrelated corporate entities** (real estate, investment,
pension-fund, medical-supply, retail businesses that happen to carry a
`lodging` taxonomy leaf for reasons unrelated to their actual business).

- **Legitimate:** "Surrey Hotel Associates Llc", "Ratan Group Hotel Llc", "Lake Placid Lodge Management, Llc"
- **Hospitality-adjacent:** "Sydell Scottsdale, Llc" (Sydell Group — owns The NoMad, The Ned NYC), "OYO USA" (a real short-term-rental chain's US entity)
- **Out of scope by design:** "Mulzac Family Vacation Rentals" (`holiday_rental_home`), "NYC Apartment" (`holiday_rental_home`), "The Double Daring Camp for Girls" / "Camp Hope" (`campground`) — correctly excluded, not a gap
- **Noise:** "Baruch Houses" (NYCHA public housing), "Weinstein Hall" (NYU dorm), "52 Restaurant Group Corp", "115 Ave Realty Llc", "Board Of Trustees Of Division A Annuity Fund"

## Recommendation

**Batch 2 (New York, Singapore) is acceptable to run as-is.** The coverage
gap is real, but:

- It's the **same order of magnitude** we already accepted for Phase 1
  (~10-16% of an already-secondary bucket), not a new or worse problem
  introduced by anything this session changed.
- The bulk of each city's rejected bucket (58% Bangkok, 46% New York
  combining noise + out-of-scope) is genuinely not lodging — a rescue rule
  aggressive enough to catch the legitimate misses risks pulling in public
  housing, real estate agencies, and street-address artifacts, which would
  be a worse outcome than the current gap.
- New York's ambiguous share (38%) and Bangkok's (32%) are large enough
  that even a careful human reviewer can't resolve most of them from the
  name alone — a real fix needs address/map verification per record, not
  a smarter regex.

**Follow-up worth scoping later (not blocking):** a conservative,
*separately tested* name-based **inclusion rescue** for the generic
`lodging` leaf specifically (not `holiday_rental_home`/`campground`, which
are working as designed) — e.g. `taxonomy.primary == 'lodging'` AND the
name contains an explicit lodging keyword (English: hotel/inn/lodge/resort;
Thai: อพาร์ทเมนท์/แมนชั่น/รีสอร์ท/โรงแรม). This should go through the same
iterate-against-real-data discipline that fixed `entity_qa.py`'s item (a) —
a first pass optimized for recall here would very plausibly reintroduce
false inclusions of noise, the mirror-image of that bug.

## Item 3: brand-allowlist / annex-word co-occurrence (logged, not fixed)

Per owner audit: `entity_qa.py`'s hospitality-brand allowlist is checked
*before* the non-hotel markers, so a hotel's own sub-venue (a restaurant,
spa, bar, parking garage, ballroom) still gets included as long as its name
contains a recognized brand token — "Royal Princess Dusit Restaurant" is
the case that surfaced this. Measured across all 10 ingested cities' 6
*included* hotel types (`taxonomy.primary`, not the rejected-lodging sample
above):

| City | Brand + annex-word records |
|---|---:|
| London | 4 |
| Bangkok | 11 |
| Paris | 0 |
| Rome | 1 |
| Barcelona | 2 |
| Amsterdam | 1 |
| Lisbon | 1 |
| Sydney | 2 |
| Tokyo | 2 |
| Dubai | 9 |
| **Total** | **33** |

Spot-checking the 33: most are genuine sub-venues sharing a parent hotel's
brand name ("Grand Ballroom, Shangri-La Hotel, Bangkok"; "SW7 Restaurant,
Melia Hotel"; "The Spa at Four Seasons Hotel Dubai..."). A few are false
matches of the annex-word regex itself, not real annexes — "Hilton Italia
SPA" is the company's Italian corporate suffix ("S.p.A.", not a spa
facility), and two Dubai listings match "parking" only because their own
description mentions "Free Parking" as an amenity, not because they *are*
a parking facility. Net: roughly 25-29 of the 33 are real annex-style
sub-venues scored as if they were standalone hotels — a small (33 of
~30,600 included hotels, 0.1%) but real double-counting/noise source,
documented in `entity_qa.py`'s module docstring. Not fixed this round —
distinguishing "the hotel's own combined branding" from "a sub-venue that
shouldn't be its own entity" needs more care than a regex reorder, per the
same caution that shaped the item (a) fixes.
