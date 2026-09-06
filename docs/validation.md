# validation.md — Phase 0bis: demand validation before heavy build

> Purpose: test the riskiest assumptions BEFORE building the full pipeline.
> The original plan's first go/no-go arrived ~8 weeks in, after everything was
> built. This phase moves the kill decision to week 1–2 and costs ≈ €0.

## 1. The assumptions being tested

A. **Demand exists**: meaningful search volume on hotel-location verification
   intent (`{hotel} location`, `is {hotel} in a good location`,
   `quiet area to stay in {city}`, `where to stay in {city} without a car`).
B. **The SERP is winnable**: a new domain can realistically appear for some
   subset of these queries within 6–12 months.
C. **The economics can work**: visits × outbound CTR × EPC can plausibly cover
   costs and reward the effort.

If A, B and C all fail, the product should not be built in this form.

## 2. Work items (owner + Claude, ~1 week elapsed, a few hours owner time)

### 2.1 Query-demand snapshot
For 3 sample cities (e.g. London, Lisbon, Bangkok) and ~20 hotels each:
- collect autocomplete/related-query evidence for the validation cluster;
- use free keyword tooling (Google Keyword Planner ranges, GSC of any existing
  owned site, autocomplete scraping by hand) — no paid SEO tools in Phase 0bis;
- classify each query: volume band (0 / <100 / 100–1k / >1k monthly), intent.

### 2.2 SERP reality check (the critical one)
For 30 representative queries across the three clusters, record what actually
ranks today:
- Is the SERP dominated by Google Maps pack / Booking / Tripadvisor /
  the hotel's own site? (expected for `{hotel} location`)
- Do Reddit/forum/blog results appear? (signal that Google lacks a good
  dedicated answer → opportunity)
- Are there any small/independent sites ranking? (existence proof)
Output: a table `query → SERP composition → opportunity score (0–3)`.

### 2.3 Competitor scan
One page, not a report: Google Maps itself, Booking/Expedia map layers,
Walk Score, any "location score" features on OTAs, travel blogs answering
"where to stay in X". For each: what they answer, what they don't, and whether
our computed-surroundings angle is genuinely absent or just poorly packaged.

### 2.4 Revenue model (orders of magnitude, not precision)
Parameters and defensible default ranges — revalidate against real program
terms at Phase 5:

| Parameter | Low | Mid | High |
|---|---:|---:|---:|
| Visits/day | 300 (Stage A ceiling) | 1,500 (Stage B) | 10,000 (ambition) |
| Completed-check rate | 40% | 55% | 70% |
| Result → outbound affiliate CTR | 5% | 10% | 15% |
| EPC per outbound click (€) | 0.10 | 0.25 | 0.45 |

Monthly revenue = visits/day × check rate × CTR × EPC × 30.

Illustrative mid-case math:
- Stage A (300/day): 300 × .55 × .10 × .25 × 30 ≈ **€124/month**
- Stage B (1,500/day): ≈ **€619/month**
- Ambition (10,000/day): ≈ **€4,125/month**

Reading: the project only becomes financially interesting at Stage B+.
Stage A revenue roughly covers costs at best. This is acceptable IF the owner
treats months 1–6 as an experiment, not income — state this explicitly in the
GO decision.

### 2.5 Honest owner-time budget (replaces "a few hours/month")

| Phase | Realistic owner time |
|---|---|
| 0 + 0bis | 4–8 h total (decisions, SERP review) |
| 1–2 (data & product proof) | 2–4 h/week (PR review, inspecting outputs) |
| 3 (golden set: 50 hotels × 5 dims) | 8–15 h one-off |
| 4–5 (launch + affiliate) | 2–3 h/week |
| 6+ (steady state) | 3–5 h/month — the original promise, reached ~month 4–6 |

## 3. Kill / pivot / go criteria

Evaluate after 2.1–2.4 and write the result in STATE.md.

**KILL** (do not build) if ALL of:
- validation-cluster queries are overwhelmingly volume-band 0/<100, AND
- SERP check shows 0 opportunity-score-≥2 queries out of 30, AND
- no competitor gap identified beyond "we'd do it slightly better".

**PIVOT** (reshape before building) if:
- hotel-name queries are dead but city-intent queries
  (`quiet area to stay in {city}` etc.) show opportunity → pivot the SEO
  center of gravity to city/area pages and treat the hotel checker as a
  product/retention feature, not the acquisition engine; or
- demand exists but SERPs are saturated by strong content → consider the B2B
  widget/API path earlier (see strategy §6).

**GO** if:
- ≥ 5 of 30 checked queries score opportunity ≥ 2, OR city-intent cluster
  shows clear long-tail room, AND
- owner accepts the Stage A revenue reality and the time budget in §2.5.

## 4. Optional (cheap) extra signal

A one-page landing ("Check if a hotel is in the right area — coming soon",
email capture), promoted only via 2–3 relevant Reddit/forum answers written
honestly. 20+ signups or strong comment engagement = extra GO confidence.
Not required; do not spend money on ads for this.
