# ADR-020 — Proper-name romanization with explicit reliability limits

Date: 2026-09-12. Status: accepted under Bloc D owner instruction.

Keep original names and existing ASCII canonical slugs. Display Latin (Original)
using current source Latin variants first, then pinned AnyAscii 0.3.3 (ISC,
free, offline) only for documented supported scripts. Unsupported scripts retain
originals and remain ineligible for indexing. No translation or fabricated
English hotel names. Romanization is labelled approximate, never official.

Allow Latin/Cyrillic/Greek/Hangul/kana-only text; reject Han, Thai, Arabic,
Hebrew and other unsupported letters without source alternatives. This reversible
readability policy is not a claim of measured linguistic accuracy. All remaining
hotel-identity/type/publication gates still apply. No flag or cohort is promoted.

POI alternatives require consistent same-name source evidence because legacy
why-facts lack GERS IDs; missing/conflicting aliases are not guessed. Preserve
original identities for exclusion checks. Retrieval uses the release catalog;
no external API or romanization at page view. Future ingestion retains names JSON.

Rich static exports exceeded local TypeScript literal-inference memory. Parse
committed JSON at build time with explicit types instead; browser code only
receives the existing static output. Compact repeated name metadata in search
and facts and reject public data assets over 25 MiB. This is a technical size
fix, not a serving architecture or framework change.

See reports/bloc-d-names.md for counts/reliability and i18n-options.md for a
future French version. No multilingual implementation is authorized here.
