# ADR-014 — Numeric-name hotels: hard, structural indexability gate

- **Status:** accepted
- **Date:** 2026-09-09 (night mission #3, Tache 6)
- **Decision recorded from:** `docs/reports/nyc-bbox-options.md` §"Numeric-name
  hotel slugs" (2026-09-07, proposed for owner decision, not applied at
  the time); night mission #3 order: implement the already-validated
  proposal, no new decision to make.

## Context

`docs/reports/nyc-bbox-options.md` found 9 hotels across 3 cities with a
purely-numeric `name` (e.g. `"8468671"`) — almost certainly an unresolved
Overture source reference, not a real hotel name. That report shipped a
slug fix (`slug.py` prefixes `hotel-` so the URL doesn't read as a bare
reference number) but explicitly deferred a bigger question: **should a
numeric-name record be structurally barred from ever being marked
indexable**, independent of its confidence score? The report's own
finding was that "low confidence stays non-indexable" does NOT
structurally protect against this — a numeric-name record can still score
high confidence on every other signal (nearby facts, dimension scores),
so confidence alone doesn't catch it.

That question is now answered (owner GO, per this session's order) —
this ADR is the implementation, not a new deliberation.

## Decision

A hard, structural gate, enforced at the lowest practical layer so no
caller can accidentally bypass it:

1. **`slug.py` gains `is_numeric_name(name)`** — the single source of
   truth for "is this a numeric-only name" (raw name, trimmed, entirely
   digits — matches `validate.py`'s existing `n_numeric_name` QA
   definition exactly). `validate.py`'s SQL aggregate stays SQL (it runs
   over the full per-city table) but is now commented as textually
   identical to this function on purpose, rather than an independent
   regex that could drift.
2. **`publication.set_status()` itself refuses** to record a hotel's
   status as `'indexable'` when a `hotel_name` is passed and
   `is_numeric_name(hotel_name)` is true — raises `ValueError`, doesn't
   silently downgrade the status (CLAUDE.md hard rule 10: fail closed).
   `hotel_name` is optional (static/city callers don't have one) but every
   hotel-indexable call site that CAN pass it now does
   (`compute_publication.py`, the go-live checklist's illustrative step-5
   snippet).
3. **`webdata.py`'s `export_city` checks it again**, independent of what
   `page_publication` says, before ever setting a hotel's
   `publication_status` to `"indexable"` in the exported JSON that
   templates actually read. Belt-and-suspenders: if the DB ever ended up
   with a stale/manually-edited `'indexable'` row for a numeric-name
   hotel (bypassing #2 some other way), the actual build still won't
   render it as indexable.

## Consequences

- No visible change today: the pilot cohort (`pilot-cohort-proposal.csv`)
  already excludes numeric-name records by construction (gate 6,
  `docs/seo-policy.md §4`), and nothing in this repo currently sets any
  hotel to `'indexable'` at all (everything is staged `draft`,
  `docs/reports/go-live-seo-checklist.md`) — so the gate has nothing to
  block yet. It's there for the future: a later automated cohort-expansion
  process, or a manual mistake, can no longer index one of these records
  even if it passed every other gate.
- Tested at the unit level (`tests/test_slug.py`, `tests/test_publication.py`)
  — the gate raises for a numeric name, is a no-op for a real name, is a
  no-op when no name is passed at all (static/city calls unaffected), and
  doesn't block `'draft'`/`'noindex'` for a numeric-name hotel (only
  `'indexable'` is barred — it still needs *some* recorded status).
- Reversible: three small, independent checks, each removable on its own
  without breaking the others.
