# ADR-017 — Exclude brands, programmes and offices without a hotel establishment

Date: 2026-09-11. Status: accepted implementation on explicit owner instruction
(Bloc B, following the external acceptance of Bloc A / ADR-016).

## Context

The pilot proposal included ALL Accor, a group loyalty/booking programme rather
than a hotel. Hotel taxonomy and a recognised brand are insufficient identity
evidence. Corporate offices can have addresses, websites and phone numbers;
real hotels can share an address with their operator's office.

## Decision

1. Run deterministic programme, office and umbrella-name detection before all
   brand/lodging allowances, across the dataset, not merely the pilot cohort.
   `brand_rules.json` is shared by Python and the JavaScript build guard.
   Offices include sales, reservations, headquarters and hotel management;
   literal rules cover the launch cities' languages. English programme names
   and documented local-script aliases are supported.
2. Withhold and log uncertain matches. Audit each existing candidate; retain
   externally supported property aliases through exact ID + exact name +
   specific-reason exceptions. An exception never permits a new office suffix.
   Affiliation after a named hotel is not an umbrella record. Bare hotel brands
   (`Marriott`, `Hilton`, `Hyatt`) are not globally banned.
3. Pin excluded IDs and slugs, so renaming or dropping the name cannot revive
   a page. Enforce again at validation, publication (including draft/noindex),
   export and build. Nearby POIs remain contextual facts, not hotel identities.
4. Purge matching hotels and dependent scores/facts, search/card exports and
   references. Retire publication records. Keep backups and recompute city
   aggregates without changing surviving scores, score version or timestamps.
5. Quantify the generic attribute signal **without activating it**: explicit
   address-country conflict, no non-empty contact channel in Overture, and
   exact duplicated coordinates among distinct IDs of the same identified
   group. Report each component, OR and AND counts, coverage and unknowns.
   Missing street is incomplete, not incoherent; suburbs/NYC's NJ coverage are
   not address conflicts. Contacts not retrieved are unknown, never absent.
   Name-derived groups are heuristic; structured source brands are preferred.
   No diagnostic count changes eligibility or publication.

## Consequences and validation

The rules are a reviewed, deterministic barrier, not a proof of universal entity
correctness. Sparse names and upstream misclassification still require Bloc F's
external cohort review. No scoring, indexing or hosting change is authorised
by this ADR. No paid dependency or runtime API is introduced.

See [Bloc B audit](../reports/bloc-b-brands.md) and its machine-readable report
for the 12-city counts, sources, exceptions, quarantines, diagnostic limitations
and validation results. CI covers ingestion, stale ETL, publication and static
exports, Python/JavaScript parity, tourist-name protection and inert diagnostics.

Cloudflare Pages is Git-connected. The live Singapore Boys' Home URL still
returned its old scored page (HTTP 200) at 21:14:34 UTC, over ten minutes after
the initial check. GitHub exposed no deployment record. This does not establish
whether Cloudflare launched a build. The owner will inspect the dashboard;
no deployment trigger, retry or configuration change is to be forced.
