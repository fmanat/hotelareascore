# Phase 0bis §2.3 — Competitor scan (PRE-FILLED DRAFT — owner to verify)

> Written from Claude's product knowledge (cutoff: Jan 2026). Features change;
> verify each line in 2–3 minutes of clicking before signing off. One page max.

| Player | What it answers | What it does NOT answer | Our angle absent, or just badly packaged? |
|---|---|---|---|
| **Google Maps** (the real competitor) | Where the hotel is; what's visibly nearby; user can pan/zoom and infer everything manually | No synthesis. No score, no persona lens, no city-relative baseline, no "is this good FOR my kind of stay", no confidence. The user does 10 minutes of manual work per hotel. | Absent as a product. Maps gives raw material, not an answer. Our promise is the 15-second synthesis. |
| **Booking.com map + "location score"** | Map layer with POI pins; a location *sub-rating* (e.g. "9.1 location") derived from guest reviews | The location rating is sentiment, not measurement — it can't say WHY, can't decompose (transit vs quiet vs food), can't compare areas, and is biased by overall stay satisfaction | Badly packaged AND methodologically different (reviews vs computed). Their number is trusted but opaque; our decomposed, explained score is the counter-position. |
| **Expedia / Hotels.com map layers** | Similar map with filters; neighborhood descriptions on some city pages | Same as Booking: no computed surroundings, no persona weighting, prose descriptions are editorial/generic | Absent in computed form. |
| **Tripadvisor** | Reviews mention location anecdotally; "location" bubble sub-rating; some neighborhood guide content | Anecdote ≠ measurement; no decomposition; guides are editorial travel prose | Absent in computed form. |
| **Walk Score** | Computed walkability/transit/bike scores for an address — the closest methodological cousin | US/CA-centric quality, generic address tool: no hotel entity, no hotel search UX, no quiet proxy, no persona fit, no hotel-vs-city comparison, no travel intent framing | EXISTS as methodology proof, absent as a hotel product. Their existence validates that computed area scores are a legible concept. |
| **Travel blogs / "where to stay in X" posts** | Neighborhood-level narrative advice, sometimes good | Hotel-level nothing; static; no data; often affiliate-driven listicles; can't answer "THIS hotel?" | Our hotel-level, data-grounded answer is absent. Blogs are also the SERP incumbent to displace on city-intent queries — respect that in seo-policy. |
| **Reddit (r/travel, city subs)** | Honest crowd answers to "is X a good area", often ranking well in SERPs | Unstructured, stale, city-level, effortful to search | The fact Reddit ranks = Google lacks a dedicated answer. That's our SERP opportunity signal, not a competitor to beat on content volume. |

## One-paragraph conclusion (draft)

The computed-surroundings-for-a-specific-hotel angle appears genuinely
unoccupied: OTAs have review-derived location ratings (opaque, undecomposed),
Walk Score proves the score concept but ignores hotels and travel intent, and
Google Maps provides raw material without synthesis. The risk is NOT that a
competitor already does this; it is (a) whether users search for it
(→ SERP grid), and (b) that Booking/Google could ship a "good enough" version
if the niche proves valuable — which argues for speed-to-data-moat (score
history, baselines) over feature breadth.

**Owner verification checklist (10 min):**
- [ ] Booking still shows a location sub-score on hotel pages; note its label
- [ ] Any new "area insights" feature on Booking/Expedia/Google since Jan 2026?
- [ ] Walk Score still free for single-address lookups; any hotel feature?
- [ ] Spot-check one "where to stay in London" SERP: are AI Overviews now
      answering it directly? (If yes → factor into opportunity scoring.)
