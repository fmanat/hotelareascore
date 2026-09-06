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


def slugify(name: str) -> str:
    s = unicodedata.normalize("NFKD", name or "").encode("ascii", "ignore").decode("ascii")
    s = s.lower()
    s = _NON_ALNUM.sub("-", s).strip("-")
    return s or "hotel"


def hotel_slug(name: str, hotel_id: str) -> str:
    suffix = hotel_id[-8:] if hotel_id else "unknown"
    return f"{slugify(name)}-{suffix}"
