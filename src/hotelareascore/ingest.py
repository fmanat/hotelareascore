"""Phase 1 ingest: Overture release -> per-city ETL parquet (hotels, pois,
segments) + a source_runs manifest.

Pipeline order matches docs/data-and-costs.md §4: discover release -> schema
check (fail closed) -> per-city bbox extract -> normalize -> dedupe -> QA
happens later in validate.py; this module only extracts + dedupes + persists
to the ETL world (never touches Supabase — docs/adr/002).

Everything stays inside DuckDB (extraction -> parquet) except the dedupe
pass, which needs the small per-city hotel set in Python for the union-find
clustering in dedupe.py; the result is fed back in via a bound INSERT
(no pandas/pyarrow dependency).
"""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from . import overture, taxonomy
from .config import City, ETL_DIR, get_city
from .dedupe import HotelRecord, dedupe_hotels
from .entity_qa import is_likely_non_hotel


def city_dir(release: overture.Release, city: City) -> Path:
    d = ETL_DIR / release.id / city.id
    d.mkdir(parents=True, exist_ok=True)
    return d


def _hotels_raw_sql(places_path: str, city: City) -> str:
    minx, miny, maxx, maxy = city.bbox
    predicate = taxonomy.hotel_sql_predicate()
    return f"""
        SELECT
            id,
            names.primary AS name,
            bbox.xmin AS lon,
            bbox.ymin AS lat,
            confidence,
            taxonomy.primary AS taxonomy_primary,
            taxonomy.hierarchy AS taxonomy_hierarchy,
            basic_category,
            len(sources) AS n_sources,
            addresses[1].freeform AS address_freeform,
            addresses[1].locality AS address_locality,
            addresses[1].postcode AS address_postcode,
            addresses[1].region AS address_region,
            addresses[1].country AS address_country
        FROM read_parquet('{places_path}')
        WHERE bbox.xmin BETWEEN {minx} AND {maxx}
          AND bbox.ymin BETWEEN {miny} AND {maxy}
          AND {predicate}
    """


def _poi_sql(places_path: str, city: City) -> str:
    minx, miny, maxx, maxy = city.bbox
    point_dims = ["food_essentials", "transit_access", "nightlife_access", "family_convenience", "walkability_density"]
    preds = [taxonomy.poi_sql_predicate(d) for d in point_dims]
    quiet_cfg = taxonomy.quietness_config()
    airport_cats = ", ".join(f"'{c}'" for c in quiet_cfg["airport_categories"])
    preds.append(f"taxonomy.primary IN ({airport_cats})")
    # family_convenience v2 (docs/adr/006): park/playground no longer score
    # from these points (see green-space polygon extraction below), but they
    # stay in the flat extract so the "Why?" section can still show a nearby
    # named park -- display only, never scoring input.
    display_only = taxonomy.family_convenience_display_only_categories()
    if display_only:
        cats = ", ".join(f"'{c}'" for c in display_only)
        preds.append(f"taxonomy.primary IN ({cats})")
    predicate = "(" + " OR ".join(preds) + ")"
    return f"""
        SELECT
            id,
            names.primary AS name,
            bbox.xmin AS lon,
            bbox.ymin AS lat,
            confidence,
            taxonomy.primary AS taxonomy_primary,
            taxonomy.hierarchy AS taxonomy_hierarchy,
            '{city.id}' AS city_id
        FROM read_parquet('{places_path}')
        WHERE bbox.xmin BETWEEN {minx} AND {maxx}
          AND bbox.ymin BETWEEN {miny} AND {maxy}
          AND NOT list_contains(taxonomy.hierarchy, 'lodging')
          AND {predicate}
    """


def _green_spaces_sql(land_use_path: str, city: City) -> str:
    """Polygon footprints for family_convenience v2 (docs/adr/006):
    Overture's base/land_use theme, filtered to park/playground -- the same
    real-world features `places` represents as points, here as their actual
    area geometry. bbox.* columns are extracted directly (Overture already
    computes them) rather than derived from geometry at score time, so
    scoring's bbox prefilter is a plain column comparison."""
    minx, miny, maxx, maxy = city.bbox
    cfg = taxonomy.family_convenience_land_use_config()
    subtypes = ", ".join(f"'{s}'" for s in cfg["subtypes"])
    rec_classes = cfg.get("recreation_classes", [])
    predicate = f"(subtype IN ({subtypes}))"
    if rec_classes:
        classes = ", ".join(f"'{c}'" for c in rec_classes)
        predicate += f" OR (subtype = 'recreation' AND class IN ({classes}))"
    return f"""
        SELECT
            id,
            names.primary AS name,
            subtype,
            class,
            ST_AsText(geometry) AS geometry_wkt,
            bbox.xmin AS bbox_xmin,
            bbox.ymin AS bbox_ymin,
            bbox.xmax AS bbox_xmax,
            bbox.ymax AS bbox_ymax,
            '{city.id}' AS city_id
        FROM read_parquet('{land_use_path}')
        WHERE bbox.xmin BETWEEN {minx} AND {maxx}
          AND bbox.ymin BETWEEN {miny} AND {maxy}
          AND ({predicate})
    """


def _segment_sql(segments_path: str, city: City) -> str:
    minx, miny, maxx, maxy = city.bbox
    quiet_cfg = taxonomy.quietness_config()
    road_classes = ", ".join(f"'{c}'" for c in quiet_cfg["road_classes"])
    return f"""
        SELECT
            id,
            subtype,
            class,
            ST_AsText(geometry) AS geometry_wkt,
            '{city.id}' AS city_id
        FROM read_parquet('{segments_path}')
        WHERE bbox.xmin BETWEEN {minx} AND {maxx}
          AND bbox.ymin BETWEEN {miny} AND {maxy}
          AND ((subtype = 'road' AND class IN ({road_classes})) OR subtype = 'rail')
    """


def ingest_city(city_id: str, release: overture.Release | None = None) -> dict[str, Any]:
    city = get_city(city_id)
    con = overture.connect()

    if release is None:
        release = overture.discover_latest_release(con)

    places_path = overture.places_path(release)
    segments_path = overture.segments_path(release)
    land_use_path = overture.land_use_path(release)
    overture.check_schema(con, places_path, overture.REQUIRED_PLACE_COLUMNS, "places theme")
    overture.check_schema(con, segments_path, overture.REQUIRED_SEGMENT_COLUMNS, "transportation theme")
    overture.check_schema(con, land_use_path, overture.REQUIRED_LAND_USE_COLUMNS, "base/land_use theme")

    t0 = time.time()
    con.execute(f"CREATE OR REPLACE TEMP TABLE hotels_raw AS {_hotels_raw_sql(places_path, city)}")
    con.execute(f"CREATE OR REPLACE TEMP TABLE pois AS {_poi_sql(places_path, city)}")
    con.execute(f"CREATE OR REPLACE TEMP TABLE segments AS {_segment_sql(segments_path, city)}")
    con.execute(f"CREATE OR REPLACE TEMP TABLE green_spaces AS {_green_spaces_sql(land_use_path, city)}")
    extract_seconds = time.time() - t0

    hotels_raw_rows = con.execute(
        "SELECT id, name, lat, lon, confidence, n_sources, taxonomy_primary FROM hotels_raw"
    ).fetchall()
    n_hotels_raw = len(hotels_raw_rows)

    # Entity QA (docs/STATE.md, item a): a name-pattern heuristic, not a
    # validated classifier -- see entity_qa.py docstring for known
    # limitations. Every exclusion is logged so it can be found and
    # reverted if it turns out to be a real hotel.
    entity_qa_excluded = [(r[0], r[1]) for r in hotels_raw_rows if is_likely_non_hotel(r[1])]
    excluded_ids = {eid for eid, _ in entity_qa_excluded}
    if excluded_ids:
        hotels_raw_rows = [r for r in hotels_raw_rows if r[0] not in excluded_ids]
        con.execute("CREATE OR REPLACE TEMP TABLE _entity_qa_excluded (id VARCHAR)")
        con.executemany("INSERT INTO _entity_qa_excluded VALUES (?)", [(i,) for i in excluded_ids])
        con.execute(
            "CREATE OR REPLACE TEMP TABLE hotels_raw_qa AS "
            "SELECT h.* FROM hotels_raw h LEFT JOIN _entity_qa_excluded e ON e.id = h.id WHERE e.id IS NULL"
        )
        con.execute("DROP TABLE hotels_raw")
        con.execute("ALTER TABLE hotels_raw_qa RENAME TO hotels_raw")

    records = [
        HotelRecord(
            id=r[0], name=r[1] or "", lat=r[2], lon=r[3],
            confidence=r[4], n_sources=r[5] or 0, taxonomy_primary=r[6] or "",
        )
        for r in hotels_raw_rows
    ]
    dedupe_results = dedupe_hotels(records)
    merged_groups = [d for d in dedupe_results if d.method != "none"]

    con.execute(
        "CREATE OR REPLACE TEMP TABLE dedupe_groups "
        "(canonical_id VARCHAR, dedupe_method VARCHAR, dedupe_confidence DOUBLE, merged_from VARCHAR[])"
    )
    con.executemany(
        "INSERT INTO dedupe_groups VALUES (?, ?, ?, ?)",
        [(d.canonical_id, d.method, d.dedupe_confidence, d.member_ids) for d in dedupe_results],
    )

    con.execute(
        "CREATE OR REPLACE TEMP TABLE hotels_final AS "
        "SELECT h.*, d.dedupe_method, d.dedupe_confidence, d.merged_from, '"
        + city.id
        + "' AS city_id "
        "FROM hotels_raw h JOIN dedupe_groups d ON d.canonical_id = h.id"
    )

    out_dir = city_dir(release, city)
    con.execute(f"COPY hotels_final TO '{out_dir / 'hotels.parquet'}' (FORMAT PARQUET)")
    con.execute(f"COPY pois TO '{out_dir / 'pois.parquet'}' (FORMAT PARQUET)")
    con.execute(f"COPY segments TO '{out_dir / 'segments.parquet'}' (FORMAT PARQUET)")
    con.execute(f"COPY green_spaces TO '{out_dir / 'green_spaces.parquet'}' (FORMAT PARQUET)")

    n_hotels_final = con.execute("SELECT count(*) FROM hotels_final").fetchone()[0]
    n_pois = con.execute("SELECT count(*) FROM pois").fetchone()[0]
    n_segments = con.execute("SELECT count(*) FROM segments").fetchone()[0]
    n_green_spaces = con.execute("SELECT count(*) FROM green_spaces").fetchone()[0]

    manifest = {
        "release": release.id,
        "city_id": city.id,
        "ingested_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "extract_seconds": round(extract_seconds, 1),
        "hotels_raw": n_hotels_raw,
        "hotels_after_dedupe": n_hotels_final,
        "dedupe_groups_merged": len(merged_groups),
        "dedupe_records_absorbed": sum(len(d.member_ids) for d in merged_groups) - len(merged_groups),
        "entity_qa_excluded_count": len(entity_qa_excluded),
        "entity_qa_excluded_names": [name for _, name in entity_qa_excluded],
        "pois": n_pois,
        "segments": n_segments,
        "green_spaces": n_green_spaces,
    }
    with open(out_dir / "manifest.json", "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    return manifest
