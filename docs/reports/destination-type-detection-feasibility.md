# "Destination/resort" hotel type — detection feasibility report

- **Date:** 2026-09-XX (owner decision session, post night mission #3)
- **Companion to:** `docs/adr/015-destination-resort-hotel-type-lens.md`
- **Status: report only, per the owner's explicit order — no detection
  code has been written or shipped.** Every finding below comes from live
  Overture queries and the existing ETL output; no data was invented.

## Verdict, up front

The **concept is validated**: the seed case (Hilton Bangkok Suvarnabhumi
Golf Resort & Spa) is correctly caught by the proposed isolation +
amenity-adjacency test at every radius tried, and Overture has real,
substantial data for golf, beach, national park/nature reserve, and theme
park. But the **naive version of this test has a real false-positive
problem** — inspected by hand below, not just counted — and should **not**
be implemented as-is. Section 6 gives specific, targeted fixes; none of
them are exotic, but none are free either. Ski resort has essentially no
usable signal in our current 12 cities (Section 5) — exclude it from a v1
scope, don't fake coverage that isn't there.

## 1. What Overture actually has, per category (verified, not assumed)

Queried live against release `2026-08-19.0`, across all 12 city bboxes.

| Category | `places` (points) | `land_use`/`land` (polygons) |
|---|---|---|
| **Golf** | `golf_course` (654), `driving_range` (379), `golf_club` (57), `miniature_golf_course` (82) | `golf`/`golf_course` (399) + sub-features (bunker, tee, green, fairway, rough, water_hazard — thousands, too granular for adjacency, useful only as confirmation) |
| **Beach** | `beach` (1,698, `geographic_entities/land_feature/beach`) | `land`/`sand`/`beach` (853, already used by `family_convenience`) |
| **National park / reserve** | `national_park` (283), `nature_reserve` (374), `wildlife_sanctuary` (93) | `land_use`/`protected`/* — `nature_reserve` (479), `national_park`, `state_park`, `wilderness_area`, `natural_monument`, `protected_landscape_seascape`, `species_management_area`, `strict_nature_reserve` (smaller counts each, ~40 combined) |
| **Theme park** | `amusement_park` (1,179), `water_park` (164), plus `circus_venue`/`haunted_house`/`carousel` (small) | `land_use`/`entertainment`/`theme_park` (46), `entertainment`/`water_park` (38) |
| **Ski** | *(none — no dedicated ski-area/piste places category exists in Overture at all)* | `land_use`/`winter_sports`/`downhill`+`sled`+`snow_park` — **10 polygons total across all 12 cities** |

Bonus, not requested but relevant: Overture's own lodging taxonomy already
has `resort` (1,126 of our 33,966 hotels), plus `ski_resort` (53) and
`beach_resort` (32) — both **currently excluded** from our hotel dataset
entirely (`taxonomy-mapping.yml`'s `hotel_types.excluded`). See Section 4
for why `taxonomy.primary == 'resort'` alone is NOT a usable proxy.

## 2. Per-city coverage and hotel counts

Hotel isolation baseline: `walkability_density` (already computed, the
"useful destinations within 400m, decay-weighted" dimension,
`docs/scoring.md`) at or below **55** (roughly the global p15) = "isolated"
for this analysis. 4,174 of 33,966 hotels (12.3%) meet that bar.

| City | Hotels | Isolated | Candidates @1km | Bad-location @1km | Candidates @3km | Bad-location @3km |
|---|---:|---:|---:|---:|---:|---:|
| london | 4,397 | 832 | 586 | 246 | 830 | 2 |
| bangkok | 7,546 | 1,189 | 420 | 769 | 1,061 | 128 |
| paris | 3,582 | 201 | 96 | 105 | 194 | 7 |
| rome | 5,040 | 333 | 193 | 140 | 328 | 5 |
| barcelona | 1,720 | 77 | 60 | 17 | 77 | 0 |
| amsterdam | 1,071 | 146 | 117 | 29 | 145 | 1 |
| lisbon | 1,289 | 46 | 40 | 6 | 46 | 0 |
| sydney | 1,078 | 198 | 174 | 24 | 198 | 0 |
| tokyo | 2,745 | 103 | 81 | 22 | 103 | 0 |
| dubai | 2,067 | 508 | 351 | 157 | 503 | 5 |
| new_york | 2,194 | 328 | 186 | 142 | 327 | 1 |
| singapore | 1,237 | 213 | 161 | 52 | 206 | 7 |
| **Total** | **33,966** | **4,174** | **2,465** | **1,709** | **4,018** | **156** |

**The radius matters enormously**: at 3km, 96% of isolated hotels get a
"candidate" flag — a discriminator that flags almost everyone isn't a
discriminator. At 1km, it drops to 59% — more plausible, but still not
validated as accurate (Section 3).

## 3. Symmetric-trap check: does "isolated without amenity" work?

Yes, cleanly. Real examples from the 1,709 hotels correctly landing in
"isolated, no qualifying amenity nearby" (bad location, NOT destination):
**"Rodeway Inn Rahway Hwy 1"**, **"Comfort Suites"**, **"Fairfield"**
(highway-motel-chain pattern, exactly the case the owner warned about),
plus several prominent hotels (Shangri-La Dubai, Ritz-Carlton Singapore)
that are simply in genuinely low-density parts of car-oriented cities with
no anchor amenity nearby — correctly NOT flagged as destination. The
"bad location stays bad location" side of the rule holds up under
inspection.

## 4. False-positive sample — inspected by hand, not just counted

Per-city example candidates were pulled with real hotel names (not just
IDs) and checked. At the 1km radius:

**Looks like a genuine true positive:**
- The seed case itself: `af88de0a…` (Hilton Bangkok Suvarnabhumi Golf
  Resort & Spa), walkability_density **10.8** (extremely isolated),
  **237m** from a `golf_course` polygon boundary-region. Correctly caught
  at every radius tested.
- Two Tokyo lodges (秋保 木の家ロッジ村, 花あさぎ) near golf/national-park-
  reserve features — plausible rural/onsen-area lodging, though their
  presence inside the Tokyo city bbox at all is worth a second look
  (possible geocoding/extraction question, separate from this feature).

**Looks like a real false positive:**
- **"Dusit Thani Dubai"** — a known downtown Sheikh Zayed Road business
  hotel, not beachfront — flagged via "980m to nearest beach". Dubai has
  beach points scattered widely; being within a kilometer of one doesn't
  make a Sheikh Zayed Road hotel a beach resort.
- **"Sunday Sheikh Zayed Road Concord Tower 1 BR by Belvilla"** — an
  apartment rental on the same corridor, same false "beach" trigger.
- Three Singapore hotels (**Cooliv**, **Marina Lodge**, **545
  Residences**) flagged via "beach" at 200–700m — Singapore is small and
  coastal enough that this is weak evidence of resort character, not
  strong evidence.
- **"Bayview Condos"** (New York) flagged via a `national_park_reserve`
  polygon 754m away — very possibly a small urban nature area, not a
  major destination amenity.
- **"บริษัทไฮเทคเอ็มบรอยเดอร์ จำกัด"** ("Hi-Tech Embroidery Co., Ltd") —
  **this is a company name, not a hotel** — an entity-QA miss
  (`docs/STATE.md`'s existing "Entity QA — known limitations" section)
  that this analysis surfaced, not a new problem this feature created.
  Flagged as a destination "candidate" via a nearby beach point, which
  would have been a doubly-wrong result (wrong entity AND wrong type) had
  this shipped as-is.

**Rough read**: of ~18 hand-inspected "candidate" examples across 6
cities, roughly a third look like clear or likely false positives — too
high to ship without the fixes in Section 6. This is exactly the
"sinon dis-le, ne l'invente" standard applied to the detection claim
itself, not just to displayed facts.

## 5. Ski: explicitly out of scope for v1, not because it can't work in principle

10 `winter_sports` polygons total, across ALL 12 city bboxes combined, and
zero dedicated ski-area `places`. None of the 12 launch cities are ski
destinations — this isn't a data gap, it's the wrong data question for
this city roster. If a ski city (Chamonix, Zermatt, Aspen-adjacent, etc.)
is ever added to the launch set, Overture's `winter_sports` land_use
subtype is confirmed to exist and would need its own coverage check
against that city — don't carry a v1 "ski" branch that has nothing to
detect today.

## 6. Why the false positives happen, and what would fix them

1. **`beach` and `national_park_reserve` are too common in coastal/green
   cities to be a "major, defining amenity" signal on their own.**
   `golf` and `theme_park` performed noticeably better in the hand
   inspection — fewer, larger, more distinctive features. Fix: either
   drop `beach`/`national_park_reserve` from v1's category list, or
   require a much tighter radius for them specifically (e.g. 300–400m —
   "the beach IS the front yard" — instead of the same 1km used for golf).
2. **Polygon distance used the bounding-box center, not the true
   boundary.** A large, irregularly-shaped national park's bbox center
   can sit far from the actual nearest edge to a given hotel (both
   over- and under-estimating true proximity depending on shape). A real
   implementation needs `ST_Distance` to the polygon geometry itself
   (DuckDB's `spatial` extension, already loaded in `overture.connect()`),
   not this report's bbox-center shortcut.
3. **No size/area floor on the amenity.** A tiny urban pocket park tagged
   `protected/nature_reserve` counts the same as an actual national park
   in this pass. Fix: an area threshold, the same pattern already proven
   for `family_convenience` (`docs/adr/009`'s `min_area_m2` — precedent
   exists in this codebase for exactly this problem).
4. **Entity-QA noise compounds it.** A non-hotel entity that should never
   have been in the dataset at all (the embroidery company) can still get
   a destination "candidate" flag. Not a reason to block this feature,
   but a reason the existing entity-QA backlog (`docs/STATE.md`) matters
   more once this ships — a wrong entity with a wrong type label is worse
   than a wrong entity alone.
5. **`taxonomy.primary == 'resort'` alone is not usable**, confirmed by
   direct measurement in this pass: the 1,125 hotels already tagged
   `resort` in our dataset have almost the SAME walkability_density
   distribution as everything else (median 82.5 vs. 84.9 overall) — most
   "resort"-branded hotels in our 12 (major, urban-leaning) launch cities
   are not actually isolated. This validates the owner's instinct to
   require measured isolation AND amenity adjacency together, rather than
   trusting Overture's own branding-derived tag.

## 7. Projected count, honestly bounded

- **Upper bound (3km, unrefined): ~4,000 hotels** — not usable, this
  radius flags almost every isolated hotel.
- **Current best estimate (1km, unrefined): ~2,465 hotels** — but
  Section 4's hand-check suggests roughly a third of these are false
  positives, so a **refined methodology (Section 6's fixes applied)
  would likely land meaningfully lower — a rough, unvalidated guess in
  the 1,200–1,800 range**. This is an estimate to set expectations, not a
  number to build a page count around; the real number only comes from
  actually implementing the fixes and re-running this same check.

## 8. Recommendation

Do not implement the 1km or 3km version tested here. Before any detection
code ships (`docs/adr/015`'s Sequencing step 4):
- Apply Section 6 fixes 1–3 (tighter/per-category radius, true polygon
  distance, area floor) and re-run this exact report's methodology.
- Re-inspect a fresh false-positive sample by hand — don't trust the
  aggregate count alone, the way this report didn't.
- Decide separately (not blocking this feature) whether to fix the
  embroidery-company-class entity-QA gap first, since it directly
  degrades this feature's accuracy.
- Ski: leave out of v1 scope; revisit only if the city roster ever
  includes a real ski destination.
