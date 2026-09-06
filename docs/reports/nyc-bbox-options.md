# New York bbox / New Jersey contamination — options report

> Bloc E, overnight mission. Report only — **no action taken**, no bbox or
> taxonomy change made. Numeric-name slug fix (item 4) is a separate, safe,
> already-applied change — see that section.

## The problem, with numbers

`docs/reports/phase-3-calibration-sensitivity-report.md` flagged one
concrete case (SpringHill Suites, Carlstadt NJ). The real scale is larger:
**351 of New York's 2,194 hotels (16%) carry a New Jersey address region**,
confirmed via Overture's own `addresses[].region` field, not a heuristic.
188 of those 351 are within the existing 15km `far_from_center` threshold
— i.e. previously undisclosed by any signal at all until the locality-
consistency check shipped this session (`docs/STATE.md`, `webdata.py`
`_locality_mismatch`). Top NJ localities by count:

| Locality | Hotels |
|---|---:|
| Jersey City | 59 |
| Newark | 45 |
| Secaucus | 22 |
| Elizabeth | 19 |
| North Bergen | 16 |
| Hoboken | 10 |
| Clifton | 10 |
| West Orange | 9 |
| Fort Lee | 8 |
| Union City | 7 |

## Why a bbox can't cleanly fix this (checked, not assumed)

The instinctive fix — shrink the bbox to exclude New Jersey — does not
work, because Staten Island (one of the 5 boroughs, unambiguously "New
York") and the New Jersey cities above **occupy the same longitude band**:

- Staten Island hotels: longitude **-74.248 to -74.062**
- New Jersey hotels (in this dataset): longitude **-74.280 to -73.973**

These ranges overlap almost entirely. A bounding *rectangle* cannot
separate "west-facing New York" from "New Jersey across the water" — any
box wide enough to keep Staten Island in is wide enough to let Jersey City
and Hoboken in too, and any box tight enough to exclude New Jersey cuts
into Staten Island. The real New York/New Jersey line is the Hudson
River/state boundary, an irregular polygon, not a rectangle. This isn't a
tuning problem the current bbox approach can solve; it's a structural
limit of bbox-based extraction for a city shape like New York's.

## Option (a): status quo + current disclosure

Keep the bbox as-is; rely on the locality-consistency check shipped this
session (`locality_mismatch` on the hotel page, `n_locality_mismatch` in
`validate.py`'s per-city QA report).

- **Cost:** €0, already shipped.
- **Effect:** every NJ hotel is now labeled honestly on its own page
  ("Address region (NJ) does not match New York (NY)"), independent of
  distance. Nothing is hidden; nothing silently claims to be Manhattan.
- **Risk:** 351 hotels (16% of the "New York" dataset) sit in a city
  labeled "New York" at all, even if individually disclosed. A user
  scanning city-level aggregates (city page averages, "hotels in New
  York" search scope) still sees Jersey City and Newark folded into "New
  York" numbers.

## Option (b): tighten the bbox

Given the geometry above, this cannot be done with a rectangle alone
without cutting real Staten Island hotels. A geometrically correct version
would need **polygon-based extraction** — filter hotels by point-in-polygon
against Overture's own administrative boundary for New York City (or the 5
counties/boroughs), not a bbox — a real ETL change (new theme:
`divisions`/`division_area`, a spatial join instead of a `BETWEEN` filter),
not a config edit. Scoped rough effort: comparable to the `base/land_use` +
`base/land` ingestion already built tonight (new theme, new schema check,
new join), applied to `hotels_raw` extraction instead of `green_spaces`.

- **Cost:** a real (if bounded) engineering task, not tonight's scope.
- **Effect:** would cleanly remove the New Jersey contamination while
  keeping every legitimate borough hotel, including Staten Island.
- **Risk:** none obvious to the data model; the main cost is engineering
  time. Worth scheduling if "New York" as a labeled dataset needs to be
  geometrically honest before Phase 4 indexing decisions, rather than
  disclosure-patched.

## Option (c): a "NYC metro" market label

Reframe rather than filter: keep the current bbox (or even keep it as-is
deliberately), but stop calling the whole thing "New York" — introduce a
"New York City metro" or similar market label that HONESTLY includes
well-connected satellite cities (Jersey City, Hoboken, Newark — all a
short PATH-train ride from Manhattan, genuinely part of how frequent
travelers think about "the New York area") while making clear it is not
literally the city.

- **Cost:** a naming/copy decision plus wherever "New York" is used as a
  literal city label in the product (hero copy, page titles, breadcrumbs).
  Not a data change.
- **Effect:** turns a data-quality-looking problem into an honest,
  deliberate product decision. Plausibly the best user-facing framing for
  the ~30 hotels in genuinely walkable/transit-linked NJ cities (Jersey
  City, Hoboken); less honest for the ~190 hotels in Newark, Elizabeth,
  Secaucus, Clifton, etc., which are not "the New York experience" by any
  reasonable traveler's expectation even if administratively close.
- **Risk:** this is a **positioning decision** (CLAUDE.md §4: "major
  positioning" is an owner decision boundary item), not an engineering
  one — flagged, not decided, here.

## Recommendation

Option (a) is already shipped and costs nothing further tonight. If the
owner wants a cleaner dataset before Phase 4 indexing decisions, **(b) is
the geometrically correct fix** and worth scheduling as its own scoped
piece of work (polygon-based extraction, likely useful for other cities
with irregular shapes too, not just New York). **(c) is a possible
parallel/alternative framing**, but it changes what "New York" means as a
product claim and should be an explicit owner call, not inferred from this
report. No preference is recorded between (b) and (c) — they answer
different questions (data correctness vs. product positioning) and are not
mutually exclusive.

---

## Numeric-name hotel slugs (Bloc E item 4)

9 hotels across 3 cities (not 12) have a purely numeric `name` — almost
certainly an unresolved source reference Overture never matched to a real
name, not an actual hotel called "86" or "8468671":

| City | hotel_id (truncated) | name |
|---|---|---|
| London | `3f627a29…` | 8468671 |
| London | `1871f6b8…` | 6805306 |
| London | `a4fdc914…` | 6805337 |
| London | `7828c4f6…` | 6805311 |
| London | `2f66ec0f…` | 7646530 |
| London | `92b19700…` | 7545060 |
| London | `1f0f8644…` | 3617683 |
| Tokyo | `2cb27a86…` | 86 |
| Bangkok | `71160e6c…` | 258 |

**Finding that changes the recommendation: `confidence` does not catch
these.** Checked directly — several score 70s-90s confidence (one at
95.5), because `confidence` measures geolocation/POI-coverage/dedupe
quality (`docs/scoring.md §3`), not name sanity. A record with a broken
name can still look fully trustworthy on every other signal, so "low
confidence stays non-indexable" (the existing rule) does **not**
structurally protect against a numeric-name page ever becoming indexable.

**Applied tonight (safe, additive, already merged):** `slug.py`'s
`slugify()` now prefixes a purely-numeric name with `hotel-`
(`"8468671"` → `"hotel-8468671"`) instead of leaving the bare number as the
entire URL segment (`/hotel/8468671-f152bc7b` read like an arbitrary
reference number or a broken/spam link; `/hotel/hotel-8468671-f152bc7b` at
least reads as "we don't have a real name for this one"). Only names that
are **entirely digits** are affected — "21 Club" and "Hotel 1898" are
untouched. Tested (`tests/test_slug.py`), zero effect on any other hotel's
slug or URL stability.

**Not applied, proposed for owner decision:** whether a numeric-name
record should be **structurally barred from ever being marked indexable**
in `page_publication` (Bloc C), independent of its confidence score — i.e.
treat "no real name" as its own hard gate alongside "low confidence",
since tonight's finding shows confidence alone doesn't catch it. This is a
one-line addition to whatever selection/publication logic Bloc C's
`page_publication` table ends up enforcing (`n_numeric_name` is already
computed by `validate.py`per hotel) — flagged here rather than decided,
since it's a publication-policy call.
