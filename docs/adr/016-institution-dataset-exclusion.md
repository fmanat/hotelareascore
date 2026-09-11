# ADR-016 — Exclude non-tourist institutions from the hotel dataset

- **Status:** accepted (implementation authorized by the owner; Bloc A review pending)
- **Date:** 2026-09-11
- **Scope:** night mission #3, Bloc A only

## Context

The owner found Singapore Boys' Home in the proposed cohort. Indexing controls
are insufficient: an institution must not receive even a noindex hotel page,
a search result or a comparison card. The legacy entity filter let lodging
words and hotel brands override exclusion signals and discarded non-Latin
characters before matching.

## Decision

1. Run institution checks before deduplication and before every legacy
   brand/lodging allowance. Keep the old behavior for other entity families.
2. Share a versioned literal lexicon between Python ingestion and the Node
   prebuild guard. Cover English, French, Italian, Spanish, Catalan, Dutch,
   Portuguese, Japanese, Thai, Arabic, Chinese, Malay and Tamil. Preserve
   scripts, normalize Latin accents/apostrophes/spacing, and use word
   boundaries for spaced languages and substrings for unspaced scripts.
3. Withhold suspicious records and log ID, name, language, matched term and
   reason. A match is a reason for quarantine, not proof of an institution.
   Broad ambiguous signals (`shelter`, `refuge`, `foyer`, `care`, `medical`
   and their local equivalents) require review before restoration.
4. Never exclude generic `Home`, `House`, `hostel`, tourist youth hostels,
   or their local tourism terms alone. A collision can be cleared only for
   an externally reviewed ID + exact normalized name + allowed reason.
   Neither a hotel brand nor a lodging word exempts any institution family.
5. Pin the 46 quarantined snapshot IDs (and old slugs) so a later rename or
   missing name cannot restore them. Restoration requires an evidence-backed
   code review, including removal from quarantine; no runtime override.
6. Purge existing hotel, score and nearby-fact rows, retire publication
   records, remove all served references and recompute city summaries.
   Keep remaining per-hotel scores, their versions and timestamps unchanged.
   Keep ETL backups and an audit; don't replace the pilot cohort in Bloc A.
7. Fail validation/export on contaminated ETL. Before Astro builds, scan
   committed exports including search shards, comparisons and city
   representatives. This also protects deployments that have no local ETL.

## Limits and consequences

The heuristic is not a multilingual identity-verification service. Opaque
names with no institutional signal can still escape; zero matches after a
scan is not proof of zero institutions. Mandatory external identity review
of the cohort belongs to Bloc F. That work has not started.

There are intentional false exclusions pending review, especially among
ambiguous tourism-themed names. This implements the owner's explicit
fail-closed preference. The report records these without labeling them as
confirmed prisons/care homes. No scoring formula, indexing flag, paid
service or new dependency is introduced.

See [the complete scan and validation report](../reports/bloc-a-institutions.md).
