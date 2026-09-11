"""page_publication (docs/seo-policy.md §6, CLAUDE.md hard rule 2):
"Indexability is a decision recorded in page_publication, never a side
effect of a route existing."

Supabase isn't provisioned yet (docs/STATE.md), so this is a local,
file-based operational stand-in with the SAME schema shape as
`migrations/0001_page_publication.sql` (SQLite's dynamic typing accepts
that Postgres DDL almost verbatim; the CHECK constraints are re-enforced
in Python here since SQLite's are easy to bypass accidentally). Once
Supabase exists, `_upsert` below is the only function that needs to change
(swap the sqlite3 connection for a Postgres one) -- every caller goes
through `get_status`/`set_status`, never raw SQL, precisely so that swap
doesn't ripple through the codebase.

The hard guarantee this module exists to enforce: a page's `indexable`
flag in the static site (`web/src/pages/**`) is read FROM a row here that
some script explicitly wrote with a `reason`, never computed inline in a
page template from "this route exists, therefore index it."
"""
from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator, Literal

from .config import REPO_ROOT

SERVING_DIR = REPO_ROOT / "data" / "serving"
DB_PATH = SERVING_DIR / "page_publication.sqlite"

PageType = Literal["hotel", "city", "static"]
Status = Literal["draft", "noindex", "indexable", "retired"]
_PAGE_TYPES = {"hotel", "city", "static"}
_STATUSES = {"draft", "noindex", "indexable", "retired"}

_SCHEMA = """
CREATE TABLE IF NOT EXISTS page_publication (
    page_type       TEXT NOT NULL,
    page_id         TEXT NOT NULL,
    status          TEXT NOT NULL,
    reason          TEXT NOT NULL,
    decided_by      TEXT NOT NULL,
    decided_at      TEXT NOT NULL,
    score_version   TEXT,
    PRIMARY KEY (page_type, page_id)
);
CREATE INDEX IF NOT EXISTS idx_page_publication_status ON page_publication (status);
"""


@contextmanager
def connect(db_path: Path = DB_PATH) -> Iterator[sqlite3.Connection]:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(db_path)
    try:
        con.executescript(_SCHEMA)
        yield con
        con.commit()
    finally:
        con.close()


def set_status(
    con: sqlite3.Connection,
    page_type: PageType,
    page_id: str,
    status: Status,
    reason: str,
    decided_by: str,
    score_version: str | None = None,
    hotel_name: str | None = None,
) -> None:
    """The only way a page's publication status changes. Always requires a
    reason and a decider -- there is no code path that flips a status
    silently.

    `hotel_name`, when given, enforces docs/adr/014's hard gate: a hotel
    whose name is purely numeric (slug.py's `is_numeric_name` -- an
    unresolved Overture source reference, not a real name,
    docs/reports/nyc-bbox-options.md) can never be recorded 'indexable',
    independent of confidence or any other signal -- that report found
    "low confidence stays non-indexable" does NOT structurally protect
    against this, since a numeric-name record can still score high
    confidence on every other signal. Optional (not every caller knows the
    name -- static/city pages have none) but every hotel-indexable call
    that CAN pass it should, so this is the actual backstop, not just a
    convention callers might forget."""
    if page_type not in _PAGE_TYPES:
        raise ValueError(f"page_type must be one of {_PAGE_TYPES}, got {page_type!r}")
    if status not in _STATUSES:
        raise ValueError(f"status must be one of {_STATUSES}, got {status!r}")
    if not reason.strip():
        raise ValueError("reason is required (CLAUDE.md hard rule 2: a recorded decision, not a side effect)")
    if page_type == "hotel" and status != "retired":
        from .institutions import assert_no_institutions

        assert_no_institutions([{"id": page_id, "name": hotel_name}], context="publication")
    if page_type == "hotel" and status == "indexable" and hotel_name is not None:
        from .slug import is_numeric_name

        if is_numeric_name(hotel_name):
            raise ValueError(
                f"Refusing to mark hotel {page_id!r} (name={hotel_name!r}) indexable -- "
                "docs/adr/014: numeric-name records are structurally barred from indexing, "
                "independent of confidence. Not a bug in this hotel's data; fix the name "
                "resolution upstream (entity_qa.py) before ever indexing this record."
            )
    con.execute(
        """
        INSERT INTO page_publication (page_type, page_id, status, reason, decided_by, decided_at, score_version)
        VALUES (?, ?, ?, ?, ?, datetime('now'), ?)
        ON CONFLICT (page_type, page_id) DO UPDATE SET
            status = excluded.status,
            reason = excluded.reason,
            decided_by = excluded.decided_by,
            decided_at = excluded.decided_at,
            score_version = excluded.score_version
        """,
        (page_type, page_id, status, reason, decided_by, score_version),
    )


def get_status(con: sqlite3.Connection, page_type: PageType, page_id: str) -> dict | None:
    row = con.execute(
        "SELECT page_type, page_id, status, reason, decided_by, decided_at, score_version "
        "FROM page_publication WHERE page_type = ? AND page_id = ?",
        (page_type, page_id),
    ).fetchone()
    if row is None:
        return None
    cols = ["page_type", "page_id", "status", "reason", "decided_by", "decided_at", "score_version"]
    return dict(zip(cols, row))


def is_indexable(con: sqlite3.Connection, page_type: PageType, page_id: str) -> bool:
    """Whether this page's RECORDED decision is 'indexable'. This is only
    half of the real gate -- the site's own FLAGS.PUBLIC_INDEXING_ENABLED
    (and HOTEL_PAGE_INDEXING_ENABLED for hotel pages) must ALSO be on
    before a page actually renders index,follow (see BaseLayout.astro).
    Both a recorded decision AND an explicit flag must agree; neither
    alone is sufficient."""
    row = get_status(con, page_type, page_id)
    return row is not None and row["status"] == "indexable"


def list_by_status(con: sqlite3.Connection, status: Status, page_type: PageType | None = None) -> list[dict]:
    if page_type:
        rows = con.execute(
            "SELECT page_type, page_id, status, reason, decided_by, decided_at, score_version "
            "FROM page_publication WHERE status = ? AND page_type = ?",
            (status, page_type),
        ).fetchall()
    else:
        rows = con.execute(
            "SELECT page_type, page_id, status, reason, decided_by, decided_at, score_version "
            "FROM page_publication WHERE status = ?",
            (status,),
        ).fetchall()
    cols = ["page_type", "page_id", "status", "reason", "decided_by", "decided_at", "score_version"]
    return [dict(zip(cols, r)) for r in rows]
