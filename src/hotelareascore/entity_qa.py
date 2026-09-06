"""Entity QA (docs/STATE.md "Bounded pre-Phase-3 task: entity QA", item a):
Overture's `hotel`-family taxonomy leaves catch some places that plainly
aren't hotels — a consultancy ("RevenuebyDesign"), an office tower
("อาคารใยแก้ว True Tower"). Overture's own fields (`basic_category`,
`categories.primary`) mirror `taxonomy.primary` for these; there is no
cheap structured signal from the source data itself to catch them.

This is therefore a **name-pattern heuristic, not a validated classifier**,
and it took four iterations against real Batch 1/2 data (Paris, Rome,
Barcelona, Amsterdam, Lisbon, Sydney, Tokyo, Dubai, New York, Singapore) to
get to something worth shipping — each caught a distinct, real bug class:

1. "tower"/"design" as markers excluded real hotels: "Design Hotel" and
   "Design Apartments" are a legitimate boutique-accommodation style, and a
   huge share of Dubai's short-term-rental supply is an OYO-branded unit
   named after the residential tower it's in (e.g. "OYO 985 Home 1BR Lake
   City Tower"). Both markers were removed; OYO/Belvilla/Occidental joined
   the brand allowlist.
2. Accented spellings of "hotel" itself weren't recognized ("Hôtel Design
   Sorbonne" has no ASCII "hotel" substring) — names are now accent-folded
   before matching.
3. Markers without their OWN word boundaries matched inside unrelated words:
   "temple" matched inside "Templeton" (a real hotel name), "church" matched
   inside "Hornchurch" (a London place name). Every marker below is
   individually `\\b`-wrapped now — the earlier version wrapped the whole
   alternation once, which does not stop an inner alternative from starting
   or ending mid-word when a neighboring alternative's boundary happens to
   line up. Only the deliberately unbounded "by ?design" pattern (for
   camelCase names like "RevenuebyDesign") skips this, on purpose.
4. Bug #3's fix (word boundaries) doesn't help when a marker word IS a real
   whole word that also names a street: "union" matched "W New York –
   Union Square" (a real W Hotels property) and "mosque" matched "Wink @
   Mosque Street" (a real Singapore hostel address) — both are Batch 2
   finds (`docs/reports/phase-3-batch-2-ingestion-report.md`). "bank",
   "church" and "temple" carry the same risk (Bank St, Church St, Temple Pl
   all exist). Fixed differently from bugs #1-3: these four now require a
   negative lookahead (`RISKY_MARKERS`) — not flagged when immediately
   followed by a street-type word — instead of being removed outright,
   since (unlike tower/design/building/office/factory) they still have
   genuine hits worth keeping ("First National Bank", "St Mary's Church").
   "union" alone was dropped entirely: no genuine hit for it has turned up
   yet, only collisions. Known residual staleness: this fix would also
   rescue 2 already-ingested Dubai records ("...union metro dubai" — a
   metro-station name, not re-ingested for this alone).

Expect this list to keep needing iteration — every exclusion is logged
(`manifest.json` `entity_qa_excluded_names`, the full per-city list, not
just a sample) specifically so a wrongly excluded hotel can be found and
reverted; nothing here is silent.

**Known limitation, logged not fixed (owner audit, 2026-09-06):** the brand
allowlist is checked FIRST and short-circuits everything else, including
cases where it shouldn't. A hotel's own sub-venue — a restaurant, spa, bar,
parking garage, or ballroom that Overture gave its own place record under a
lodging-family taxonomy leaf — still slips through as long as its name
contains a recognized brand token, e.g. "Royal Princess Dusit Restaurant"
(the "Dusit" brand hit fires before any annex word could matter) or "Grand
Ballroom, Shangri-La Hotel, Bangkok". Across the 10 Batch 1 + Phase 1
cities, 33 included hotel records combine a brand token with an annex word
(restaurant|spa|bar|cafe|parking|ballroom) — see
`docs/reports/phase-3-coverage-bangkok-nyc.md` for the count per city and
examples. Not fixed here: distinguishing "the hotel's own combined Hotel &
Spa branding" (a single legitimate property) from "a sub-venue that should
not be its own entity" needs more than a regex order fix and risks a new
false-exclusion class if done carelessly — same caution as the marker
changes above.
"""
from __future__ import annotations

import re
import unicodedata

LODGING_KEYWORDS = re.compile(
    r"\b(hotel|hotels|inn|suite|suites|resort|resorts|hostel|hostels|lodge|lodges|guest ?house|"
    r"guesthouse|b\s*&\s*b|bed and breakfast|motel|villa|aparthotel|apart-hotel|"
    r"serviced apartments?|residences?|accommodation|"
    r"chateau|ryokan|homestay|home stay|pension|auberge|casa rural)\b",
    re.IGNORECASE,
)

# Major global/regional hospitality AND short-term-rental brands (presence
# overrides NON_HOTEL_MARKERS below). Not exhaustive: extend as spot-checks
# find more false positives (see module docstring). Names are matched after
# accent-folding, so plain-ASCII entries here also catch accented variants.
HOSPITALITY_BRANDS = re.compile(
    r"\b(marriott|hilton|hyatt|sheraton|westin|ascott|lebua|ritz-?carlton|four seasons|"
    r"mandarin oriental|peninsula|shangri-?la|intercontinental|kempinski|raffles|aman(?!\w)|"
    r"baiyoke|conrad|st\.? ?regis|waldorf astoria|fairmont|sofitel|novotel|mercure|ibis|accor|"
    r"centara|dusit|anantara|banyan tree|amari|avani|oberoi|taj\b|leela|rosewood|edition|"
    r"bulgari|six senses|como\b|nobu|citizenm|yotel|premier inn|travelodge|holiday inn|"
    r"crowne plaza|doubletree|best western|radisson|wyndham|meli[a]|nh hotels|barcel[o]|"
    r"riu\b|iberostar|jumeirah|w hotels?\b|pullman|swissotel|park hyatt|grand hyatt|"
    r"okura|nikko|prince (park|sakura|hotel)|ana intercontinental|cheval\b|bob w\b|blue orchid|"
    r"native\b|urbanest|oakwood|frasers hospitality|shama\b|somerset\b|citadines|staybridge|"
    r"residence inn|homewood suites|extended stay|oyo\b|belvilla|occidental|atlantis the palm|"
    r"autograph collection|airbnb|vrbo|booking\.com|park plaza)\b",
    re.IGNORECASE,
)

# Each entry is individually word-bounded when compiled (see module
# docstring, bug #3) -- do not hand-craft one shared \b(...)\b string here,
# it does not guarantee every alternative is bounded on both sides.
# Deliberately excludes "tower"/"building"/"office"/"design"/"factory" (bug
# #1): each is a common, legitimate hospitality-naming convention somewhere
# in the world. Also excludes "union" (bug #4 below moved it to the guarded
# list, then it was dropped entirely -- see RISKY_MARKER_TERMS).
_NON_HOTEL_MARKER_TERMS = [
    "consulting", "consultant", "consultants", "solutions", "solution", "trading", "chartered", "law",
    "llp", "plc", "ltd", "limited", "insurance", "embassy", "consulate", "chamber of commerce",
    "regional office", "head office", "corporation", "corp", "foundation",
    "school", "academy", "university", "hospital", "clinic", "dental", "government",
    "ministry", "council", "municipal", "logistics", "shipping", "freight", "import", "export",
    "accountant", "accountants", "accounting", "architect", "architects", "estate agents",
    "real estate agency", "surveyor", "surveyors", "recruitment", "staffing", "marketing agency",
    "advertising agency", "construction co", "construction company", "engineering co",
    "engineering company", "engineering services", "it services", "software", "warehouse", "depot",
    "centre for", "center for", "society", "association",
]
NON_HOTEL_MARKERS = re.compile(
    r"\b(" + "|".join(re.escape(t) for t in _NON_HOTEL_MARKER_TERMS) + r")\b",
    re.IGNORECASE,
)

# Bug #4 (owner-audited, Batch 2 New York/Singapore): "union" matched inside
# "W New York - Union Square" (a real W Hotels property) and "mosque"
# matched inside "Wink @ Mosque Street" (a real Singapore hostel address) --
# both are streets/squares named after the same concept the marker means to
# catch (a labor union, a mosque), not an instance of it. "bank"/"church"/
# "temple" carry the identical risk (Bank St, Church St, Temple Pl all
# exist). These four are checked separately with a guard: not flagged when
# immediately followed by a street-type word. "union" itself is dropped
# outright -- no genuine hit for it has turned up yet, only this collision.
_STREET_TYPE_WORD = (
    r"(?:street|st|road|rd|square|sq|avenue|ave|lane|ln|way|drive|dr|"
    r"boulevard|blvd|place|pl|court|ct|close|row|walk|circle|crescent|terrace)"
)
_RISKY_MARKER_TERMS = ["bank", "church", "mosque", "temple"]
RISKY_MARKERS = re.compile(
    r"\b(?:" + "|".join(re.escape(t) for t in _RISKY_MARKER_TERMS) + r")\b"
    r"(?!\.?\s*" + _STREET_TYPE_WORD + r"\b)",
    re.IGNORECASE,
)

# Deliberately NOT \b-bounded on the left: catches camelCase/no-space
# business names like "RevenuebyDesign" that a strict boundary would miss.
# Narrow on purpose -- bare "design" was bug #1.
COMPOUND_NAME_MARKERS = re.compile(r"by ?design\b", re.IGNORECASE)


def _fold(name: str) -> str:
    """ASCII-fold accents so "Hôtel"/"Château" match the same as
    "Hotel"/"Chateau" (bug #2 above)."""
    return unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode("ascii")


def is_likely_non_hotel(name: str | None) -> bool:
    """True if `name` looks like a business/institution swept up by a
    hotel-family taxonomy leaf rather than an actual lodging business.
    Conservative by design (brand allowlist checked first, and markers with
    a demonstrated false-positive history removed — see module docstring):
    false negatives (missed non-hotels) are the intended failure mode, not
    false exclusions of real hotels. Some still slip through either way.
    """
    if not name:
        return False
    folded = _fold(name)
    if HOSPITALITY_BRANDS.search(folded):
        return False
    if LODGING_KEYWORDS.search(folded):
        return False
    return bool(
        NON_HOTEL_MARKERS.search(folded)
        or RISKY_MARKERS.search(folded)
        or COMPOUND_NAME_MARKERS.search(folded)
    )
