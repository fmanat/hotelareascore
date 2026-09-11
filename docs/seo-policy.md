# seo-policy.md — indexing policy, page types, and the pilot hotel cohort

> Supersedes §20–21, 43–44, 51–52 of the original document, and RESOLVES the
> contradiction between the acquisition strategy (hotel-name queries) and the
> "hotel pages noindex by default" rule.

## 1. Fundamental rule

We do not try to evade Google's spam systems; we are architected so we don't
rely on low-value scaled content. Defense = original computed metrics,
interactive tool, transparent methodology, provenance, limited index footprint,
selective publication, genuine utility.

**Anti-spam test for every indexable page:** if all AI-written prose
disappeared, would the page still be useful? If no → do not index.

## 2. The contradiction, and its resolution

The marketing clusters target `{hotel} location` queries, but a blanket
"hotel pages noindex by default" policy means we never rank for them. City
pages alone (`where to stay in London`) are among the most competitive travel
queries and cannot carry a new domain.

**Resolution: a measured pilot cohort, not a blanket default.**

- Hotel pages remain noindex **by default**, BUT
- at Phase 4 launch we promote a **pilot cohort of 150–300 hotel pages**
  (≈ 12–25 per launch city) to indexable, selected by the gates in §4.
- The pilot cohort is the SEO experiment: it is how we learn whether
  hotel-name long-tail queries can send traffic to us at all.
- Expansion beyond the cohort is driven ONLY by measured results (§5), never
  by page-generation capacity. We still never auto-index 50,000 hotels.

Cohort selection priorities (within gate-passing hotels): mix of brand sizes
(big brands have crowded SERPs; independent/boutique hotels are the likelier
long-tail wins — weight toward them ~70/30), spread across cities, high
confidence, distinctive surroundings (a hotel where our data tells a story
beats a generic one).

**Readable Latin name required for pilot eligibility (Bloc D, 2026-09-12).**
The original source name is retained. Display `Latin (Original)` when a Latin
variant exists, and the original alone when no reliable variant exists.
Priority: original Latin name (diacritics preserved), Overture current
common/official Latin alternative (English first), then documented script-limited
romanization. Latin, Cyrillic, Greek, Hangul and kana-only Japanese may pass the
readability gate; any Han/kanji, Thai, Arabic, Hebrew or other unsupported letters
without a source Latin variant keep the original and remain nonindexable.
Mixed scripts fail if any letter needs an unsupported conversion. Romanization
is labelled, never presented as a verified official spelling or translation.

`names.present_name` supplies the recorded name-gate input. Missing name-gate
metadata fails closed in publication and the build. Name readability is only
one gate: it does NOT prove a hotel, reception, legal operation or fitness for
the cohort. A/B exclusions always inspect original identities; all type and
existing quality gates still apply. Existing canonical slugs remain byte-for-byte
unchanged: rendering changes never feed slug generation. POI why-facts follow
the same display policy; ambiguous same-name POI matches cannot borrow another
place's Latin alternative. See `reports/bloc-d-names.md` and ADR-020.

## 3. Page types

**Always potentially indexable:** `/`, `/hotel-location-checker`,
`/methodology`, `/about`, `/data-sources`, `/city/{city}`, and carefully
justified city-intent pages (`/city/london/quiet-areas-to-stay`, etc.) —
published only when the dataset supports meaningful analysis.

**Default noindex:** internal search, query-param URLs, arbitrary user
comparisons, low-confidence hotels, duplicate aliases, thin combinations,
automatic translations, filters, sort variants — and all hotel pages outside
the pilot cohort.

City pages are generated from aggregate data (score distributions, transit/
quiet/food/family/nightlife clusters, representative hotels, methodology +
update date). Never "the best neighborhood" without an explicit criterion;
prefer "highest-scoring areas for transit access in our dataset".

## 4. Hotel page indexability gates (all must pass)

1. confidence ≥ 80; 2. hotel identity highly reliable; 3. all critical score
dimensions present; 4. unique location facts present; 5. city baseline
available; 6. automated content QA passes; 7. demonstrated demand OR editorial
pilot selection; 8. no canonical duplicate; 9. meaningful comparison/context on
page; 10. user value independent of keyword targeting;
**11. (new) affiliate deep-link resolvable OR page consciously published
without CTA** — see `docs/affiliate-matching.md`; an indexable page that can
never monetize should be a deliberate choice, not an accident.
**12. (new, 2026-09-07) Latin-script name** — see §2 above; a cohort-
eligibility rule for the English-language launch, not a data-quality
exclusion — non-Latin-script hotels stay searchable and scored, just not
pilot-cohort-eligible.

## 5. Pilot cohort measurement (90 days from indexing)

Track per cohort page: indexed?, impressions, clicks, avg position, internal
checker usage, outbound CTR.

Decision rules at day 90:
- ≥ 20% of cohort pages have impressions and ≥ 5% have clicks →
  **expand cohort** by the same size, same selection logic.
- Impressions concentrated on independent hotels → rebalance selection.
- < 5% of cohort pages have any impressions → do NOT add pages. Diagnose in
  order: technical indexing, internal linking, domain trust, demand mismatch.
  If demand mismatch confirmed → execute the PIVOT path in
  `docs/validation.md §3` (city/area pages + product-led, or B2B).

## 6. Mechanics (unchanged from original, kept as rules)

- `page_publication` table governs status: draft / noindex / indexable /
  retired. Indexability is a recorded decision.
- One canonical hotel identity → one canonical URL; aliases, params, locales,
  search paths never create duplicate canonicals.
- Sitemap contains exactly the indexable set; split by type
  (`sitemap-static/cities/hotels.xml`); noindex URLs never included.
- Internal links mirror real navigation (city↔areas↔hotels↔methodology);
  no keyword-stuffed anchor repetition.
- Structured data: `Hotel`/`LodgingBusiness`/`Place`/`BreadcrumbList`/
  `WebSite`. Our environmental score is NOT a review — no review/rating markup.
- Localization: a locale is added only on evidence (impressions, revenue,
  ranking opportunity); dedicated locale URLs, reciprocal hreflang, full useful
  UI translated, never machine-translation page multiplication.
- Publication quality gate (weights: data confidence 25, unique computed info
  20, completeness 15, utility 15, canonical integrity 10, freshness 5,
  performance 5, structured metadata 5): ≥ 80 eligible, 60–79 noindex,
  < 60 unpublished. Eligibility never forces indexing.
- Retirement is normal: merge / noindex / redirect / retire pages with no
  unique value, confidence, demand, or engagement.
- SEO self-improvement loop: GSC weekly → clustering → opportunity rules →
  recommendation → **PR/report, never auto-publication** for structural
  changes. Improve existing pages before creating new ones.

### Accommodation-type gate (Bloc C, 2026-09-12)

Only an explicitly classified `hotel` can be considered for indexing, in
addition to every other gate and a recorded publication decision. Aparthotel,
serviced-apartment, whole-home, hostel, guesthouse-B&B and unknown stay searchable
with their English type label, but remain noindex. B&B is not admitted yet:
source taxonomy cannot prove staffed reception. OYO alone never decides type;
explicit OYO Home/whole-unit evidence does. Sonder/Domio unresolved properties
remain unknown. This descriptive field never changes scores or weights.
See ADR-019 and `reports/bloc-c-accommodation.md`. No flag is activated.
