# Bloc A — Non-tourist institution exclusion

Date: 2026-09-11. Owner-authorized Bloc A only. Block B has not started.

## Result

**33,966 existing hotel records scanned across all 12 configured cities; 46 quarantined and removed, 33,920 remain.** Eleven externally checked tourist-name collisions are preserved. These are exclusion decisions, **not 46 externally verified institutional classifications**. Ambiguous matches remain excluded pending review.

The input is the complete existing `hotels.parquet` dataset, not the 200-hotel cohort and not a sample. Source release: `2026-08-19.0`, independently rediscovered from the Overture catalog. ETL snapshots were recovered from the existing local checkout and copied into this workspace. An additional fresh raw extraction was attempted but made no completed extract and was stopped; it is not counted as a scan. No claim is made about all worldwide Overture places, out-of-bbox points, or raw records already rejected by earlier ingestion.

Each city’s pre-purge SHA-256, all 46 IDs/names/reasons, every reviewed exception and removed web reference counts are in [the machine-readable audit](bloc-a-institutions.json). ETL backups remain locally under `data/etl/2026-08-19.0/<city>/institution-backup/`.

## Entire-dataset counts by city and reason

Reasons count the first matching family only, so columns sum exactly to exclusions. The JSON retains all matched families/languages. `Medical` includes ambiguous care/medical-name signals; `Shelter` includes ambiguous refuge/foyer tourism names.

| City | Scanned | Child | Elder | Detention | Rehab | Shelter | Medical | Excluded | Remaining |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| london | 4397 | 0 | 2 | 0 | 2 | 1 | 3 | 8 | 4389 |
| bangkok | 7546 | 0 | 4 | 0 | 0 | 0 | 2 | 6 | 7540 |
| paris | 3582 | 0 | 1 | 0 | 0 | 4 | 0 | 5 | 3577 |
| rome | 5040 | 0 | 2 | 0 | 0 | 5 | 0 | 7 | 5033 |
| barcelona | 1720 | 0 | 1 | 0 | 0 | 4 | 0 | 5 | 1715 |
| amsterdam | 1071 | 0 | 0 | 0 | 0 | 1 | 0 | 1 | 1070 |
| lisbon | 1289 | 0 | 0 | 0 | 0 | 1 | 1 | 2 | 1287 |
| sydney | 1078 | 1 | 0 | 0 | 0 | 0 | 0 | 1 | 1077 |
| tokyo | 2745 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 2745 |
| dubai | 2067 | 1 | 0 | 0 | 0 | 0 | 1 | 2 | 2065 |
| new_york | 2194 | 0 | 0 | 0 | 0 | 1 | 4 | 5 | 2189 |
| singapore | 1237 | 3 | 1 | 0 | 0 | 0 | 0 | 4 | 1233 |
| **Total** | 33966 | 5 | 11 | 0 | 2 | 17 | 11 | 46 | 33920 |

Zero in Tokyo or in the detention column means no matching record in this snapshot. Singapore Boys’ Home is counted under child care because that is the matched naming signal, not a classification of its legal function.

## Language coverage

| Cities | Languages covered |
|---|---|
| London, Sydney, New York City metro | English |
| Paris | French + English |
| Rome | Italian + English |
| Barcelona | Spanish, Catalan + English |
| Amsterdam | Dutch + English |
| Lisbon | Portuguese + English |
| Tokyo | Japanese + English |
| Bangkok | Thai + English |
| Dubai | Arabic + English |
| Singapore | English, Chinese, Malay, Tamil |

All 13 languages have rules and regression specimens for all six families. This is a reviewed heuristic lexicon, not a native-speaker certification or evidence of complete recall. Unicode normalization preserves Thai/Tamil vowel signs and other non-Latin characters. Home/House and tourist hostel words alone never trigger exclusion.

## Confirmed specimens and useful collisions

- [MSF](https://www.msf.gov.sg/what-we-do) identifies the Singapore Boys’/Girls’ Homes in its youth rehabilitation work; the owner’s seed ID `2511f051-4294-4d3c-8b4c-bc553ba67d6c` is removed.
- [MSF explicitly identifies Singapore Boys’ Hostel as a children’s home](https://www.msf.gov.sg/media-room/article/closing-speech-by-sps-eric-chua-at-the-second-reading-of-the-social-residential-homes-bill). Thus `hostel` cannot be an unconditional allowance.
- [The operator identifies Andrew and Grace Home as the former name of Gladiolus Place](https://www.gladiolusplace.org.sg/about-gladiolus-place), a residential children’s home. Its otherwise opaque name is covered explicitly.
- [Sankofa Care](https://sankofacare.co.uk/) describes residential children’s care. [Ronald McDonald House Charities](https://rmhc.org.uk/wp-content/uploads/2025/03/Digital-Family-Leavers-Pack-2025.pdf) documents hospital-family accommodation including Moorfields.
- [Shelter Jordan’s operator](https://www.thdv.nl/zien/verdieping/181/thdv-biedt-jonge-asielzoekers-onderdak) describes housing unaccompanied minor asylum seekers there. It remains excluded despite the stale tourist-hostel name. [Shelter City](https://shelterhostel.amsterdam/) currently offers tourist rooms and bookings and is preserved as an exact-ID exception.
- The eight Mama Shelter records are preserved with individual official source URLs in the lexicon; [the brand](https://mamashelter.com/) offers hotel accommodation. The London source is Accor’s hotel listing, not a successful fetch of the London property website.
- [Siam Shelter](https://www.siamshelter.com/) is preserved after checking its own hotel site. Golden Foyer Bangkok is preserved after its source address `541, 8 Luang Phaeng Rd` matched [the bookable property listing](https://www.booking.com/hotel/th/golden-foyer-suvarnabhumi-airport.en-gb.html).

Other withheld names such as B&B Maru Shelter, Refuge Hostel, Halfway House Farm or an apartment referring to Health Care City **are not declared institutions by this report**. Their identity/use is unresolved within Bloc A; the owner’s instruction is to exclude and log doubt. Exact-ID exceptions are limited to 11 checked collisions; they do not constitute the cohort-wide external gate of Bloc F.

Terminology references include [French public-service EHPAD guidance](https://solidarites.gouv.fr/ehpad), [Japan’s Ministry of Justice facility terminology](https://www.moj.go.jp/keiji_shisetsu_index.html), and [Thailand’s Department of Older Persons](https://www.dop.go.th/). The literal lexicon and fixtures are inspectable in the source tree.

## Removal and preservation checks

- Global search: 33,966 → 33,920; exactly the 46 audited slugs removed, all surviving search objects identical.
- Static hotel cards: 15,749 → 15,738; 11 removed, no new cards. Search shards, comparisons and city representatives also purged, including two representatives with null slugs.
- Excluded IDs absent from all 12 hotel/score/nearby-fact datasets. Remaining score rows compared in both directions using SQL `EXCEPT ALL`: zero differences. Score version stays 1.2.1; source timestamps remain unchanged.
- City counts and summary means/medians recomputed from the remaining score rows. Old local validation reports are marked as requiring revalidation rather than left as stale clean reports. Full data refresh/recalibration was not run.
- All 46 local publication records set to `retired`. Existing staged cohort proposal remains historical evidence: it now has 2 removed entries (Singapore Boys’ Home and B&B Maru Shelter), so only 198/200 are still present. Do not use the old 214-URL dry-run report as a current readiness statement. Replacement/reconstruction is deferred to Bloc F.
- 1,825 surviving names contain the whole word Home/House; 1,061 contain hostel/hostels (overlap possible). These are preservation counts, not independent verification of every survivor.

## Tests and build

- 98 positive regression specimens across 13 languages, 30 negative tourist/Home/House specimens and 11 exact-record exceptions. Zero missed positives and zero false exclusions in these explicit fixture sets.
- Integration tests exercise exclusion before deduplication with misleading hotel brands, complete reason logging, stale ETL rejection, publication rejection for draft/noindex/indexable, renamed/nameless quarantined IDs, and static/search/comparison/city export barriers.
- Python/JavaScript parity test covers all lexicon literals, regression names and ID/slug exceptions; production exports are also checked.
- Local `make test`: **284 passed, 1 expected failure** (the pre-existing CJK liquor-shop limitation, outside Bloc A). Pytest now explicitly imports this checkout’s `src`, preventing another installed editable checkout from being tested accidentally.
- Local real-data Astro build: 15,759 HTML pages; SEO assertions passed (unique titles, one canonical, JSON-LD and sitemap/publication consistency). Typecheck: zero errors/warnings, one pre-existing async-function hint.
- GitHub CI: **all five jobs passed** for commit `1d4e4ef` ([run 34646720383](https://github.com/fmanat/hotelareascore/actions/runs/34646720383)), including E2E.

## Reproduction and limits

From an unpurged copy of the existing release: `python3 scripts/exclude_institutions.py` produces the audit; `python3 scripts/exclude_institutions.py --apply` purges ETL and committed exports, retaining local backups. `node web/scripts/institution-guard.mjs` checks every current export. `make test` exercises regressions. The script preserves an existing pre-purge report when no matches remain.

This closes the known institution naming/ID paths, not the general identity-verification problem. Unknown institutions with opaque names can escape a lexicon; the gate in Bloc F remains necessary. No Block B work, score formula change, new indexable URL, paid dependency or indexing flag change was made.

## Production handoff — unresolved

The code/data commit `1d4e4ef` is pushed and its CI is green. A live GET
**after CI completed** still returned HTTP 200 and the Singapore Boys’ Home
scored page at `/hotel/singapore-boys-home-3ba67d6c`. This is **not** a
successful production removal. GitHub exposes no Cloudflare deployment
status for this commit. The available API authentication returned HTTP 403
when reading the `staycontext` Pages project, and browser discovery returned
no connected browser. No deployment was performed in this session.

The owner was asked to provide a connected Cloudflare browser or deploy
`origin/main` to the existing `staycontext` project. Recheck the old URL and
search index afterward; no indexing flag needs changing. The production
blocker must remain visible until those checks pass.
