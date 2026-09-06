# family_convenience v1.2.0 — recalibration result (Bloc A, overnight run)

> Owner's pre-authorized decision rule: Spearman ≥ 0.5 against
> `tests/golden/family_strict.csv` → Phase 3's family_convenience gate
> passes, close it. < 0.5 → stop, no tuning, report and continue. **Result:
> 0.2088 — FAIL. Stopped here. No constant or taxonomy change made beyond
> what was already decided and executed in `docs/adr/007`. Phase 3 stays
> open.**

## What was run

1. Ingested `base/land_use` (expanded classes) + `base/land` (new theme) for
   all 12 cities, re-scored (`score_version` 1.2.0), re-validated (all 12
   pass) — `docs/reports/family-v1.2.0-diagnostic.md`,
   `docs/adr/007-family-convenience-v1.2.0-green-classes.md`. Diff report:
   `docs/reports/score-diff-1.1.0-to-1.2.0.md` — zero big movers in any
   city, family_convenience changed for nearly every hotel as expected,
   mostly upward (broader source, monotonically more green-space hits).
2. Committed `tests/golden/family_strict.csv` (owner-provided, a fresh
   strict re-labeling of the same 50 hotel_ids — "reachable on foot only,"
   see `LABELS-PROVENANCE.md` amendment).
3. Recalibrated: `scripts/calibrate_family_strict.py`.

## Result

| Comparison | Spearman |
|---|---:|
| `family_strict` vs `family_convenience` @ v1.1.0 (before class expansion) | 0.234 |
| `family_strict` vs `family_convenience` @ v1.2.0 (after class expansion) | **0.209** |
| original `park_family_convenience` vs `family_convenience` @ v1.1.0 | 0.095 |
| original `park_family_convenience` vs `family_convenience` @ v1.2.0 | **0.239** |

**The class expansion helped the original, holistic label (0.095 → 0.239,
more than doubled) but did not help — if anything, marginally hurt — the
new strict label (0.234 → 0.209).** Both numbers are far short of any
usable bar (0.5 required, 0.6 used elsewhere in this project).

This split result is itself informative, not just noise: it suggests the
two label definitions are measuring genuinely different things, and
v1.2.0's broader green-space filter moved the formula toward the *holistic*
notion ("this area feels leafy/open/pleasant") rather than the *strict*
one ("there is a specific park or playground within a short walk"). Spot
check on the ten largest label-vs-computed gaps
(`docs/reports/phase-3-family-strict-calibration.json`) supports this:
several hotels the strict label rated 1-2/5 (essentially "no real walkable
park") score 77-99/100 computed — e.g. a hotel in Rome (label 1, computed
91.4) or Amsterdam (label 2, computed 99.1). These are very likely cases
where v1.2.0's `managed/grass`, `recreation/pitch`, or `forest` polygons
sit within radius but aren't what a strict "is there a park to walk to"
judgment would count — a large sports pitch or a patch of managed grass
behind a building is not the same thing as a park a family would actually
visit, even though both are genuinely green and genuinely nearby.

## What this does NOT mean, and what happens now

- It does not mean v1.2.0 is a regression — the original diagnostic
  (`family-v1.2.0-diagnostic.md`) found real, verified, previously-missed
  green space for 3 of 5 spot-checked hotels, and the diff report shows a
  clean, well-behaved change with zero big movers. The fix, taken on its
  own terms, is correct.
- It means the *specific bar this session was asked to clear*
  (`family_strict.csv` ≥ 0.5) was not cleared, and per the owner's own
  pre-authorized rule, **no further tuning happens without another
  explicit review** — not narrowing the class list back down, not
  adjusting radius or saturation, not another re-labeling round on our own
  initiative.
- **Phase 3 stays open on family_convenience.** The rest of the gate
  (transit, restaurants, quietness — accepted as a documented limitation —
  and the overall v1.0.1 freeze) is unaffected and was not reopened by this
  result.

## Candidate next steps (not started, owner's call)

1. Narrow the v1.2.0 land_use/land class list toward the strict definition
   specifically — e.g. drop `recreation/pitch`+`track` and `managed/grass`
   (arguably "a green area" more than "a park to walk to"), keep
   `park`/`playground`/`protected`/`forest`/`zoo`/beach. This is a plausible
   fix but is itself a new hypothesis needing its own verification pass,
   not a safe inference from tonight's data alone.
2. Treat family_convenience like quietness_proxy: ship as a disclosed,
   lower-confidence dimension rather than chasing a calibration bar this
   golden set (Claude-labeled, weak evidence per
   `LABELS-PROVENANCE.md` throughout) may not be able to clear regardless
   of the formula.
3. A genuinely independent (owner or third-party) labeling pass, since two
   rounds of Claude's own re-labeling have now produced two different,
   both-weak results — some of the noise may be in the label, not just the
   formula.
