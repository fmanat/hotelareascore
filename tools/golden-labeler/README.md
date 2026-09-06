# Golden-set labeler

Source for the Phase 3 golden-set labeling tool (`docs/scoring.md §4.1`).
Published as a Claude Artifact so the owner can rate hotels from any device;
this directory is the versioned source, not a copy of the published page.

## Files

- `template.html` — the tool itself: blind (no scores/verdicts/reason codes
  ever shown — see the mandatory rule in `docs/scoring.md §4.1`), mobile-first,
  keyboard shortcuts, shuffled hotel order, "can't judge" skip, CSV export.
  Contains one placeholder, `__HOTELS_JSON__`, filled in at build time.
- `build.py` — injects the identity-only fields (id, name, city, locality,
  lat, lon) from `tests/golden/selection.json` into the template. Deliberately
  strips out `confidence`, `balanced_score` and `selection_reason` — those
  are methodology/audit data, never shown to the labeler.
- `dist/` — build output, gitignored (regenerate, don't hand-edit or commit).

## How a hotel gets into the tool

`tests/golden/selection.json` is the canonical, versioned list: which
hotels, from which cities, and why each was picked (chain vs. independent,
score/confidence spread anchor, or a deliberate calm-vs-nightlife tension
case — see `docs/reports/phase-3-plan.md §6`). Change the selection there,
not in the tool.

## Build & publish

```bash
python3 tools/golden-labeler/build.py
# -> tools/golden-labeler/dist/golden-labeler.html
```

Publish that file as a Claude Artifact with
`capabilities: {"db": {}, "downloads": true}` — `db` for cross-session/
cross-device resume, `downloads` for the CSV export button. Republish the
same Artifact URL (don't create a new one) whenever `selection.json` or
`template.html` changes, so the owner's in-progress labels (stored in the
Artifact's own `db`, keyed by hotel id) carry over.

## How labels get back into the repo (the part that matters)

The tool's `db` storage lives inside the published Artifact — **it is not
part of this repo and Claude cannot read it by browsing the codebase.**
Two ways the labels actually reach `tests/golden/hotels.csv`:

1. **Owner-driven (what the tool is built for):** click "Export labels
   (CSV)" in the tool. It tries a real file download first
   (`downloads.save`); if that's unavailable in the current view, it falls
   back to a copy-paste panel. Either way, hand the resulting CSV to
   Claude (attach the file, or paste the text) to be committed as
   `tests/golden/hotels.csv`.
2. **Claude-driven (works without the owner doing anything):** the
   `Artifact` tool's `read_db` action can query the tool's `labels`
   collection directly in a later session — no export step needed. This is
   the fallback if the export button ever fails; it's not a replacement for
   giving the owner a working export, since they may want to inspect or
   reuse the CSV themselves.

The CSV schema (columns, in order):

```
hotel_id,name,city,locality,transit_convenience,nearby_restaurants,major_road_exposure,nightlife_intensity,park_family_convenience,labeled_at
```

Rows marked "can't judge" in the tool are excluded from the export entirely
(no guessed label — `docs/scoring.md §4.1`), not included with blanks.
