# Phase 4 launch runbook

> Ordered checklist from "brand/domain decided" (`docs/adr/012`) to a live,
> indexed pilot cohort. Report only when written — every step below still
> respects CLAUDE.md §8 (flags default OFF, flip deliberately) and §2 rule
> 2 (indexability is a recorded decision, never a side effect).
>
> **Status update, 2026-09-09 (night mission #3):** B1/B2 below are done —
> the site is deployed and `staycontext.com` is attached. **The production
> Cloudflare Pages project is named `staycontext`** (an older project,
> `hotelareascorec`, is dead/unused — don't confuse it for prod, and don't
> delete it either). Currently affected by a Cloudflare Pages platform
> incident (their side, intermittent, since ~08:00 UTC 2026-09-09) —
> `docs/STATE.md` "Blockers" and `docs/reports/incident-2026-09-09-cloudflare-pages/`
> have the live detail. Still noindex/all-flags-off throughout, per every
> guardrail below — the incident doesn't change that.

## How to read this

Two lanes:
- **Part A — owner-only steps.** Account creation, payment, DNS, and
  content only the owner can authorize or knows the real values for
  (CLAUDE.md's action-permission rules also mean Claude should not attempt
  these even with access — account creation and anything requiring a
  password are explicitly owner actions).
- **Part B — what Claude does next**, once the matching Part A item is
  done, in the exact order that keeps blast radius smallest at every step.

Each Part A item lists **what to hand back to Claude** so the next session
can pick up without a round-trip.

## Part A — owner steps

### A1. Cloudflare account
**What:** Create a Cloudflare account (or confirm an existing one this
project should use) and enable Cloudflare Pages. Free tier is sufficient
at this traffic level (`docs/data-and-costs.md`).
**Est. duration:** 10 min if new, 0 if reusing an existing account.
**Hand back:** Confirmation the account exists, and whether Claude should
get a scoped API token to drive deploys from CI, or whether the owner
prefers to connect the GitHub repo to Cloudflare Pages manually via the
dashboard (simpler, no token to manage — recommended for a project this
size).

### A2. DNS for staycontext.com
**What:** Point the domain at Cloudflare — either move nameservers to
Cloudflare (simplest, gives Cloudflare full DNS control) or, if the
registrar/DNS must stay elsewhere, add the CNAME/A records Cloudflare
Pages' custom-domain setup will specify.
**Est. duration:** 15-30 min active work; DNS propagation up to 24-48h
(often much faster, but don't assume it for a single deploy window).
**Hand back:** Confirmation DNS is pointed and (roughly) when it
propagated, or a note if the registrar setup is unusual and needs a
different record layout than the Cloudflare default.

### A3. Legal placeholders
**What:** Fill in the real values in the 4 DRAFT legal pages
(`web/src/pages/legal-notice.md`, `privacy.md`, `terms.md`,
`affiliate-disclosure.md`): Companies House number, registered office
address, contact email, "last updated" dates, and confirm the
governing-law line in `terms.md` (currently "[England and Wales / France —
to confirm]" — FrenchSquare Ltd being an English company makes "England
and Wales" the likely answer, but this is a legal choice, not inferred
here). Optional but recommended: one-off advisor check on the GDPR
EU-representative flag already noted in `privacy.md`'s HTML comment.
**Est. duration:** 30-60 min to fill in known values; open-ended if an
advisor review is wanted first.
**Hand back:** Either edit the 4 files directly and say so, or paste the
values in chat; either way, explicit confirmation to remove the DRAFT
banner and flip these 4 pages' `indexable` flag (per-page, independent of
the pilot cohort).

### A4. Pilot cohort review
**What:** Review the 12-hotel inspection pack (`docs/reports/
cohort-inspection-12.json`, this session's task 2) and/or spot-check
further into the full 200-hotel list (`docs/reports/
pilot-cohort-proposal.csv`). Confirm no hotel should be pulled before
`compute_publication.py` marks them indexable.
**Est. duration:** 30-45 min for the 12-sample pack; longer if
spot-checking beyond it.
**Hand back:** Go/no-go, plus any specific hotel_ids to exclude from the
cohort (the CSV is the input `compute_publication.py` reads — an
exclusion is a one-line CSV edit, not a code change).

### A5. Supabase (later — not this launch)
**What:** Create a Supabase project once traffic or a serving-DB need
(personalization, search-events storage beyond static JSON) actually
exists — `docs/adr/002` deliberately deferred this past the static-site
launch.
**Est. duration:** ~20 min.
**Hand back:** Project URL and anon key only. **Never** paste the
service-role key into chat — that goes directly into the Cloudflare/GitHub
secret store (CLAUDE.md hard rule 8).

## Part B — what Claude does next, in order

### B1. Deploy the current build to Cloudflare Pages (no custom domain yet)
**Prerequisite:** A1.
**What:** Connect the repo to a Pages project, deploy the current build
exactly as it is today — every flag OFF, every page `noindex, nofollow`,
`SITE_URL` already `https://staycontext.com` (`docs/adr/012`) even though
nothing is attached to that domain yet. Build settings: root directory
`web`, build command `npm run build`, output directory `dist`, env var
`NODE_VERSION=22`. Verify on the `*.pages.dev` preview URL: robots.txt
still disallows everything, spot-check a few page types render correctly.
**Guardrail:** this step makes the *build* live at a Cloudflare-assigned
URL, not at staycontext.com — no real-world visibility change yet, no
confirmation needed beyond the standard build/typecheck/e2e/seo-assertions
gates already in CI.
**Data dependency (found the hard way on the first deploy attempt,
2026-09-07):** Cloudflare's checkout has no `data/etl/` (gitignored,
`docs/adr/002`), so `web/src/data/*.json` + `web/public/data/
search-index.json` must already be committed — they're the frozen
snapshot exception in `web/.gitignore`, see `web/README.md`'s "Committed
artifacts" section. `npm run build`'s `prebuild` hook
(`web/scripts/check-data-exports.mjs`) fails fast with an explicit
message if one is missing, rather than a bare bundler `UNRESOLVED_IMPORT`.
Re-freshing that snapshot (new score_version, new hotels) is a manual
`python3 -m hotelareascore.cli webdata --city london,bangkok` + commit +
push, same as any other source change — Cloudflare does not regenerate it.

### B2. Attach staycontext.com as the custom domain
**Prerequisite:** A2 (DNS pointed).
**What:** Attach the domain in the Pages project settings.
**Guardrail:** still fully noindex — but the site becomes reachable at the
real domain for the first time. **Confirm with the owner before this
specific step**, even though nothing here violates a hard rule: it's the
first moment "staycontext.com" resolves to anything, worth a heads-up
rather than a silent flip.

### B3. Legal pages live
**Prerequisite:** A3 done and explicitly confirmed.
**What:** Remove the DRAFT banner and flip `indexable: true` on the 4
legal pages' frontmatter. This is safe to do *before* `PUBLIC_INDEXING_
ENABLED` itself flips: `BaseLayout.astro`'s robots logic is `PUBLIC_
INDEXING_ENABLED AND indexable` (plus any `requiresFlag`), so setting a
page's own `indexable: true` ahead of time has zero visible effect until
the site-wide flag in step B5.1 also turns on — this step is content
readiness, not an indexing change by itself.
**Guardrail:** re-run `seo_assertions.py` after — unique titles, one
canonical, no forbidden JSON-LD keys — before deploy.

### B4. Google Search Console property
**Prerequisite:** B2 (domain live).
**What:** Add `staycontext.com` as a GSC property. Verification is
simplest via an HTML meta tag Claude adds to `BaseLayout.astro`'s
`<head>` (no DNS access needed) — GSC gives a verification string once
the property is created.
**Guardrail:** do this *before* flipping any indexing flag — GSC can see
crawl/coverage data for a noindexed site (Google still fetches robots.txt
and can show "blocked by robots.txt" status), which is a useful clean
baseline before anything is actually indexable.
**Hand back needed mid-step:** the GSC verification meta-tag value (owner
creates the GSC property, since it's tied to the owner's Google account —
Claude cannot create it) → Claude adds the tag and deploys.

### B5. Flip flags — one at a time, smallest blast radius first
Each of these is a separate PR/deploy, not a batch. Wait for the previous
step's verification before starting the next.

1. **`PUBLIC_INDEXING_ENABLED`** — first pass covers home + methodology
   only. Checked against the actual code, not assumed: `index.astro` and
   `methodology.astro` pass `indexable={true}` (so they respond to this
   flag immediately), but `city/[id].astro` currently hardcodes
   `indexable={false}` as a literal — matching `compute_publication.py`'s
   current recorded decision (city pages: noindex, "not yet measured
   against real search demand," `docs/seo-policy.md §3`). **Flipping this
   flag alone does not index the 12 city pages** — that needs its own,
   separate decision: update the recorded status in `page_publication`
   *and* wire `city/[id].astro` to read it (`hotel.publication_status`
   already does this on the hotel template — city pages don't yet), not
   just flip the hardcoded literal, to stay compliant with CLAUDE.md hard
   rule 2. Treat "index the city pages" as its own future step, not bundled
   into this one.
   **Verify:** submit the sitemap in GSC, check indexing status over a few
   days, confirm `noindex` truly cleared only where intended (re-run
   `seo_assertions.py`'s sitemap check against the deployed build).
2. **Run `python3 scripts/compute_publication.py`** to populate
   `page_publication` for the reviewed pilot cohort (reads
   `docs/reports/pilot-cohort-proposal.csv` directly — confirm the row
   count matches the owner-approved cohort size from A4 before proceeding,
   especially if any hotel_ids were excluded in A4).
3. **`HOTEL_PAGE_INDEXING_ENABLED`** — this exposes exactly the hotels
   `compute_publication.py` marked `indexable` in step 2, nothing else
   (CLAUDE.md hard rule 2: indexability is a recorded decision). Deploy,
   verify sitemap-hotels.xml matches the expected count exactly.
4. **Hold and monitor.** Per `docs/STATE.md`'s Phase 4 commitment,
   `search_events` becomes the coverage KPI from here — let it accumulate
   real signal for the agreed period before considering cohort expansion.
   No further flag flips scheduled by this runbook past this point.
5. **`AFFILIATE_ENABLED`, `MAP_ENABLED`, `AI_SUMMARIES_ENABLED`** are
   Phase 5+ decisions (affiliate contracts not yet signed — CLAUDE.md
   hard rule 9 applies the moment this flips) — out of this runbook's
   scope, each needs its own review when its precondition is actually met.

### Rollback, at any step
Every flag is read at **build time** (`web/src/lib/flags.ts` — static
site, nothing re-checks per request). Rollback means flipping the env var
back and triggering a redeploy, not an instant runtime toggle — budget a
few minutes for a fresh build (~1-2 min locally for this dataset size;
Cloudflare Pages build times are usually comparable), not zero.

## Guardrails that apply to every step above

- CI (typecheck, e2e, seo-assertions) must be green on the exact commit
  being deployed — never deploy a commit CI hasn't run on.
- `robots.txt`'s own logic (driven by `PUBLIC_INDEXING_ENABLED`) is the
  real kill switch if anything looks wrong post-deploy — flipping it back
  off blocks all crawling immediately on the next deploy, independent of
  any per-page `indexable` state.
- No step in Part B is taken without the matching Part A hand-off having
  actually arrived — this runbook is a sequence, not a schedule.

## 2026-09-12 incident — explicit manual deployment (supersedes Git deployment above)

Owner dashboard evidence: Git connection remains **disconnected** despite
correct settings and GitHub reauthorization. Pushes do not start a Pages
build; the dashboard only replays `77e49b3` (2026-09-09). Production still
serves pre-A/B data, including Singapore Boys' Home. A pushed commit and a
green GitHub CI **do not update production**. Treat deployment as an explicit
manual step until a separately verified repair. Do not create another Pages
project or move the attached `staycontext.com` / `www.staycontext.com` domains.

Prepared, not executed: pinned free dev dependency Wrangler 4.131.1 and
`make deploy`. No login, upload, account creation or dashboard action was
performed by the agent. This does not change any launch/indexing flag.

One-time owner action, from the repository root (Node >=22.12):

```bash
npm --prefix web ci
web/node_modules/.bin/wrangler login
```

The second command opens interactive OAuth in your browser; the owner must
perform it. Choose the existing account that owns `staycontext`. If a stale
`CLOUDFLARE_API_TOKEN` / `CLOUDFLARE_API_KEY` is set in your terminal, unset it
locally before using OAuth; do not paste credentials into chat or git. On
multiple accounts, set `CLOUDFLARE_ACCOUNT_ID` to the existing account's ID.

Each deployment, after checking the **exact commit's CI is green**:

```bash
git pull --ff-only origin main
make deploy
make verify-prod
```

`make deploy` requires a clean `main` matching local `origin/main`, reads
Wrangler's project list to require the existing `staycontext` with its apex
domain, runs the Astro build from committed exports, checks SEO, then checks
robots disallow-all and absence of public sitemaps. Only then it calls:
`wrangler pages deploy web/dist --project-name staycontext --branch main
--commit-hash <HEAD>`. It does not run ETL or regenerate the static selection.
The project keeps its existing Git integration and domains. It runs Wrangler
with closed stdin and `CI=true`: missing auth/project fails rather than
starting login or proposing project creation. Never replace this with a
`pages project create`, `wrangler deploy` Worker migration, or a new project.

If a preflight/build/SEO check fails, stop and resolve that error; there has
been no upload. If Pages refuses the existing project or account, leave the
incident open for the owner. The command deliberately supports the current
all-noindex state only; a later indexing launch needs its own reviewed change.

After upload, verify both domains and confirm these former scored URLs no
longer return a hotel page (expected 404), and that their names disappeared
from search: `/hotel/singapore-boys-home-3ba67d6c` and the ALL Accor slug in
`bloc-b-brands.json`. A deployment success message alone does not close the
incident. Rollback is an explicit owner deployment of a reviewed commit;
**do not roll back to pre-A/B**, which would restore excluded institutions.

Sources: [Cloudflare existing Git projects support manual Wrangler uploads](https://developers.cloudflare.com/pages/get-started/direct-upload/),
[Pages deployment CLI](https://developers.cloudflare.com/workers/wrangler/commands/pages/).
Validation: 3 mocked deployment safety tests (no network/auth), local full
build/SEO; command is prepared, production outcome remains unverified.
