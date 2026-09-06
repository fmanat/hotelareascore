-- page_publication (docs/seo-policy.md §6, CLAUDE.md hard rule 2):
-- "Indexability is a decision recorded in page_publication, never a side
-- effect of a route existing." This is the serving-world (Supabase
-- Postgres) DDL for that table -- docs/adr/002 lists page_publication
-- among the serving tables but doesn't specify its schema; this migration
-- is that specification.
--
-- Not yet applied anywhere: Supabase isn't provisioned yet (docs/STATE.md).
-- The overnight mission's operational stand-in
-- (src/hotelareascore/publication.py) uses an equivalent SQLite schema
-- locally so the decision logic and its "never a side effect" guarantee
-- can be built and tested now, and ported to this exact table once
-- Supabase exists -- see that module's docstring for the mapping.

CREATE TABLE IF NOT EXISTS page_publication (
    page_type       TEXT NOT NULL CHECK (page_type IN ('hotel', 'city', 'static')),
    page_id         TEXT NOT NULL,       -- hotel_id (Overture GERS id), city_id, or a static slug ('home', 'methodology', 'compare', 'legal-notice', ...)
    status          TEXT NOT NULL CHECK (status IN ('draft', 'noindex', 'indexable', 'retired')),
    reason          TEXT NOT NULL,       -- human-readable justification, always required -- CLAUDE.md hard rule 2
    decided_by      TEXT NOT NULL,       -- 'system:<script-or-rule-name>' or 'owner:<name>'
    decided_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    score_version   TEXT,                -- the score_version this decision was made against, if applicable (hotel/city pages)
    PRIMARY KEY (page_type, page_id)
);

-- One row per page identity; a status change is an UPDATE (with a new
-- decided_at/decided_by/reason), never a delete-and-reinsert, so history
-- stays auditable via decided_at. A full audit trail (every past decision,
-- not just the current one) would need a separate append-only
-- page_publication_history table -- not needed yet at this scale, noted
-- here for whoever revisits this once real publication activity exists.

CREATE INDEX IF NOT EXISTS idx_page_publication_status ON page_publication (status);
CREATE INDEX IF NOT EXISTS idx_page_publication_type_status ON page_publication (page_type, status);
