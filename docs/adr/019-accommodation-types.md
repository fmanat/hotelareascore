# ADR-019 — Accommodation type is identity metadata

Date: 2026-09-12. Status: accepted under owner's Bloc C instruction.

Classify seven accommodation types using explicit property names, Overture
primary category and structured operator, with conservative unknown fallback.
Only hotel is eligible for further indexing gates. B&B remains noindex pending
reception evidence. OYO is mixed: Home evidence overrides hotel taxonomy;
ordinary OYO hotels remain hotels. Blueground furnished rental evidence maps to
whole-home; mixed Sonder/Domio defaults unknown without property evidence.
Apartments without hotel/service evidence conservatively map to whole-home;
this is reversible metadata, not verified reception availability.

Add English type labels to static profiles, limited profiles and search.
Preserve every retained A/B row, existing scores, source dates and stable slugs.
No re-ingestion of rejected lodging: report category-level potential only.
No score, indexing flag, cohort promotion, sitemap or deployment changes.
All later cohorts must apply this gate; external verification remains necessary.
