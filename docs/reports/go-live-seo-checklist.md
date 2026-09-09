# Go-live SEO checklist — exact sequence

- **Date:** 2026-09-09 (night mission #2 follow-up, Tache 3)
- **Scope:** the staged "ready to index" package only — home, methodology,
  all 12 city pages, the 200-hotel pilot cohort v2. Nothing else ever goes
  indexable as a side effect of this sequence (CLAUDE.md hard rule 2).
- **Current state:** everything in the package is recorded **`draft`** in
  `page_publication` (`scripts/compute_publication.py`, re-run this
  session) — staged and verified, not yet decided. Every flag
  (`PUBLIC_INDEXING_ENABLED`, `HOTEL_PAGE_INDEXING_ENABLED`) is still OFF.
  `docs/reports/go-live-sitemap-dry-run-report.md` confirms all 214 staged
  URLs (2 static + 12 city + 200 hotel) resolve to a real built page today
  — zero consistency issues.

Do these steps **in order**. Each one is a deliberate, reversible action;
none of them is "automatic" as a side effect of another.

## 1. Owner cohort validation

- Review a sample of the 200 hotels — `docs/reports/pilot-cohort-proposal.md`
  (selection logic) and `docs/reports/cohort-inspection-12-v2.json` (a
  12-hotel deep-dive pack: full published-page fiche, 11 gates, selection
  reasoning per hotel, including 2 flagged as most discutable).
- This is `docs/STATE.md`'s open decision (b) — the only remaining
  blocker before step 3 can happen. Nothing below is safe to do until this
  is a recorded **GO**.
- If some cohort hotels are rejected here: remove them from
  `docs/reports/pilot-cohort-proposal.csv`, re-run
  `python3 scripts/compute_publication.py`, re-run
  `python3 scripts/dry_run_sitemaps.py` and confirm 0 consistency issues
  again before continuing.

## 2. Google Search Console — domain property verification (DNS TXT via Cloudflare)

Do this in parallel with step 1 if you want GSC data flowing sooner — it
does not expose or index anything on its own.

1. In [Google Search Console](https://search.google.com/search-console),
   **Add property → Domain** (not "URL prefix" — a domain property covers
   `staycontext.com`, `www.staycontext.com`, and both `http`/`https` under
   one property, which is what you want here).
2. Enter `staycontext.com`. Google shows a TXT record value, formatted
   like `google-site-verification=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`.
3. In the Cloudflare dashboard: **your zone → DNS → Records → Add record**.
   - Type: `TXT`
   - Name: `@` (the apex, i.e. `staycontext.com` itself)
   - Content: the exact value Google gave you (include the whole
     `google-site-verification=...` string)
   - TTL: Auto
   - **Proxy status: does not apply to TXT records** — no orange/grey
     cloud toggle to worry about.
4. Save. Wait a few minutes for DNS propagation (Cloudflare is usually
   fast, often seconds).
5. Back in GSC, click **Verify**. If it fails immediately, wait 5–10
   minutes and retry (DNS propagation, not a Cloudflare-side lag).
6. Once verified: leave GSC connected but **do not submit a sitemap yet**
   (step 4) and expect **zero indexing** for now — `robots.txt` still
   disallows everything and every page still renders `noindex` while the
   flags are off (verified today, `make verify-prod` — though note the
   live site is currently down, see `docs/STATE.md` "PROD DOWN"; re-run
   `make verify-prod` once it's back before trusting this).
7. **New finding this session, check before step 4:** `/robots.txt` may be
   served by Cloudflare's own "Managed robots.txt" zone feature instead of
   this repo's `robots.txt.ts` (seen during the outage — `Content-Signal`
   block, `Allow: /` for `User-agent: *`). Confirm which one GSC's own
   robots.txt tester sees once the site is back up; if it's Cloudflare's
   managed version, either disable that zone feature or confirm it merges
   with (rather than overrides) the origin's own `Disallow: /` output —
   otherwise GSC could crawl before you intend it to.

## 3. Flip `PUBLIC_INDEXING_ENABLED` for statics + cities

- This is an environment variable in the Cloudflare Pages project
  settings (`web/src/lib/flags.ts` reads `import.meta.env`), **not** a
  code change — no PR needed for the flip itself.
- Also flip the recorded decisions from `draft` → `indexable` for exactly
  the staged static/city set:
  ```
  python3 -c "
  import sys; sys.path.insert(0, 'src')
  from hotelareascore import publication
  with publication.connect() as con:
      for page_id in ('home', 'methodology'):
          publication.set_status(con, 'static', page_id, 'indexable',
              'Owner GO, go-live checklist step 3', 'owner:go-live', None)
      for city_id in ('london','bangkok','paris','rome','barcelona','amsterdam',
                       'lisbon','sydney','tokyo','dubai','new_york','singapore'):
          publication.set_status(con, 'city', city_id, 'indexable',
              'Owner GO, go-live checklist step 3', 'owner:go-live', None)
  "
  ```
- Re-run `make webdata` (regenerates `city-pages.json` with the new
  `publication_status`), rebuild, redeploy.
- **`HOTEL_PAGE_INDEXING_ENABLED` stays OFF at this point** — no hotel
  goes indexable in this step, deliberately (see step 5).
- Verify: `make verify-prod` — home and city-page samples should now show
  `index, follow`; hotel samples must still show `noindex`.

## 4. Sitemap submission

- Confirm the real (not dry-run) sitemaps now match
  `docs/reports/dry-run-sitemaps/sitemap-{static,cities}.xml` for the
  static+city set (hotels still empty at this point — step 5 hasn't
  happened yet).
- In GSC: **Sitemaps → Add a new sitemap → `sitemap.xml`**.
- Do NOT submit the per-type sitemaps individually — the index at
  `/sitemap.xml` already references all three; GSC crawls the index and
  discovers the rest.

## 5. Cohort 200 — flip hotels, then `HOTEL_PAGE_INDEXING_ENABLED`

- Flip the 200 cohort hotels from `draft` → `indexable`:
  ```
  python3 -c "
  import sys, csv; sys.path.insert(0, 'src')
  from hotelareascore import publication
  ids = [r['id'] for r in csv.DictReader(open('docs/reports/pilot-cohort-proposal.csv'))]
  with publication.connect() as con:
      for hid in ids:
          row = publication.get_status(con, 'hotel', hid)
          publication.set_status(con, 'hotel', hid, 'indexable',
              'Owner GO, go-live checklist step 5', 'owner:go-live',
              row['score_version'] if row else None)
  "
  ```
- Re-run `make webdata` — this both regenerates the sitemap-eligible set
  AND re-runs `select_static_subset` (`docs/adr/013`), which will now
  force these 200 into the static subset again via the `indexable` rule
  (they already have real pages today from Bloc A's build, so this should
  be a no-op in practice — confirm the diff is empty or near-empty before
  rebuilding).
- Flip `HOTEL_PAGE_INDEXING_ENABLED` in Cloudflare Pages env vars.
- Rebuild, redeploy.
- Verify: `make verify-prod` on a cohort-hotel sample — now `index,
  follow`, canonical still `staycontext.com`. Confirm `sitemap-hotels.xml`
  now lists exactly the 200 (compare against
  `docs/reports/dry-run-sitemaps/sitemap-hotels.xml`).

## 6. Start the 90-day clock

- `docs/seo-policy.md §5`: track per cohort page — indexed?, impressions,
  clicks, avg position, internal checker (search box) usage, outbound
  CTR. Add the mandatory AI-Overview column (`docs/STATE.md` "Blockers" —
  whether Google AI Overviews already answer cluster-2 queries).
- Wire `search_events` (searches with no matching hotel) as the per-city
  coverage KPI from day 1 (`docs/STATE.md` "Phase 4 commitment") — this
  was deferred by every prior session; do it now, not at day 90.
- Record the indexing start date somewhere durable (this file, or
  `docs/STATE.md`) — day 90 decision rules in `docs/seo-policy.md §5`:
  - ≥20% of cohort pages have impressions AND ≥5% have clicks → expand
    cohort, same size, same selection logic.
  - Impressions concentrated on independent hotels → rebalance selection.
  - <5% of cohort pages have any impressions → do not add pages; diagnose
    (technical indexing → internal linking → domain trust → demand
    mismatch) before considering the PIVOT path (`docs/validation.md §3`).

## Tooling this checklist depends on (built night mission #2)

- `make verify-prod` (`scripts/verify_prod.py`) — run after every step
  above that touches a flag or a deploy.
- `python3 scripts/dry_run_sitemaps.py` — re-run after any cohort or
  static-page-list change, before trusting step 4's real sitemap.
- `python3 scripts/compute_publication.py` — the only script that writes
  `page_publication`; every write requires a reason and a decider
  (`src/hotelareascore/publication.py`), so the commands above are
  reproducible from this file alone if `data/serving/page_publication.sqlite`
  is ever rebuilt from scratch.
