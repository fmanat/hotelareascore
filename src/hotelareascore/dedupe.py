"""Hotel dedupe: normalized name + proximity <= 25m + same category family.

docs/data-and-costs.md §4: "dedupe (GERS/source ids -> normalized name ->
category family -> proximity <= 25 m -> address; never merge distinct
branches of a chain; store canonical id + method + confidence)".

Overture's own place theme already conflates most duplicate source records
under one GERS id, so this pass mainly catches near-duplicates that survive
Overture's own conflation. Normalization is deliberately conservative
(no stopword stripping) because under-merging is the safe failure mode here —
merging two different branches of the same chain would corrupt both records'
identity, which the ADR explicitly forbids. When still ambiguous we keep
both records rather than guess.
"""
from __future__ import annotations

import math
import re
import unicodedata
from dataclasses import dataclass, field

_NON_ALNUM = re.compile(r"[^a-z0-9]+")


def normalize_name(name: str) -> str:
    s = unicodedata.normalize("NFKD", name or "").encode("ascii", "ignore").decode("ascii")
    s = s.lower()
    s = _NON_ALNUM.sub(" ", s)
    return re.sub(r"\s+", " ", s).strip()


def haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6_371_000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlambda / 2) ** 2
    return 2 * r * math.asin(min(1.0, math.sqrt(a)))


@dataclass
class HotelRecord:
    id: str
    name: str
    lat: float
    lon: float
    confidence: float | None
    n_sources: int
    taxonomy_primary: str


@dataclass
class DedupeResult:
    canonical_id: str
    member_ids: list[str] = field(default_factory=list)
    method: str = "none"  # "none" | "normalized_name+proximity"
    dedupe_confidence: float = 100.0  # 100 = single source, no merge needed


def _grid_key(lat: float, lon: float, cell_deg: float = 0.0003) -> tuple[int, int]:
    return (math.floor(lat / cell_deg), math.floor(lon / cell_deg))


def _neighbor_keys(key: tuple[int, int]) -> list[tuple[int, int]]:
    gx, gy = key
    return [(gx + dx, gy + dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1)]


def dedupe_hotels(records: list[HotelRecord], proximity_m: float = 25.0) -> list[DedupeResult]:
    """Union-find over candidate pairs sharing a normalized name, the same
    taxonomy leaf, and within `proximity_m` meters of each other."""
    n = len(records)
    parent = list(range(n))

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a: int, b: int) -> None:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra

    buckets: dict[tuple[int, int], list[int]] = {}
    norm_names = [normalize_name(r.name) for r in records]
    for i, r in enumerate(records):
        buckets.setdefault(_grid_key(r.lat, r.lon), []).append(i)

    for i, r in enumerate(records):
        if not norm_names[i]:
            continue
        candidates: set[int] = set()
        for nk in _neighbor_keys(_grid_key(r.lat, r.lon)):
            candidates.update(buckets.get(nk, []))
        for j in candidates:
            if j <= i:
                continue
            if norm_names[j] != norm_names[i]:
                continue
            if records[j].taxonomy_primary != r.taxonomy_primary:
                continue
            if haversine_m(r.lat, r.lon, records[j].lat, records[j].lon) <= proximity_m:
                union(i, j)

    groups: dict[int, list[int]] = {}
    for i in range(n):
        groups.setdefault(find(i), []).append(i)

    results: list[DedupeResult] = []
    for members in groups.values():
        member_records = [records[i] for i in members]

        def sort_key(rec: HotelRecord) -> tuple[float, int, str]:
            return (-(rec.confidence or 0.0), -rec.n_sources, rec.id)

        canonical = sorted(member_records, key=sort_key)[0]
        if len(member_records) == 1:
            results.append(DedupeResult(canonical_id=canonical.id, member_ids=[canonical.id]))
        else:
            results.append(
                DedupeResult(
                    canonical_id=canonical.id,
                    member_ids=[r.id for r in member_records],
                    method="normalized_name+proximity",
                    # merged records are inherently less certain than a single
                    # clean source — a documented v1 prior, see confidence
                    # weights in score-weights.yml.
                    dedupe_confidence=70.0,
                )
            )
    return results
