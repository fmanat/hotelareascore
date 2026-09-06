"""Phase 2 export: Phase 1 ETL parquet -> static JSON consumed by the Astro
build (web/). Build-time only — the website has no live backend and makes no
external call on the page-view path (CLAUDE.md §6); this is the bridge
between the ETL world and a static-first product proof, without standing up
Supabase (docs/adr/002 describes Supabase as the eventual serving world for
a live indexed site — Phase 2 is an owner-inspection proof, not a
deployment, so it stays fully static).
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from . import overture
from .config import DIMENSIONS, ETL_DIR, REPO_ROOT, get_city, load_score_weights
from .dedupe import haversine_m
from .reason_codes import compute_reason_codes
from .slug import hotel_slug
from .verdict import build_verdict

WEB_SRC_DATA = REPO_ROOT / "web" / "src" / "data"
WEB_PUBLIC_DATA = REPO_ROOT / "web" / "public" / "data"

N_COMPARABLE = 4

# Entity QA item (c): a hotel this far from the city center gets an honest
# "N km from central <city>" disclosure instead of implying it's simply "in"
# the city (docs/STATE.md — "The Hautboy" is ~30 km from central London but
# Overture's own address_locality already correctly says "Guildford"; the
# bbox-driven city assignment is what was misleading, not the address data).
FAR_FROM_CENTER_KM = 15.0

# docs/STATE.md entity-QA backlog: a hotel can sit under the km threshold
# above and still be in the wrong place -- SpringHill Suites (Carlstadt, NJ)
# is 13.6 km from the New York center point but is a different US state.
# This checks address consistency directly, independent of distance.
def _locality_mismatch(city, address_region: str | None, address_country: str | None) -> str | None:
    if address_country and address_country != city.country:
        return f"Address country ({address_country}) does not match {city.name} ({city.country})"
    if city.expected_region and address_region and address_region != city.expected_region:
        return f"Address region ({address_region}) does not match {city.name} ({city.expected_region})"
    return None


def confidence_label(confidence: float) -> str:
    if confidence >= 80:
        return "High"
    if confidence >= 60:
        return "Medium"
    return "Low"


def _fetch_hotels(con, etl_dir: Path) -> list[dict[str, Any]]:
    q = f"""
        SELECT h.id, h.name, h.lat, h.lon, h.address_locality, h.address_region, h.address_country,
               h.dedupe_confidence,
               s.walkability_density, s.transit_access, s.food_essentials,
               s.quietness_proxy, s.family_convenience, s.nightlife_access,
               s.balanced_score, s.confidence, s.score_version, s.source_release
        FROM read_parquet('{etl_dir / 'hotels.parquet'}') h
        JOIN read_parquet('{etl_dir / 'hotel_scores.parquet'}') s ON s.hotel_id = h.id
    """
    cols = [d[0] for d in con.execute(q).description]
    return [dict(zip(cols, row)) for row in con.execute(q).fetchall()]


def _fetch_nearby_facts(con, etl_dir: Path) -> dict[str, list[dict[str, Any]]]:
    q = f"""
        SELECT hotel_id, rank, category, name, distance_m
        FROM read_parquet('{etl_dir / 'nearby_facts.parquet'}')
        ORDER BY hotel_id, rank
    """
    by_hotel: dict[str, list[dict[str, Any]]] = {}
    for hotel_id, rank, category, name, distance_m in con.execute(q).fetchall():
        by_hotel.setdefault(hotel_id, []).append(
            {"rank": rank, "category": category, "name": name, "distance_m": round(distance_m, 1)}
        )
    return by_hotel


def _attach_comparable_hotels(hotels: list[dict[str, Any]]) -> None:
    """Nearest-scoring peers in the same city (deterministic, real-data-based
    "comparable hotels" per docs/strategy.md §2 — not fabricated, not AI)."""
    ordered = sorted(range(len(hotels)), key=lambda i: hotels[i]["balanced_score"])
    n = len(ordered)
    for pos, idx in enumerate(ordered):
        window = []
        lo, hi = pos - 1, pos + 1
        while len(window) < N_COMPARABLE and (lo >= 0 or hi < n):
            if lo >= 0:
                window.append(ordered[lo])
                lo -= 1
            if len(window) < N_COMPARABLE and hi < n:
                window.append(ordered[hi])
                hi += 1
        hotels[idx]["_comparable_idx"] = window


def export_city(city_id: str, release: overture.Release) -> list[dict[str, Any]]:
    city = get_city(city_id)
    etl_dir = ETL_DIR / release.id / city.id
    con = overture.connect()

    rows = _fetch_hotels(con, etl_dir)
    nearby_by_hotel = _fetch_nearby_facts(con, etl_dir)

    hotels: list[dict[str, Any]] = []
    for r in rows:
        scores = {d: round(r[d], 1) for d in DIMENSIONS}
        nearby = nearby_by_hotel.get(r["id"], [])
        confidence = round(r["confidence"], 1)
        distance_km = round(haversine_m(city.center_lat, city.center_lon, r["lat"], r["lon"]) / 1000, 1)
        locality_mismatch = _locality_mismatch(city, r["address_region"], r["address_country"])
        hotel = {
            "id": r["id"],
            "slug": hotel_slug(r["name"] or "hotel", r["id"]),
            "name": r["name"] or "(unnamed)",
            "city_id": city.id,
            "city_name": city.name,
            "locality": r["address_locality"],
            "region": r["address_region"],
            "country": r["address_country"],
            "lat": round(r["lat"], 6),
            "lon": round(r["lon"], 6),
            "distance_from_center_km": distance_km,
            "far_from_center": distance_km > FAR_FROM_CENTER_KM,
            "locality_mismatch": locality_mismatch is not None,
            "locality_mismatch_detail": locality_mismatch,
            "scores": scores,
            "balanced_score": round(r["balanced_score"], 1),
            "confidence": confidence,
            "confidence_label": confidence_label(confidence),
            "dedupe_confidence": r["dedupe_confidence"],
            "score_version": r["score_version"],
            "source_release": r["source_release"],
            "verdict": build_verdict(scores),
            "reason_codes": compute_reason_codes(scores, confidence, nearby),
            "nearby_facts": nearby,
        }
        hotels.append(hotel)

    _attach_comparable_hotels(hotels)
    for h in hotels:
        h["comparable"] = [
            {"slug": hotels[i]["slug"], "name": hotels[i]["name"], "balanced_score": hotels[i]["balanced_score"]}
            for i in h.pop("_comparable_idx")
        ]

    return hotels


def _city_baseline(city_id: str, release: overture.Release) -> dict[str, Any]:
    etl_dir = ETL_DIR / release.id / city_id
    with open(etl_dir / "city_baseline.json", "r", encoding="utf-8") as f:
        return json.load(f)


def export_web_data(release: overture.Release, city_ids: list[str]) -> None:
    WEB_SRC_DATA.mkdir(parents=True, exist_ok=True)
    WEB_PUBLIC_DATA.mkdir(parents=True, exist_ok=True)

    search_index: list[dict[str, Any]] = []
    baselines: dict[str, Any] = {}

    for city_id in city_ids:
        hotels = export_city(city_id, release)
        with open(WEB_SRC_DATA / f"hotels-{city_id}.json", "w", encoding="utf-8") as f:
            json.dump(hotels, f, ensure_ascii=False)
        search_index.extend(
            {
                "slug": h["slug"],
                "name": h["name"],
                "city": h["city_name"],
                "locality": h["locality"],
                # Compare page (docs/strategy.md §2 journey B) reuses this
                # same index client-side rather than fetching a second file
                # -- these fields were already computed for the hotel page.
                "scores": h["scores"],
                "balanced_score": h["balanced_score"],
                "confidence": h["confidence"],
                "confidence_label": h["confidence_label"],
                "verdict": h["verdict"],
            }
            for h in hotels
        )
        baselines[city_id] = _city_baseline(city_id, release)

    with open(WEB_PUBLIC_DATA / "search-index.json", "w", encoding="utf-8") as f:
        json.dump(search_index, f, ensure_ascii=False)
    with open(WEB_SRC_DATA / "city-baselines.json", "w", encoding="utf-8") as f:
        json.dump(baselines, f, ensure_ascii=False)
    with open(WEB_SRC_DATA / "meta.json", "w", encoding="utf-8") as f:
        json.dump({"release": release.id, "cities": city_ids}, f)

    weights = load_score_weights()
    with open(WEB_SRC_DATA / "personas.json", "w", encoding="utf-8") as f:
        json.dump(weights["personas"], f)
