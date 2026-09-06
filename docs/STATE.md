# STATE.md — project state tracker

> Claude Code: read this first every session; update it whenever phase,
> decisions, or blockers change. Keep it under ~150 lines — this is a
> dashboard, not a journal. Move resolved history to `docs/adr/` or delete it.

## Current phase

**Phase 3 — launch dataset (~12 cities), golden set, calibration** (see
`docs/strategy.md §5`), **gate still open**; Phase 4 SEO-launch machinery
has now been built ahead of time but stays fully inert (flags off) until
Phase 3 actually closes. See the overnight-mission summary at the bottom
of this file (2026-09-07) for the full picture — condensed here:

**PHASE 3 GATE: NOT CLOSED.** Owner's own closing condition: "la Phase 3 se
clôt quand famille passe." All 12 cities ingested/scored/validated on
**score_version 1.2.0**. Status per dimension (full detail:
[phase-3-calibration-sensitivity-report.md](reports/phase-3-calibration-sensitivity-report.md),
[family-v1.2.0-recalibration.md](reports/family-v1.2.0-recalibration.md)):
- Transit, restaurants, nightlife: **pass** (Spearman 0.77-0.83). Every
  constant sensitivity-tested and stable — frozen, no further tuning.
- Quietness: kept as-is, documented as a moderate-correlation **proxy** —
  owner-accepted limitation, not a blocker.
- **family_convenience: still fails after two fix attempts.** v2
  (`docs/adr/006`, land_use polygons) fixed the wrong-signed correlation;
  v1.2.0 (`docs/adr/007`, expanded green classes + a fresh strict
  re-labeling `tests/golden/family_strict.csv`) still landed at Spearman
  **0.209**, below the owner's pre-authorized 0.5 threshold. Per that same
  instruction, stopped — no further tuning without another explicit review.
  **This is the one thing blocking Phase 3 closure.**

Golden-set labels are Claude-produced, not owner (`tests/golden/
LABELS-PROVENANCE.md`) — weaker evidence, read every number above with
that caveat.

Phase 2 gate: ✅ closed 2026-09-06. Phase 1 Data Proof Report: accepted
2026-09-06 ([report](reports/data-proof-report-2026-08-19.0.md)).

## Phase gate status

| Phase | Gate | Status |
|---|---|---|
| 0 — repo & ADRs | ADR-001…005 merged, CI green | ✅ committed & pushed 2026-09-06 (github.com/fmanat/hotelareascore) |
| 0bis — demand validation | Kill criteria evaluated, owner GO recorded | ✅ **GO recorded 2026-09-06** (see decision log below) |
| 1 — data proof (2 cities) | Data Proof Report accepted by owner | ✅ **accepted 2026-09-06** |
| 2 — product proof | Owner inspected 15–20 hotel outputs | ✅ **closed 2026-09-06** |
| 3 — launch dataset (~12 cities) | Golden set built, calibration done | ▶ current — NOT closed: family_convenience fails Spearman ≥ 0.5 (0.209) after 2 fix rounds; owner decision pending |
| 4 — SEO launch (incl. pilot hotel cohort) | Pilot cohort live, GSC connected | ▶ **machinery built overnight 2026-09-07, all inert (flags OFF)** — page_publication, sitemaps, robots.txt, canonicals, JSON-LD, city pages, CI SEO assertions, 200-hotel pilot cohort proposal. Nothing launched; owner decision to actually flip a flag is separate from this being ready. |
| 5 — commercial test | First affiliate integrated, clicks measured | ☐ |
| 6 — growth automation | Weekly GSC loop producing PRs | ☐ |

## Open owner decisions

- [ ] Domain/brand name (blocking public launch, not blocking Phases 1–2) —
      also now blocks giving `web/src/lib/site.ts`'s `SITE_URL` a real value
      (currently the RFC 2606 placeholder `example.invalid`)
- [ ] Legal vehicle & jurisdiction for the site and affiliate revenue
      (`docs/strategy.md §8` — owner homework)
- [ ] **Phase 3 closure**: accept family_convenience as a disclosed
      limitation (like quietness) and close the gate, or commission a
      genuinely independent re-labeling pass first — see
      [family-v1.2.0-recalibration.md](reports/family-v1.2.0-recalibration.md)
- [ ] **NYC bbox/positioning**: polygon-based extraction (data fix) vs. a
      "NYC metro" market label (positioning decision) for the 351 New
      Jersey hotels currently inside the "New York" dataset — see
      [nyc-bbox-options.md](reports/nyc-bbox-options.md)
- [ ] **Pilot cohort review**: sanity-check a sample of the 200 proposed
      hotels before any Phase 4 flag is turned on — see
      [pilot-cohort-proposal.md](reports/pilot-cohort-proposal.md)
- [ ] **4 legal pages** (`/legal-notice`, `/privacy`, `/affiliate-disclosure`,
      `/terms`) are owner-provided templates, drafted onto the site with
      every `[bracket]` placeholder still open — need real review, not just
      technical integration (already done, noindex, DRAFT-banner marked)

## Entity QA — done this session (items a-d)

All 4 items from the bounded pre-Phase-3 task are implemented and live in
Batch 1's data (full detail: `docs/reports/phase-3-batch-1-ingestion-report.md`):

- **(a)** `src/hotelareascore/entity_qa.py` — name-pattern non-hotel
  exclusion, wired into `ingest.py`. Took 3 iterations against real Batch 1
  data (see module docstring for the false-positive history — "tower"/
  "design" markers wrongly excluded real hotels, up to 3.3% of Dubai's
  candidates, before removal). **Known limitation: effectively English-market
  only** — near-zero recall on French/Italian/Japanese/Arabic business
  names. Every exclusion logged in full per city (`manifest.json`).
- **(b)** `validate.py` flags purely-numeric and empty hotel names
  (`n_numeric_name`).
- **(c)** Every hotel now carries `distance_from_center_km` +
  `far_from_center` (>15 km, `webdata.py`); result pages show an honest
  disclosure instead of implying "in London" etc. Batch 1 bboxes also
  deliberately tightened (`cities.yml`). London itself: 928 hotels (20.8%)
  are >15 km from center — not re-ingested (Phase 2 closed), but now
  disclosed.
- **(d)** `nearby_facts_display_exclude` in `taxonomy-mapping.yml` — pet
  services, personal coaching, delivery services no longer clutter the
  "Why?" section; walkability_density's SCORE predicate is unchanged.

**Blind-labeling rule** added to `docs/scoring.md §4.1` per owner
instruction: the labeling tool never shows our scores/verdict/reason codes.

## Entity QA backlog — not started (5 specimens, from golden-set labeling)

Found while Claude labeled the golden set (`tests/golden/LABELS-PROVENANCE.md`
§"Data-quality specimens"), left IN the calibration (labels judge the pin,
per the tool's own rule) but each needs a real fix before any indexable
cohort:

- **`2bf89f8c…` 桝本屋酒店 (Tokyo)** — almost certainly a **liquor shop**, not
  a hotel (酒店 = "sake shop" in Japanese, "hotel" only in Chinese). Textbook
  case of the documented English-only limitation (item a above): the current
  heuristic has no CJK vocabulary at all, so this is a false *inclusion* the
  existing exclusion logic structurally cannot see. Any CJK-market fix needs
  its own language-specific marker list, not a patch to the English one.
  **Documented as an honest `xfail` test** (overnight Bloc E,
  `test_known_limitation_cjk_liquor_shop_not_caught`) so this stays visible
  in CI rather than silently unaddressed — a full CJK-market marker list is
  still not attempted, deliberately (guessing at non-English markers
  without native judgment risks new false exclusions).
- **`346a49c0…` アクアプレイス旭湯 (Tokyo)** — looks like a **bathhouse/sento**
  (旭湯), possibly with lodging attached. Same CJK-blind-spot family as above;
  verify on the ground before it enters any indexable cohort.
- **`a9b48284…` Souq Madinat Jumeirah (Dubai)** — a souk/venue, not a hotel.
  **"souq" added as a marker (overnight Bloc E)**, checked against every hit
  across all 12 cities first ("Maison Souquet," a real Paris hotel, does not
  collide; "souk"/"bazaar"/"mall" were checked too and deliberately NOT
  added — each has a real, currently-included hotel using the word as a
  theme name with no guardable collision pattern, see `entity_qa.py`'s
  comment). **This specimen still isn't caught in practice**: "Jumeirah"
  hits the brand allowlist first and short-circuits before the new marker
  is even checked — the pre-existing brand-shortcut limitation (item a
  above, 33 other records) claiming one more concrete instance. Not fixed
  tonight, same reasoning as the existing 33.
- **`b2a1e3f4…` "Holiday Inn Paris Charles de Gaulle S.A.R.L." (Paris)** — a
  corporate-entity record; the name says CDG airport, the pin is at Porte de
  Charenton (SE Paris, ~25 km away). Looks like a legal-entity/HQ record
  Overture attached hotel-adjacent taxonomy to, not a bookable property.
- **`756a9130…` SpringHill Suites (New York)** — pin is in Carlstadt, New
  Jersey, inside the "New York" bbox (5-borough box is wide enough to catch
  nearby NJ). **Fixed at the disclosure layer** (locality-consistency check,
  earlier this session) — but the real scale turned out much bigger than
  this one example: **351/2,194 "New York" hotels (16%) are actually in New
  Jersey.** A bbox fix turns out to be geometrically impossible (Staten
  Island and the New Jersey cities in this dataset occupy the same
  longitude band — a rectangle can't separate them without also cutting
  real Staten Island hotels). Full options report, no action taken:
  [nyc-bbox-options.md](reports/nyc-bbox-options.md) — recommends
  polygon-based extraction (a real ETL change) or a "NYC metro" market
  label (a positioning decision) as the two live options, owner's call.

## Batch 2 (New York, Singapore) — DONE 2026-09-06

Owner green-lit Batch 2 off the coverage report's recommendation. Ingested,
scored, validated (bboxes tightened per the Batch 1 lesson —
`data/config/cities.yml`) —
[ingestion report](reports/phase-3-batch-2-ingestion-report.md). **All 12
Phase 3 launch cities are now ingested; cumulative volumetry (~131 MB) landed
within 0.5% of the plan's ~130 MB estimate.** A 4th entity-QA false-positive
class surfaced and was fixed (see next section). Golden-set wave 2 (8
New York/Singapore hotels, `tests/golden/selection.json`) added and the
labeling tool republished — **owner's wave-1 labels confirmed preserved**
(verified via `read_db` before/after: `state/order` unchanged, still 42
ids, until the next page load merges in the new 8 automatically).

## Phase 4 commitment: `search_events` as the coverage KPI (owner decision, 2026-09-06)

No automatic "rejected lodging" rescue rule will be built off blind sampling
(Bangkok's 58% noise rate makes that too risky — `docs/reports/phase-3-coverage-bangkok-nyc.md`).
**In exchange:** once the live site is up (Phase 4), `search_events`
(searches with no matching hotel) becomes the per-city coverage KPI. If it
shows real user demand concentrated on specific missing hotels, the rescue
rule gets reconsidered against that actual-demand data — not another
sampling pass. Whoever picks up Phase 4 SEO-launch work: wire this metric
in from the start, it's a decision input, not an afterthought.

## Decisions taken (pointers, not prose)

- 2026-09-06 — **Phase 0bis GO** (owner: Jean; `rapport-decision-phase-0bis.md`);
  ADR-001…005 drafted; Phase 1 pipeline built and run (4,463 London + 7,558
  Bangkok hotels, €0 cost) — **report accepted**; Phase 2 Astro site built
  (`web/`, static-first). **Owner code audit** then found and fixed a real
  `transit_access` bug (DuckDB `least()` swallowing NULL, scoring 100
  instead of 0 — `score_version` → `1.0.1`, 414/1,960 hotels moved exactly
  −20 pts, [diff report](reports/score-diff-1.0.0-proof-to-1.0.1.md)) plus a
  self-contradictory-verdict bug and a scoring.md doc/code drift — **Phase 2
  gate closed**. Phase 3 plan researched (10 candidates, no ingestion) and
  presented ([plan](reports/phase-3-plan.md)).
- 2026-09-06 — **Owner approved the Phase 3 plan** with 3 amendments
  (2-batch ingestion, 2-wave golden set, blind/mobile-first tool). Entity QA
  (a)-(d) implemented (see section above). Batch 1 (8 cities) ingested,
  scored, validated — [ingestion report](reports/phase-3-batch-1-ingestion-report.md).
  Golden-set tool built (`db` capability, blind, mobile-first, keyboard
  shortcuts, shuffled order, "can't judge" skip) and published with 42
  Batch-1 candidates loaded, stratified by score/confidence/chain-vs-
  independent plus 2 deliberate calm-vs-nightlife tension cases (Tokyo). Not
  yet reviewed by owner.
- 2026-09-06 — **Owner audit round 2** (before labeling starts): (1) tool
  export + source committed — CSV export (`downloads` capability, copy-paste
  fallback), `tools/golden-labeler/` source + `tests/golden/selection.json`
  committed and versioned, Artifact republished with `db`+`downloads`. (2)
  Coverage check (the real Batch 2 precondition, not the entity-QA fix) —
  hand-classified 100 rejected-lodging records (50 Bangkok + 50 New York):
  ~10-16% look like real miscategorized lodging, ~46-58% genuine noise
  (public housing, real-estate agencies, street-address artifacts), rest
  ambiguous. Recommendation: Batch 2 OK to proceed as-is; a rescue rule is a
  scoped follow-up, not a blocker. (3) Logged (not fixed): brand-allowlist
  short-circuit lets 33 hotel sub-venues (restaurant/spa/bar/parking/
  ballroom sharing a parent brand name, e.g. "Royal Princess Dusit
  Restaurant") through across the 10 ingested cities.
- 2026-09-06 — **Owner green-lit Batch 2** off the coverage report. New
  York + Singapore ingested/scored/validated (tightened bboxes) —
  [report](reports/phase-3-batch-2-ingestion-report.md); **all 12 cities
  done**, cumulative volumetry ~131 MB (within 0.5% of the ~130 MB
  estimate). Found and fixed a 4th entity-QA bug in the process: "union"/
  "mosque"/"bank"/"church"/"temple" collided with real street/square names
  ("W New York – Union Square", "Wink @ Mosque Street") — now guarded
  against a following street-type word, "union" dropped outright. Owner
  decision: no automated "rejected lodging" rescue rule now; `search_events`
  becomes the Phase 4 coverage KPI instead (see section above). Golden-set
  wave 2 (8 hotels) added, tool republished with wave-1 labels confirmed
  intact (verified via `read_db`).
- ~~`web/` is NOT wired into CI~~ **Resolved, overnight mission Bloc B/C
  (2026-09-07):** `web/` now has 3 real CI jobs (`typecheck`, `e2e`,
  `seo-assertions`), all running against a small deterministic fixture
  dataset (`web/e2e-fixtures/`) instead of the gitignored, network-fetched
  ETL output — solves exactly the reproducibility problem this note used to
  flag. The previous `typecheck` job had also been a silent no-op since
  Phase 2 (checked for `package.json` at the repo root, which doesn't
  exist — it's in `web/`); fixed in the same pass.

## Blockers / risks being watched

- **AI Overviews (unmeasured):** validation could not observe whether Google
  AI Overviews already answer cluster-2 queries. Mitigation: owner spot-check
  when convenient; mandatory AI-Overview column in the day-90 cohort
  measurement (`docs/seo-policy.md §5`). If AI Overviews cleanly answer the
  majority of tracked cluster-2 queries → execute PIVOT path
  (`docs/validation.md §3`).
- No search-volume data was available in Phase 0bis (SERP composition only);
  treat all traffic projections as unvalidated priors.
- Affiliate program eligibility likely requires a live site with traffic —
  sequencing in `docs/affiliate-matching.md §5`.
- Supabase free-tier fit depends on keeping POIs out of the serving DB —
  `docs/data-and-costs.md §2`.

## Cost tracker (update monthly)

| Month | Est. recurring € | Main driver | Notes |
|---|---:|---|---|
| 2026-09 | 0 | - | 33,970 hotels, 185 MB ETL output, all free tiers |

## Last session summary

- 2026-09-06 — Phase 0bis → Phase 1 → Phase 2 (owner audit fixed a real
  scoring bug, `score_version 1.0.1`) → **gate closed**. Phase 3 plan
  approved with 3 amendments. Entity QA (a)-(d) implemented (3 iterations to
  get item (a) safe). Batch 1 (8 cities) ingested/scored/validated — real
  volumetry within 6% of estimate. Golden-set tool built.
- Same day, before labeling started: **owner audit round 2** required (1)
  CSV export + committed tool source (`tools/golden-labeler/`,
  `tests/golden/selection.json`) before any labels could safely leave the
  Artifact, and (2) a coverage check on Bangkok/New York's rejected-lodging
  buckets as the *real* Batch 2 precondition (not the entity-QA fix, which
  only cleans the included set). Both done: tool republished with
  `db`+`downloads`, [coverage report](reports/phase-3-coverage-bangkok-nyc.md)
  recommends Batch 2 is OK to proceed as-is. Also logged: the brand-allowlist
  short-circuit lets ~33 hotel sub-venues through (not fixed).
- Same day: **owner green-lit Batch 2**. New York + Singapore ingested,
  scored, validated (tightened bboxes) — **all 12 launch cities now done**,
  cumulative volumetry ~131 MB (within 0.5% of the ~130 MB estimate). Found
  and fixed a 4th entity-QA bug along the way ("union"/"mosque"/"bank"/
  "church"/"temple" colliding with real street/square names — see
  `entity_qa.py` and the Batch 2 report). Owner decision: no automated
  rescue rule for rejected-lodging now; `search_events` becomes the Phase 4
  coverage KPI instead. Golden-set wave 2 (8 hotels) added to the 50-hotel
  selection; tool republished with wave-1 labels verified intact via
  `read_db` before and after. **Owner is labeling now.** Next: collect the
  50 labels when ready (export, or `read_db` next session), run the
  sensitivity analysis (`docs/scoring.md §4.3`), freeze `score_version`.
- Same day: owner declined the labeling task partway through and asked
  Claude to label the 50 hotels instead, from world knowledge
  (`tests/golden/LABELS-PROVENANCE.md`, committed with the CSV) —
  `docs/scoring.md`/`ADR-004`/`/methodology` corrected to state that real
  provenance and never imply human/owner validation. Ran §4.2 calibration
  (3 required variants + a 4th composite-quietness-label variant requested
  as a follow-up) and the full §4.3 sensitivity sweep (decay scales, hybrid
  weight, quietness penalties, nightlife nearest-vs-density variant, persona
  weights ±10pt): **everything stable, nothing load-bearing.** Investigated
  the one real anomaly (`family_convenience` wrong-signed vs its label) down
  to a root cause: the formula only reads Overture's point `places` theme,
  never the polygon `base/land_use` theme also present in the same release —
  confirmed 9/11 zero-scoring golden-set hotels have a real nearby park/
  playground polygon the pipeline can't see. Logged the 5 entity-QA
  specimens found while labeling to the backlog (2 independently verified:
  "souq" is absent from `entity_qa.py`'s markers; the Carlstadt-NJ
  SpringHill Suites pin is 13.6 km from the New York center, under the
  15 km disclosure threshold). **Full report and recommendation:
  [phase-3-calibration-sensitivity-report.md](reports/phase-3-calibration-sensitivity-report.md)
  — freeze v1.0.1 as-is, no version bump. No constant was changed; owner
  review is next**, per explicit instruction not to touch
  `score-weights.yml` before this report was seen.
- Same day: **owner accepted the v1.0.1 freeze and approved the
  family_convenience v2 fix** the report identified (docs/adr/006):
  ingested Overture's `base/land_use` polygon theme (new fail-closed schema
  check, same treatment as `places`/`transportation`); family_convenience
  is now its own scoring function, boundary-distance to park/playground
  polygons + point distance for zoo/aquarium, same constants reused
  unchanged. `score_version` → **1.1.0**, all 12 cities re-ingested,
  re-scored, re-validated (all pass), zero big movers in the diff
  ([score-diff-1.0.1-to-1.1.0.md](reports/score-diff-1.0.1-to-1.1.0.md)).
  Re-calibrated against the same 50 labels: **sign fixed (−0.22/−0.33 →
  +0.06/+0.10) but still short of the 0.6 target** — per the owner's own
  instruction, stopped here, no further tuning, reported back (report §6).
  Also shipped this round: quietness limitation line on `/methodology`
  (kept as-is per owner decision); `tests/golden/joined-scores-1.0.1.csv` +
  `-1.1.0.csv` committed for audit/replay; a locality-consistency
  disclosure independent of the km threshold, which surfaced a bigger
  problem than expected (351/2,194 "New York" hotels are actually in New
  Jersey, 188 previously undisclosed) — all now disclosed, bbox tightening
  itself deferred as a separate decision. **Phase 3 gate stays open**;
  owner decision pending on family_convenience (accept as a disclosed
  limitation vs. commission re-labeling).

- **2026-09-07 — Ordre de mission de nuit (propriétaire absent), 6 blocs
  exécutés en autonomie, 6 commits poussés, CI verte à chaque étape.**

  **Bloc A — Famille v1.2.0 (priorité absolue) : ÉCHEC, comme prévu par la
  règle pré-autorisée.** Diagnostic sur 5 hôtels nommés : confirmé à la
  fois des trous de filtre réels (pelouses gérées, terrains de sport
  ignorés) et des cas d'absence réelle de verdure (pas de fix possible).
  Filtre étendu (`docs/adr/007`, vérifié contre un extrait Overture réel —
  jamais deviné), 2ᵉ thème Overture ingéré (`base/land`), 12 villes
  ré-ingérées/re-scorées/validées en `score_version` 1.2.0. Recalibré
  contre `tests/golden/family_strict.csv` (fourni par vous) : **Spearman
  0,209, sous le seuil de 0,5** — arrêt immédiat, aucun réglage
  supplémentaire, comme demandé. Fait notable : le même filtre étendu AIDE
  le label original (0,095→0,239) mais PAS le label strict — les deux
  labels mesurent des choses différentes. Rapport complet :
  [family-v1.2.0-recalibration.md](reports/family-v1.2.0-recalibration.md).
  **La Phase 3 reste ouverte** — c'est la seule chose qui bloque sa
  clôture.

  **Bloc B — Page Compare (dette Phase 2) : FAIT.** `/compare`, 2 hôtels
  côte à côte, sélection depuis la page résultat (lien direct + recherche),
  mobile d'abord, noindex, zéro appel externe. Première vraie
  infrastructure E2E du projet (Playwright, données de test déterministes,
  10 tests, desktop + mobile) — a aussi révélé que le job CI "typecheck"
  était un no-op silencieux depuis la Phase 2 (mauvais chemin), corrigé.

  **Bloc C — Machinerie SEO Phase 4 : FAITE, entièrement inerte.**
  `page_publication` opérationnelle (SQLite local + migration Postgres
  pour plus tard), sitemaps/robots.txt/canonicals/JSON-LD (jamais de
  markup review/note), assertions SEO en CI (titres uniques sur
  l'ensemble indexable, un seul canonical, sitemap exact, JSON-LD valide),
  gabarit de page ville (12 générées, toutes noindex), 4 pages légales
  intégrées avec bandeau "DRAFT" visible et placeholders intacts — **non
  relues par vous**. `robots.txt` est le vrai interrupteur : tout est
  bloqué tant que `PUBLIC_INDEXING_ENABLED` reste OFF. Bug réel trouvé et
  corrigé au passage : `validate.py` écrivait l'id de release Overture à
  la place du `score_version` dans chaque baseline ville depuis le début.
  Détail : [ADR-008](adr/008-page-publication-and-seo-machinery.md).

  **Bloc D — Cohorte pilote : FAIT.** 200 hôtels proposés (6 des 11 portes
  de `seo-policy.md §4` réellement vérifiées par hôtel, les autres
  structurellement acquises à ce stade — détaillé dans le rapport), ~70/30
  indépendant/chaîne, répartis sur les 12 villes. Aucun changement de
  `page_publication` fait à ce stade — juste la proposition. Point
  d'attention signalé : le critère de "distinctivité" n'est pas orienté
  (un score anormalement BAS compte autant qu'un anormalement HAUT).
  [pilot-cohort-proposal.md](reports/pilot-cohort-proposal.md).

  **Bloc E — Hygiène backlog : FAIT.** Marqueur "souq" ajouté (vérifié
  contre les 12 villes ; "souk"/"bazaar"/"mall" délibérément écartés —
  vrais hôtels réels qui collisionnent). Limitation CJK documentée avec
  test `xfail` honnête (桝本屋酒店). Rapport bbox NYC : resserrer la bbox
  est **géométriquement impossible** (Staten Island et le New Jersey
  occupent la même bande de longitude) — 2 options réelles présentées,
  aucune tranchée. Correctif de slug pour les 9 hôtels à nom purement
  numérique (appliqué, sûr, testé).

  **Bloc F — Bots d'exploitation : FAIT, squelettes inertes.** 2 workflows
  GitHub Actions (`data-refresh-monthly`, `ops-weekly`), tous deux
  `workflow_dispatch` uniquement — aucun cron actif dans aucun fichier.
  Bot de coût : mesure des proxys locaux réels (pas d'API de facturation
  branchée), coût actuel honnête = 0€, alerte prête pour quand ce sera
  réel.

  Aucun flag activé, aucune page rendue indexable en pratique, aucune
  dépense, aucun compte tiers créé, aucune décision de marque/domaine/
  légal/commercial prise à ma place. Liste complète des décisions qui vous
  attendent : voir "Open owner decisions" en haut de ce fichier.
