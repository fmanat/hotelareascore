"""Overture Maps release discovery + DuckDB access.

docs/adr/003: release path is discovered from the bucket's own release/
catalog listing, never hardcoded; upstream schema is checked before use and
the run fails closed (raises SchemaError) if expected fields are missing —
staleness over wrongness (CLAUDE.md hard rule 10).
"""
from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass

import duckdb

BUCKET_URL = "https://overturemaps-us-west-2.s3.amazonaws.com/"
S3_REGION = "us-west-2"

_RELEASE_RE = re.compile(r"^release/(\d{4}-\d{2}-\d{2})\.(\d+)/$")

# Columns the pipeline reads by name. If Overture renames/removes one of
# these, we must stop rather than silently score on nulls.
REQUIRED_PLACE_COLUMNS = {
    "id", "geometry", "confidence", "names", "addresses",
    "taxonomy", "basic_category", "sources", "bbox",
}
REQUIRED_SEGMENT_COLUMNS = {"id", "subtype", "class", "geometry", "bbox"}


class SchemaError(RuntimeError):
    """Raised when the upstream schema no longer matches what we code against."""


@dataclass(frozen=True)
class Release:
    id: str  # e.g. "2026-08-19.0"


def discover_latest_release(con: duckdb.DuckDBPyConnection | None = None) -> Release:
    """List the bucket's release/ prefixes and return the newest one.

    This IS the catalog lookup ADR-003 requires (no hardcoded release path):
    Overture publishes releases as top-level S3 prefixes under `release/`.

    Fetched via DuckDB's own httpfs (rather than stdlib urllib) so release
    discovery uses the exact same HTTP/TLS stack as the parquet reads that
    follow it — one less thing to diverge between environments.
    """
    own_con = con is None
    if own_con:
        con = duckdb.connect()
        con.execute("INSTALL httpfs; LOAD httpfs;")
    url = BUCKET_URL + "?list-type=2&delimiter=/&prefix=release/"
    body = con.execute(f"SELECT content FROM read_text('{url}')").fetchone()[0]
    if own_con:
        con.close()
    ns = {"s3": "http://s3.amazonaws.com/doc/2006-03-01/"}
    root = ET.fromstring(body)
    releases: list[tuple[str, int, str]] = []
    for cp in root.findall("s3:CommonPrefixes", ns):
        prefix = cp.find("s3:Prefix", ns).text
        m = _RELEASE_RE.match(prefix)
        if not m:
            continue
        date_str, minor = m.groups()
        releases.append((date_str, int(minor), f"{date_str}.{minor}"))
    if not releases:
        raise SchemaError(
            "Overture release catalog returned no parseable release/ prefixes; "
            "refusing to guess a release path (fail closed)."
        )
    releases.sort(key=lambda r: (r[0], r[1]))
    return Release(id=releases[-1][2])


def connect() -> duckdb.DuckDBPyConnection:
    con = duckdb.connect()
    con.execute("INSTALL httpfs; LOAD httpfs;")
    con.execute("INSTALL spatial; LOAD spatial;")
    con.execute(f"SET s3_region='{S3_REGION}';")
    con.execute("SET enable_progress_bar=false;")
    return con


def places_path(release: Release) -> str:
    return f"s3://overturemaps-us-west-2/release/{release.id}/theme=places/type=place/*"


def segments_path(release: Release) -> str:
    return f"s3://overturemaps-us-west-2/release/{release.id}/theme=transportation/type=segment/*"


def check_schema(con: duckdb.DuckDBPyConnection, path: str, required_columns: set[str], label: str) -> None:
    rows = con.execute(f"DESCRIBE SELECT * FROM read_parquet('{path}') LIMIT 0").fetchall()
    actual = {r[0] for r in rows}
    missing = required_columns - actual
    if missing:
        raise SchemaError(
            f"{label}: upstream schema is missing expected column(s) {sorted(missing)}. "
            "Failing closed (CLAUDE.md hard rule 10) — no scores/pages will be published "
            "from this run. Update the schema adapter in overture.py before re-running."
        )
