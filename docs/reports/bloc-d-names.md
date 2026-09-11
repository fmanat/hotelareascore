# Bloc D — readable proper names

2026-09-12. Release 2026-08-19.0. Full 12-city scan after A/B/C. No indexing, cohort promotion or deployment.

| City | Retained | Non-Latin names before | Name gate unlocked | Also type hotel | Still name-ineligible |
|---|---:|---:|---:|---:|---:|
| london | 4364 | 20 | 3 | 0 | 27 |
| bangkok | 7517 | 2978 | 4 | 2 | 2976 |
| paris | 3568 | 17 | 7 | 5 | 10 |
| rome | 5030 | 5 | 4 | 1 | 2 |
| barcelona | 1704 | 6 | 3 | 3 | 3 |
| amsterdam | 1065 | 0 | 0 | 0 | 0 |
| lisbon | 1282 | 1 | 0 | 0 | 1 |
| sydney | 1067 | 7 | 0 | 0 | 8 |
| tokyo | 2734 | 1672 | 143 | 128 | 1530 |
| dubai | 2060 | 82 | 5 | 5 | 77 |
| new_york | 2174 | 6 | 1 | 1 | 5 |
| singapore | 1214 | 30 | 0 | 0 | 30 |
| **Total** | 33779 | 4824 | 170 | 145 | 4669 |

170 newly readable names, 145 also classified hotel. **Zero newly indexable pages.** Other cohort gates and external verification remain mandatory. Name-ineligible includes numeric/empty/one-letter names in addition to unsupported scripts; it is not exactly non-Latin minus unlocked.

## Source coverage and actual results

Original Overture `names` retrieved by GERS ID through STAC-pruned Parquet reads for all 33,779 retained accommodation records (zero missing), plus the POIs referenced by why-fact names. Original primary names, IDs, coordinates, scores and existing slugs are preserved. Raw snapshots and asset provenance are under each local release/city `source-names*`; the extraction script is committed. No extra geospatial call at page view.

No accommodation received a usable alternative Latin name in this source snapshot: all 170 unlocks are script-limited romanization. POI alternatives do exist. Since historic why-facts lack POI IDs, a source alternative is used only when all matching same-name source records agree; conflicting or missing matches fall back conservatively.

| City | Why-fact occurrences | Source Latin primary | Source Latin alternative | Romanized | Original fallback |
|---|---:|---:|---:|---:|---:|
| london | 52034 | 51867 | 0 | 26 | 141 |
| bangkok | 89938 | 41448 | 0 | 122 | 48368 |
| paris | 42816 | 42642 | 0 | 31 | 143 |
| rome | 60326 | 60100 | 0 | 25 | 201 |
| barcelona | 20442 | 20374 | 0 | 15 | 53 |
| amsterdam | 12697 | 12651 | 0 | 14 | 32 |
| lisbon | 15384 | 15338 | 0 | 21 | 25 |
| sydney | 12799 | 12703 | 0 | 17 | 79 |
| tokyo | 32798 | 7087 | 18 | 3205 | 22488 |
| dubai | 24466 | 23621 | 0 | 16 | 829 |
| new_york | 26075 | 25922 | 0 | 23 | 130 |
| singapore | 14415 | 13524 | 0 | 10 | 881 |

Counts are fact occurrences, not distinct POIs. The JSON companion lists per-city scripts/methods and every non-Latin accommodation decision.

## Reliability policy by script

| Script/evidence | Action | Reliability limit |
|---|---|---|
| Latin, including real accents | Keep source spelling | No translation or removal of diacritics |
| Current Overture common/official Latin variant, English first | Latin (Original) | Source alias, not independent establishment verification; historical/scoped alternatives ignored |
| Cyrillic, Greek | AnyAscii, labelled romanization | Readable character mapping; language-specific/official spelling may differ |
| Hangul | AnyAscii, labelled romanization | Syllable mapping; spacing and official romanization may differ |
| Japanese kana only, optionally mixed Latin | AnyAscii, labelled romanization | Phonetic approximation; long vowels, particles and proper-name spelling may differ |
| Han/kanji (including Japanese mixed kanji/kana), Thai, Arabic, Hebrew, other scripts | Original, noindex unless source Latin variant | Context/language/vowels unavailable; never substitute Mandarin reading for Japanese |
| Missing or unsupported letters | Original, noindex | No silent letter deletion |

[AnyAscii primary documentation](https://github.com/anyascii/anyascii) describes character mapping without context and shows the limitations for Japanese Han, Thai and Arabic. We use pinned 0.3.3, ISC license, offline, €0 dependency cost. The allowlist is a reversible product-readability choice, **not measured linguistic accuracy**; external spelling/reception checks are still necessary. [Overture source model](https://docs.overturemaps.org/schema/reference/transportation/segment/) documents primary/common/rule names; the actual downloaded places names were inspected rather than assuming alternatives existed.

## Display, URLs, English UI and verification

Hotel headings, titles, breadcrumbs, structured identity, search, comparisons, city references and POI why-facts use display names. Original names remain available for searching and A/B safety guards. Transliteration is never used to rewrite existing slugs; all existing URLs remain ASCII and unchanged. No mass URL regeneration or redirect change.

UI templates and TS labels were scanned for French/non-English interface text; no such label was found. Source proper names/localities are not translated. The limited-profile type label remains English. No French routes, translations, hreflang or sitemap were introduced; see [FR options](i18n-options.md).

Rich JSON literal inference exhausted the local 2 GB TypeScript heap. Build-only typed JSON parsing removes that inference overhead; no browser filesystem access or runtime network dependency. Search retains only display metadata it uses, keeping the asset within Pages limits. Name-gate and type-gate build checks fail closed.

Validation: 464 Python tests pass (18 new name tests, one historical xfail),
two Node type/name guard tests pass, Astro typecheck has zero errors/warnings.
Full build: 15,721 pages; SEO assertions pass. New E2E fixture checks both hotel
and POI dual-script display on desktop/mobile in CI. Original 33,779 hotel rows
and columns compare equal to pre-D backups. Search asset is 19,181,941 bytes;
all current slugs remain ASCII. No score files or publication flags changed.
