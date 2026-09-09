"""Canonical hotel slugs — one hotel identity -> one canonical URL
(docs/seo-policy.md §6). Deterministic from name + a short id suffix (never
just the name: many hotels share a brand name, e.g. multiple "Premier Inn"
per city) so a slug never collides and never changes as long as the
hotel's `id` (Overture GERS id) is stable.
"""
from __future__ import annotations

import re
import unicodedata

_NON_ALNUM = re.compile(r"[^a-z0-9]+")
_PURELY_NUMERIC = re.compile(r"^[0-9]+$")
# Same shape as _PURELY_NUMERIC but applied to the RAW name (trimmed, not
# slugified) -- this is validate.py's n_numeric_name definition exactly
# (its DuckDB query: regexp_matches(trim(name), '^[0-9]+$')). Kept as its
# own compiled pattern rather than reusing _PURELY_NUMERIC on a pre-slugified
# string: slugify() strips punctuation before checking, so "Hotel #86"
# would slugify to "hotel-86" (not purely numeric) but a name that's
# JUST "86" either way still needs the same raw-name check both places.
_RAW_NUMERIC_NAME = re.compile(r"^[0-9]+$")


def is_numeric_name(name: str | None) -> bool:
    """docs/reports/nyc-bbox-options.md "Numeric-name hotel slugs": a hotel
    whose `name` is entirely digits is almost certainly an unresolved
    Overture source reference, not a real hotel name. Single source of
    truth for this check -- validate.py's QA count, compute_publication.py's
    seeding, and publication.py's hard indexability gate (docs/adr/014) all
    call this instead of each re-deriving the same regex."""
    return bool(_RAW_NUMERIC_NAME.match((name or "").strip()))


def slugify(name: str) -> str:
    s = unicodedata.normalize("NFKD", name or "").encode("ascii", "ignore").decode("ascii")
    s = s.lower()
    s = _NON_ALNUM.sub("-", s).strip("-")
    if not s:
        return "hotel"
    if _PURELY_NUMERIC.match(s):
        # docs/reports/nyc-bbox-options.md (overnight backlog): a handful of
        # Overture records carry a bare numeric string as `name` (an
        # unresolved source reference, not a real hotel name -- validate.py
        # already flags these separately as n_numeric_name). Left as-is, the
        # slug would be indistinguishable from an arbitrary reference number
        # ("/hotel/8468671-f152bc7b"); prefixing makes the URL legible as
        # "we don't have a real name for this one" instead of looking like a
        # broken or spam link. Only affects names that are ENTIRELY digits --
        # a real name that happens to contain a number ("21 Club") is
        # untouched.
        return f"hotel-{s}"
    return s


def hotel_slug(name: str, hotel_id: str) -> str:
    suffix = hotel_id[-8:] if hotel_id else "unknown"
    return f"{slugify(name)}-{suffix}"
