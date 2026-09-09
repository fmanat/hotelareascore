# ADR-015 — "Destination/resort" hotel type: a presentation lens, never a scoring input

- **Status:** accepted (framing only — detection is a separate, gated
  implementation step, see "Sequencing" below)
- **Date:** 2026-09-XX (owner decision session, post night mission #3)
- **Decision recorded from:** owner decision, this session — "Hilton
  Bangkok Suvarnabhumi Golf Resort & Spa" case

## Context

The owner reviewed the pilot cohort v2 pack and found a real, structural
framing problem: **"Hilton Bangkok Suvarnabhumi Golf Resort & Spa"** scores
low on nearly every density dimension (walkability, food & essentials,
nightlife — all measure "things within a short walk") because it is
genuinely isolated. But the owner has personally stayed there for golf and
calls it an excellent hotel *for that purpose*. The scores are not wrong —
a golf resort really doesn't have a corner shop or a metro stop nearby —
but presenting six low density scores with no further context reads as
"bad hotel," which is a **framing failure**, not a **data failure**. The
scoring methodology has no way to say "this kind of isolation is the
point."

This is a real, general pattern, not a one-off: any golf resort, beach
resort, national-park lodge, ski lodge, or theme-park hotel will show the
same shape (low density dimensions, because low-density surroundings are
exactly what makes the location work for its purpose).

## Decision

Introduce a **hotel type** — starting with "destination/resort" — that
changes how a hotel's page is **presented**, and nothing else.

### The non-negotiable rule

> **A hotel type changes presentation. It never changes a score, a
> weight, or a ranking.**

No bonus, no favorable re-weighting, no separate scoring formula for
"destination" hotels. Every score on every hotel — destination-typed or
not — is computed by the exact same formula, from the exact same
`taxonomy-mapping.yml`, at the exact same `score_version`
(`docs/scoring.md §5` still applies: no silent formula change).
Comparability across all hotels — the entire reason a "Similar-scoring
hotels nearby" list or the Compare page means anything — depends on this.
A hotel type is a **lens over already-correct numbers**, supplying the
context a bare number can't carry on its own, never a thumb on the scale.

Concretely, this means:
- `scoring.py` is untouched by this ADR. No dimension formula, weight, or
  normalization curve changes.
- `hotel_type` (or equivalent) is a new, purely descriptive field on the
  hotel record — computed from data, displayed on the page — never an
  input to `scoring.py`, never read by anything under `scoring.py`'s
  import graph.
- The verdict generator (`verdict.py`) may change its **wording** for a
  destination-typed hotel (see "Presentation" below) but not the
  **numbers** it describes.

### Detection: proposed criteria, not yet validated (see the companion report)

A hotel is a detection *candidate* for "destination/resort" when it
combines **both**:
1. **Measured isolation** — low density on the already-computed
   `walkability_density` dimension (the direct "useful destinations
   within a short walk" measure, `docs/scoring.md`), and
2. **Adjacency to a major leisure amenity** — golf, beach, national
   park/nature reserve, ski resort, or theme park, **found in real
   Overture data** (not inferred from the hotel's own name or brand).

**The symmetric trap, explicitly guarded against**: isolation *without* a
qualifying amenity is not "destination" — it's a bad location (a
motorway-adjacent motel, an industrial-zone hotel). Criterion 2 is not
optional; both conditions are required together. Getting this wrong in
either direction breaks trust: false positives dress up a genuinely poor
location as a feature; false negatives leave real destination properties
looking penalized.

Exact thresholds, per-category Overture data availability, city coverage,
and a false-positive sample check are the subject of
`docs/reports/destination-type-detection-feasibility.md` — that report is
the "rapport avant implémentation" this session's order required, and
**no detection code ships until it's reviewed**.

### Presentation, once a hotel type applies

- The hotel page states its type up front — e.g. *"Destination hotel — [X]
  immediately adjacent; a car is needed to reach most other amenities."*
  Plain, factual, no editorializing ("excellent" / implied failure are
  both out).
- The adjacent amenity is surfaced prominently (already-real data — the
  same "Why?" nearby-facts mechanism every hotel page uses, CLAUDE.md hard
  rule 3: no invented facts).
- Car/transfer access is surfaced as a fact when the underlying data
  supports it (e.g. distance to nearest road-accessible point, or airport
  proximity if that's how the destination is normally reached) — **if the
  data doesn't support a specific access claim, the page says so rather
  than inventing one** (owner's explicit instruction: "sinon dis-le, ne
  l'invente [pas]").
- The verdict generator (`verdict.py`) stops phrasing low density
  dimensions as a shortfall for a destination-typed hotel — the numbers
  are unchanged, but "limited walkability" framing (implying a defect)
  becomes a neutral statement of fact ("surroundings are low-density by
  design — this is a destination property built around [amenity], not a
  walkable neighborhood").
- Whether a new "amenity access" dimension or fact is *addable* (vs. just
  reusing existing nearby-facts/distance data) is itself a data-coverage
  question — answered in the detection feasibility report, not assumed
  here.

## Sequencing (owner order: "Cadre-la d'abord, implémente ensuite")

1. **This ADR** — the rule and the intended shape. Accepted now.
2. **Detection feasibility report** — real Overture coverage per
   category/city, false-positive rate on a sample, projected count of
   typed hotels across the 12 cities, explicit isolation-without-amenity
   vs. isolation-with-amenity split. Report only, no code.
3. **Owner reviews the report** and decides whether/how to proceed.
4. **Only then**: detection implementation, `page_publication`-style
   recorded field (a computed fact, not silently inferred at render
   time — same spirit as CLAUDE.md hard rule 2, applied to hotel type
   the way it's already applied to indexability), and the presentation
   changes above.

## Consequences

- If detection is implemented later, the golden-set regression
  (`docs/scoring.md §5`) needs NO new run — no score changes at all. Only
  presentation-layer tests (verdict wording, page rendering) are new
  surface area.
- Reversible at every step: this ADR alone changes nothing about the live
  product. The feasibility report changes nothing either. Only step 4
  touches code, and only after an explicit owner review of step 2's
  findings.
