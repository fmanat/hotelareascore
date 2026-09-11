# STATE.md — project state tracker

> Read this first every session, whichever agent you are (`CLAUDE.md` /
> `AGENTS.md`); update it whenever phase, decisions, or blockers change.
> Keep it under ~150 lines — this is a dashboard, not a journal. Move
> resolved history to `docs/adr/` or the dated report it already lives in;
> don't re-narrate it here.

## Mission de nuit 2026-09-12 — G → C → D → E ; arrêt obligatoire après E

A et B validés par contre-audit externe (instruction propriétaire).
**G préparé :** Wrangler 4.131.1, `make deploy` limité au projet existant
`staycontext`, build + SEO + noindex + contrôle de domaine avant envoi.
Tests de sécurité locaux ; aucune connexion OAuth ni publication tentée.
Procédure et incident Git déconnecté dans le [runbook](reports/phase-4-launch-runbook.md).
Production figée sur `77e49b3` selon le propriétaire ; commande à lancer par
lui après `wrangler login`. Aucun flag activé, aucun projet créé.
**G poussé `6a2af23`, CI verte (5 jobs). C livré dans le commit de ce bloc :**
33 779 entrées conservées : 24 452 hôtels, 266 aparthotels, 1 049 appartements
avec services, 950 logements entiers, 2 237 hostels, 3 298 guesthouses/B&B,
1 527 inconnus. Seul `hotel` passe le gate de type, sans activation.
OYO Home du propriétaire classé logement entier ; 14 Sonder/Domio inconnus
à vérifier. 2 412 candidats théoriques de récupération hors hôtels,
**zéro ré-ingestion**. [Rapport C](reports/bloc-c-accommodation.md).
446 tests passent (+ 1 xfail historique), garde de build testée, typecheck propre,
15 721 pages construites et assertions SEO conformes.
**À suivre : D, puis rapport E uniquement.** L'arrêt explicite demandé
à E interdit de commencer F cette nuit sans un nouveau GO.

### Décisions en attente du propriétaire

- Exécuter le login et le déploiement manuel G, puis vérifier la disparition
  effective des pages A/B en production.
- Examiner le rapport E avant toute implémentation d'ancrage et la reprise F.
- Phase 4 : identité légale complète, nouvelle cohorte vérifiée et revue,
  GSC et autorisation d'indexation restent à régler ; tous les flags restent OFF.

## Contexte A/B — tous deux acceptés par le propriétaire

**2026-09-11 — Bloc A accepted by the owner after external counter-audit:**
46 / 33,966 institutional exclusions, no verified tourist-hotel loss;
1,825 Home/House and 1,061 hostel names preserved at that checkpoint.
See [Bloc A report](reports/bloc-a-institutions.md), ADR-016.

**Bloc B implemented on explicit owner instruction (ADR-017):** full 12-city
scan **33,920 → 33,779**, **141 exclusions** (5 programme-name, 63 office-name,
73 umbrella-name matches). **26 uncertain identities quarantined**, not
claimed as confirmed non-hotels; **11 property aliases protected** with
external evidence. Physical ETL/search/card/reference purge; 38 static hotel
pages removed. Kept hotel/score/fact values unchanged; A audit preserved.
Guards at ingestion, validation, publication (also noindex), export and build;
quarantined IDs/slugs cannot return through renaming. See the complete
[Bloc B report](reports/bloc-b-brands.md) and JSON city/group/review log.

**Generic attribute signal quantified, NOT activated:** original contacts
retrieved for all 33,920 records; 24 have no non-empty contact, 91 share exact
coordinates with another identified same-group record, 158 have an address
country different from the nominal city. All 158 are MY in Singapore's
cross-border bbox — not proven bad addresses. OR = 273, AND = 0 before B;
OR = 269, AND = 0 after B. Incomplete streets and unknown groups reported
separately. No automatic exclusion on these proxies.

Local validation: **419 tests passed + 1 pre-existing expected failure**,
including 135 Bloc B tests; typecheck clean, full 15,721-page build and SEO
assertions passed. Full `make validate` (including remote taxonomy coverage) and dataset
integrity checks passed across all 12 cities.
Implementation commit `fbbc0c4` pushed; all five [CI jobs green](https://github.com/fmanat/hotelareascore/actions/runs/34651434836)
(including E2E).
**Historical checkpoint before the night mission: C–F were undone.** The old 200-entry proposal now
has 197 surviving identities after A+B; its old 214-URL go-live dry-run is
obsolete. Cohort reconstruction belongs to F. No indexing/scoring change.

**Production remains an owner-dashboard blocker:** requested live check at
21:04:20 UTC, repeated **21:14:34 UTC on 2026-09-11**: Singapore Boys' Home
still serves its scored page with **HTTP 200** after Bloc A commit `1d4e4ef`.
GitHub exposes no deployment record; this does not prove whether Cloudflare
started a build. Owner explicitly handles the dashboard. **Do not force a
Cloudflare trigger, retry or configuration change.** A green GitHub CI does
not establish production removal; old URL/search disappearance is unverified.

**Correction (2026-09-11, owner):** night mission #3 delivered **only**
Blocs G/H/I (golden-set expansion, technical debt, pre-launch readiness —
see below). At that checkpoint its own Blocs A-F had never been executed and were **not**
long-shipped work — an earlier session's STATE.md note claiming otherwise
was wrong and has been removed. The remaining blocs are the top priority for
whoever picks up next, **before** any of the "Idées non autorisées" list
further down. Do not confuse this A-F set with the *different* A-F set
from the project's very first overnight mission (commits `8806111`
through `6321f9e` — 12-city pages, security headers, SEO machinery,
pilot-cohort proposal, entity-QA hygiene, ops bots — that one really is
done and shipped).

**Findings (2026-09-11, owner's manual review, "pack v2"): 12 pilot-cohort
fiches inspected, 5 defective / 7 validated — 42% anomaly rate, all on
establishment *identity*, none on the scores themselves.**

- **A — Institutions non touristiques**: `"Singapore Boys' Home"` was in
  the pilot cohort — a juvenile detention center. Publishing a scored
  page for a children's penal institution would be a serious incident.
  Family to exclude from the whole dataset, not just the cohort: homes,
  foyers, detention/rehab centers, nursing homes (EHPAD), shelters. New
  specimen, not previously logged (distinct from the non-Latin-script
  institutions already in "Entity QA" below — this one has a fully
  English, hotel-plausible name, so the language-filter gap doesn't
  explain it).
- **B — Marques sans établissement**: `"ALL Accor"` was in the cohort —
  not a hotel, Accor group's loyalty program. Geolocated points under
  that name are marketing/SEO artifacts with no real establishment
  behind them. Distinct from the already-logged "brand-allowlist
  short-circuit" below (real sub-venues of a real hotel) — here the name
  passes every hotel-sounding filter; it's the *referent* that doesn't
  exist.
- **C — Type d'hébergement**: an OYO cohort entry is a fully
  self-serviced independent home — no reception, no on-site staff. Real
  accommodation, but not a hotel; the page would misrepresent the
  category. Caution: OYO also operates real hotels, so this can't be a
  brand-wide exclusion — same family of problem as the `lodging`
  hierarchy mix in `data/config/taxonomy-mapping.yml`, but needs a
  per-listing signal, not a brand rule.
- **D — Écritures non latines**: on an English-language site, all
  Claude-produced text must be English; Japanese and Thai text was
  showing in fiches. Proper nouns aren't translated but must render
  legibly → dual "Latin (Original)" display, e.g. "Hotel Coco (ホテルCOCO)".
  This is a presentation/i18n fix, distinct from bloc D's original
  framing as an `entity_qa.py` filter-recall issue (still true and still
  useful context, "Entity QA" below, but not what this finding is about).
- **E — Biais urbain / hôtels d'ancrage**: two cases now — `"Hilton
  Bangkok Suvarnabhumi Golf Resort & Spa"` (excellent hotel FOR GOLF,
  owner stayed there) and `"Sheraton East Rutherford NJ"` (adjacent to
  MetLife Stadium). Both score low everywhere because all 6 dimensions
  measure urban density, while these hotels have a FUNCTION. The scores
  are factually correct; the framing misleads. Rule: type changes
  presentation, never scores (`docs/adr/015`, decision (c) — this
  finding is the second confirming case, not a new decision).
- **F — Reconstruction cohorte + vérification externe (method
  conclusion, not a separate defect)**: 5/12 = 42% anomaly rate, 100% on
  identity, 0% on scores; the other 7 pass the 15-second test. Overture
  data alone is not sufficient to decide a point is a publishable hotel
  → a mandatory external-verification gate on the 200-hotel cohort,
  using these 5 cases as the test set. Sequenced after A-D land, not
  parallel.

## Session checkpoint (long-session discipline — overwritten hourly, not accumulated)

**Last updated:** 2026-09-11 19:49 UTC — SESSION CLOSED. ~57.8h elapsed
since mission start (22:05 UTC 2026-09-09), ~4.8x the stated ~12h window
(flagged 2026-09-10 14:41, 16:05, 2026-09-11 05:42). Watcher script hit
its 10h internal budget and exited ~19:41 UTC; asked the owner directly
whether to keep the fallback loop going. **Owner decision: stop here.**
**Bloc en cours:** none — G, H, I done since 22:40 (2026-09-09). Session
closed by owner instruction; that watcher remains stopped. Bloc A was
subsequently implemented on explicit owner instruction (see above).
**Poussé sur origin/main:** `7c0a586` (checkpoint 19h47) + this closing
commit. CI green on every commit this session (confirmed via `gh run
list`, run 34640632737 succeeded).
**Probe status:** `prod_probe_loop.sh` (PID 6593) stopped on owner
instruction at 19:49 UTC — last live read was 200 OK on both domains,
no incident at close. `probe.log` / `probe-summary.md` committed as the
final record; not appending further.
**Reste à faire:** night mission #3's own Blocs A-F, see the priority
section at the top of this file — **not** long-shipped, corrected
2026-09-11 (an earlier version of this note wrongly said otherwise).
After that: the "Idées non autorisées" section below and the "Depends on
the owner" list in `docs/reports/pre-launch-readiness.md`. Do not resume
the probe/checkpoint loop without a fresh explicit instruction.

## Current phase

**Phase 3 — launch dataset (~12 cities), golden set, calibration —
CLOSED 2026-09-07.** All 12 cities ingested/scored/validated on
`score_version` **1.2.1**. Final dimension status:
- Transit, restaurants, nightlife: pass (Spearman 0.77-0.83), frozen.
- Quietness and family_convenience: both closed as **documented
  thin-to-moderate proxies**, not robustly validated dimensions —
  `/methodology` and `docs/scoring.md §4.3` state this explicitly.
  family_convenience's last iteration (`docs/adr/009`): Spearman 0.5052
  against `tests/golden/family_strict.csv`, a 0.005 margin above the
  owner's 0.5 bar, with per-city Spearman still ranging −0.632 to +1.0
  (3-5 hotels/city). No further tuning without an explicit new review.

Golden-set labels are Claude-produced, not owner-verified
(`tests/golden/LABELS-PROVENANCE.md`) — read every calibration number with
that caveat. Phase 4 SEO-launch machinery (`docs/adr/008`) was built ahead
of time and stays fully inert (flags off) — see open decisions below.

## Phase gate status

| Phase | Gate | Status |
|---|---|---|
| 0 — repo & ADRs | ADR-001…005 merged, CI green | ✅ 2026-09-06 |
| 0bis — demand validation | Kill criteria evaluated, owner GO | ✅ GO 2026-09-06 |
| 1 — data proof (2 cities) | Data Proof Report accepted | ✅ 2026-09-06 |
| 2 — product proof | Owner inspected 15–20 hotel outputs | ✅ 2026-09-06 |
| 3 — launch dataset (~12 cities) | Golden set + calibration | ✅ **closed 2026-09-07** (`docs/adr/009`) |
| 4 — SEO launch (incl. pilot cohort) | Pilot cohort live, GSC connected | ▶ machinery ready (`docs/adr/008`), all flags OFF — blocked on decisions below |
| 5 — commercial test | First affiliate integrated, clicks measured | ☐ |
| 6 — growth automation | Weekly GSC loop producing PRs | ☐ |

## Open owner decisions (blocking Phase 4, nothing else)

- [ ] **(a) Legal placeholders on the 4 legal pages** (`/legal-notice`,
      `/privacy`, `/affiliate-disclosure`, `/terms`) — publisher is settled
      (FrenchSquare Ltd, `docs/adr/011`) but Companies House number,
      registered office address, contact email, "last updated" dates, and
      `/terms`'s governing-law line are still owner-provided placeholders,
      not technical work
- [ ] **(b) Pilot cohort review**: sanity-check a sample of the 200
      proposed hotels before any Phase 4 flag is turned on —
      [pilot-cohort-proposal.md](reports/pilot-cohort-proposal.md). A
      12-hotel inspection pack is ready to support this review — full
      published-page fiche, 11 gates, and selection reasoning per hotel,
      including 2 flagged as most discutable (a likely non-hotel
      institution, an ambiguous short-term-rental listing) —
      [cohort-inspection-12.json](reports/cohort-inspection-12.json). **Superseded 2026-09-11: the cohort requires the A–F identity fixes
      and a new review before go-live** —
      [go-live-seo-checklist.md](reports/go-live-seo-checklist.md) (night
      mission #2 Tache 3) is the exact 6-step sequence from here to the
      90-day clock starting. The package is staged (`page_publication`:
      home/methodology/12 cities/200-cohort all `draft`, re-run via
      `python3 scripts/compute_publication.py`) and dry-run verified —
      [go-live-sitemap-dry-run-report.md](reports/go-live-sitemap-dry-run-report.md):
      all 214 staged URLs resolved at that time; this is now obsolete
      after Bloc A removed 2 cohort entries.
- [ ] **(c) "Destination/resort" hotel type — review the detection
      feasibility report before any implementation** (not a go-live
      blocker, a separate decision track). Owner-framed
      (`docs/adr/015`): a hotel type changes presentation only, never
      scores. Detection tested (isolation + real Overture amenity
      adjacency) correctly catches the seed case but has a real
      false-positive rate on hand inspection (~1/3 of a sample) —
      [destination-type-detection-feasibility.md](reports/destination-type-detection-feasibility.md)
      recommends specific fixes before implementing, not shipping as
      tested. Also surfaced one new entity-QA specimen (a non-hotel
      company record) — noted below, not fixed.

Resolved this session, no longer open: family_convenience gate (closed,
`docs/adr/009`); New York/New Jersey market label (`docs/adr/010` — market
renamed "New York City metro", per-hotel disclosure unchanged); legal
vehicle (`docs/adr/011` — FrenchSquare Ltd, an existing English company;
the 4 DRAFT legal templates already name it as publisher/data controller).
Resolved this session (see below): brand & domain (`docs/adr/012` —
StayContext / staycontext.com, owned). Resolved night mission #2, Bloc A:
`web/src/lib/data.ts`'s 2-city hardcoding, and the 10-cities-with-no-built-
hotel-page bug it caused — all 12 cities now have real pages for every
indexable hotel, via a static-subset + client-rendered-long-tail
architecture (`docs/adr/013`, `docs/reports/hotel-pages-architecture-options.md`).
**Night mission #3, Tache 5 note:** the requested ops-bot skeletons
(monthly data-refresh, weekly health/cost) were already fully delivered
an earlier session (commit `6321f9e`, "Bloc F") — verified still correct
and re-ran `cost_bot.py` rather than duplicating the work. The one
documented gap (a per-release score diff step in the monthly workflow) is
still blocked on Supabase not being provisioned, unchanged from when that
gap was first written down.

## Entity QA — known limitations (not blockers, tracked for a future pass)

Full detail in `docs/reports/phase-3-batch-1-ingestion-report.md` and
`tests/golden/LABELS-PROVENANCE.md` §"Data-quality specimens". Summary:

- **Pilot-cohort v2 human review (2026-09-11, owner, 5 new specimens)**:
  see "NEXT SESSION — Blocs A-F" at the top of this file for full
  detail/rationale. `"Singapore Boys' Home"` (juvenile detention center),
  `"ALL Accor"` (loyalty program, no establishment), an OYO
  self-serviced-home entry (real accommodation, not a hotel), plus
  non-Latin-script display text found in fiches (i18n, not a filter
  gap) and a second anchoring case (`"Sheraton East Rutherford NJ"`,
  alongside the existing Hilton Bangkok Golf Resort case). The Singapore Boys’ Home case is now excluded by Bloc A (ADR-016).
  The other failure modes remain open; Bloc B awaits owner validation of A.
- **English-market-only name filter** (`entity_qa.py`): near-zero recall on
  CJK/Arabic/etc. non-hotel names. Original 2 specimens (Tokyo liquor shop
  + bathhouse), `xfail`-tested. **6 more found in the pilot-cohort v1 audit
  (2026-09-07)**, all non-Latin-script non-hotels: `a995410c…` an
  archaeological site, `dd23804b…` a sake shop, `7c60ea93…` a share house
  (all Tokyo); `02f2535f…` a boat pier, `c4ce64a3…` a housing estate,
  `6679c755…` a university residence complex (all Bangkok) — full names in
  `docs/reports/destination-name-mismatch-audit.md`. All 8 now excluded
  from pilot-cohort candidacy by gate 12 (Latin-script name,
  `docs/seo-policy.md §2`), but remain in the full dataset as "hotels" —
  gate 12 is a cohort-eligibility rule, not an entity-QA fix; the
  still-unattempted language-specific marker list is the real fix. **1
  more found (2026-09, destination-type detection feasibility pass)**:
  a Bangkok record named "บริษัทไฮเทคเอ็มบรอยเดอร์ จำกัด" ("Hi-Tech
  Embroidery Co., Ltd") — a company, not a hotel — same
  non-Latin-script-filter gap.
- **Brand-allowlist short-circuit**: ~33 hotel sub-venues (restaurant/spa/
  parking sharing a parent brand name) pass through across all 12 cities;
  one additional case (Souq Madinat Jumeirah) confirmed not caught because
  "Jumeirah" hits the allowlist first.
- **Corporate-entity records**: at least one (`Holiday Inn Paris CDG
  S.A.R.L.`, pin ~25 km from the airport at Porte de Charenton) looks like
  a legal-entity record, not a bookable property.
- **Numeric-name records — RESOLVED 2026-09-09 (`docs/adr/014`):** 9
  hotels with a purely-numeric `name` (Overture reference number, not a
  real name) — slug fix (`hotel-` prefix) plus a hard, structural
  indexability gate now enforced in `publication.set_status()` (raises
  rather than allowing `'indexable'`) and re-checked in `webdata.py`'s
  export as a second layer. No longer an open question.
- **Bad-geocode records — fixed, not just logged (2026-09-07 owner
  audit):** 4 real hotels whose own `address_freeform` contradicted their
  extraction city (a Bora Bora resort and a Fiji resort both in the
  "Sydney" extract; a Bali villa in "London"; a Bali hotel whose name and
  address disagreed, in "Singapore") — found via a systematic
  destination-name search, verified per-record before exclusion, not
  guessed from the name alone. Now excluded from their cities' datasets
  entirely via `entity_qa.KNOWN_BAD_GEOCODE`, re-ingested. Full triage
  (including same-pattern hits checked and NOT excluded — Tokyo's "Petit
  Bali" love-hotel naming convention, Lisbon's "Pensão Nova Goa", etc. —
  for insufficient evidence of an actual mismatch) in
  [destination-name-mismatch-audit.md](reports/destination-name-mismatch-audit.md).

## Phase 4 commitment: `search_events` as the coverage KPI

No automatic "rejected lodging" rescue rule will be built off blind
sampling (owner decision, 2026-09-06,
`docs/reports/phase-3-coverage-bangkok-nyc.md`). Once the live site is up,
`search_events` (searches with no matching hotel) becomes the per-city
coverage KPI; a rescue rule gets reconsidered only against real demand
data from that metric. Whoever picks up Phase 4: wire this in from the
start.

## Blockers / risks being watched

- **Cloudflare Pages platform incident (2026-09-09, ~08:00–09:00 UTC),
  their platform not us — recovered, stable since, still monitored**
  (background probe running, `docs/reports/incident-2026-09-09-cloudflare-pages/`
  has the raw log/summary; check `probe-summary.md` before assuming it's
  still fine, since it's described as intermittent). **Production
  Cloudflare Pages project is named `staycontext`** — `hotelareascorec` is
  an older, dead/unused project, don't delete it, don't confuse it for
  prod. Two header/404 anomalies noticed during the outage were confirmed
  transient (not real config bugs) once stable — full writeup:
  [tache3-anomaly-recheck.md](../reports/incident-2026-09-09-cloudflare-pages/tache3-anomaly-recheck.md).
  Still open, minor, unrelated to the incident: `https://www` doesn't
  redirect to the apex (no SEO risk, canonicals already handle it).
- **Data freshness (checked 2026-09-07):** `2026-08-19.0` is still
  Overture's latest release (live catalog check, not cached) — no
  re-ingestion needed. Re-check next time rather than assuming still true.
- **AI Overviews (unmeasured):** could not observe whether Google AI
  Overviews already answer cluster-2 queries. Mandatory AI-Overview column
  in the day-90 cohort measurement (`docs/seo-policy.md §5`); if AI
  Overviews cleanly answer most tracked queries → PIVOT path
  (`docs/validation.md §3`).
- No search-volume data (Phase 0bis was SERP-composition-only) — treat all
  traffic projections as unvalidated priors.
- Affiliate program eligibility likely requires a live site with traffic —
  sequencing in `docs/affiliate-matching.md §5`.
- Supabase free-tier fit depends on keeping POIs out of the serving DB —
  `docs/data-and-costs.md §2`.
- **Night mission #2, Bloc B was cut off mid-instruction** ("CSP en
  Report-Only d'abord av...") — implemented what was unambiguous
  (`web/public/_headers`: HSTS w/o `preload` — deliberately, that's a
  harder-to-reverse commitment than one truncated line should authorize —
  X-Content-Type-Options, Referrer-Policy, a minimal Permissions-Policy,
  and CSP in Report-Only mode with no `report-uri` since wiring one needs
  a new service). Whatever came after "av" in the original order is
  unknown — re-issue Bloc B in full if there was more to it.

## Idées non autorisées (2026-09-10) — pour décision propriétaire, rien lancé

Blocs G/H/I terminés et poussés (`e70c8df`), rien d'autre n'était
explicitement autorisé cette nuit. Voici ce que je ferais ensuite avec un
go-ahead, par ordre d'impact perçu — aucune de ces actions n'a été
commencée :

1. **Corriger les 2 findings a11y encore ouverts** (persona tablist sans
   modèle clavier flèche gauche/droite ; contraste de bordure
   `--border` vs `--bg`, jamais re-mesuré contre WCAG 1.4.11) —
   `docs/reports/pre-launch-readiness.md`. Petit, scopé, déjà identifié
   précisément (fichier + ligne).
2. **Affiner la détection destination/resort** selon les correctifs
   listés dans `docs/reports/destination-type-detection-feasibility.md`
   §6 (rayon par catégorie, vraie distance au polygone, seuil de
   surface), puis re-mesurer le taux de faux positifs sur un nouvel
   échantillon. Ne coderait PAS le type lui-même (présentation) sans
   nouvelle revue — juste la détection.
3. **Publier `tools/golden-labeler`** comme Artifact (capabilities `db` +
   `downloads`) pour que les 56 hôtels (dont les 6 nouveaux) soient
   labellisables dans un vrai outil, pas juste un JSON.
4. **Investiguer un fix `_redirects` pour www→apex** avant de supposer
   qu'il faut absolument passer par le dashboard Cloudflare — pas vérifié
   si un fichier `_redirects` dans le repo peut gérer une redirection
   cross-host sur Cloudflare Pages ; si oui, ça sort ce point de la liste
   "dépend du propriétaire".
5. **Prototyper le schéma D1/Analytics Engine** pour `search_events`/
   `outbound_clicks` (option (c) de `docs/reports/analytics-storage-options.md`)
   localement, sans le connecter — pour raccourcir la décision propriétaire
   à "oui/non" plutôt que "oui/non + comment".

## Cost tracker (update monthly)

| Month | Est. recurring € | Main driver | Notes |
|---|---:|---|---|
| 2026-09 | 0 | - | 33,920 hotels after Bloc A, all free tiers |

## Decision & session history

Full narrative history lives in `docs/adr/001` through `016` (each records
context/decision/consequences) and the dated reports under `docs/reports/`
they reference. Batch ingestion, golden-set construction, and calibration
runs are documented in `docs/reports/phase-3-*` and
`docs/reports/score-diff-*`. This file tracks only current state — see git
log and the ADR index for anything not summarized above.
