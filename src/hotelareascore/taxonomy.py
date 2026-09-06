"""Overture taxonomy -> internal category classification.

Reads data/config/taxonomy-mapping.yml. All matching happens on the CURRENT
Overture fields (`taxonomy.primary`, `taxonomy.hierarchy`), never the
deprecated `categories` field (docs/adr/003).
"""
from __future__ import annotations

from .config import load_taxonomy_mapping


def hotel_included_types() -> set[str]:
    return set(load_taxonomy_mapping()["hotel_types"]["included"])


def hotel_excluded_types() -> set[str]:
    return set(load_taxonomy_mapping()["hotel_types"]["excluded"])


def is_hotel_type(taxonomy_primary: str | None) -> bool:
    """True if this place's leaf taxonomy is an in-scope hotel type (v1 product
    scope — see the comment block in taxonomy-mapping.yml)."""
    if not taxonomy_primary:
        return False
    return taxonomy_primary in hotel_included_types()


def hotel_sql_predicate(column: str = "taxonomy.primary") -> str:
    included = sorted(hotel_included_types())
    values = ", ".join(f"'{v}'" for v in included)
    return f"{column} IN ({values})"


def dimension_names() -> list[str]:
    return list(load_taxonomy_mapping()["dimensions"].keys())


def dimension_config(dimension: str) -> dict:
    dims = load_taxonomy_mapping()["dimensions"]
    if dimension not in dims:
        raise KeyError(f"Unknown dimension '{dimension}'. Known: {sorted(dims)}")
    return dims[dimension]


def matches_point_dimension(
    dimension: str, taxonomy_primary: str | None, taxonomy_hierarchy: list[str] | None
) -> bool:
    """Pure-Python classifier mirroring the SQL predicate built in
    poi_sql_predicate — used by unit tests and any Python-side reclassification
    (e.g. reason codes)."""
    if dimension == "quietness_proxy":
        raise ValueError("quietness_proxy has no single point predicate; see quietness sub-categories")
    cfg = dimension_config(dimension)
    hierarchy = taxonomy_hierarchy or []
    if "categories" in cfg and taxonomy_primary in set(cfg["categories"]):
        return True
    if "hierarchies" in cfg and hierarchy and hierarchy[0] in set(cfg["hierarchies"]):
        return True
    return False


def poi_sql_predicate(dimension: str, primary_col: str = "taxonomy.primary", hierarchy_col: str = "taxonomy.hierarchy") -> str:
    cfg = dimension_config(dimension)
    clauses: list[str] = []
    if "categories" in cfg:
        values = ", ".join(f"'{v}'" for v in cfg["categories"])
        clauses.append(f"{primary_col} IN ({values})")
    if "hierarchies" in cfg:
        values = ", ".join(f"'{v}'" for v in cfg["hierarchies"])
        clauses.append(f"list_contains(ARRAY[{values}], {hierarchy_col}[1])")
    if not clauses:
        raise ValueError(f"dimension '{dimension}' has no categories/hierarchies configured")
    return "(" + " OR ".join(clauses) + ")"


def all_point_poi_categories() -> set[str]:
    """Union of every explicit category leaf used by any point-based dimension
    (food_essentials, transit_access, nightlife_access, family_convenience) —
    used to build the flat POI extract's category filter alongside the
    hierarchy-based walkability_density match."""
    dims = load_taxonomy_mapping()["dimensions"]
    cats: set[str] = set()
    for name, cfg in dims.items():
        if name == "quietness_proxy":
            continue
        cats |= set(cfg.get("categories", []))
    return cats


def all_point_poi_hierarchies() -> set[str]:
    dims = load_taxonomy_mapping()["dimensions"]
    hiers: set[str] = set()
    for name, cfg in dims.items():
        if name == "quietness_proxy":
            continue
        hiers |= set(cfg.get("hierarchies", []))
    return hiers


def quietness_config() -> dict:
    return load_taxonomy_mapping()["dimensions"]["quietness_proxy"]


def nearby_facts_display_exclude() -> set[str]:
    return set(load_taxonomy_mapping().get("nearby_facts_display_exclude", []))
