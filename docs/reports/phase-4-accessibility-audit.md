# Accessibility audit — interactive components

> Optional item, this session (time remained after tasks 1-4). Manual
> review of markup, ARIA usage, keyboard handling, and computed WCAG
> contrast ratios for the site's 3 interactive component families:
> hotel-search autocomplete (`SearchBox.astro`), the compare-hotel picker
> (`ComparePicker.astro`), and the persona selector
> (`ScoreDimensions.astro`) — plus `compare.astro`'s own inline pair of
> pickers, a third hand-written copy of the same pattern. Report only, no
> automated scanner run (no axe-core/pa11y dependency added — everything
> below is verified against the actual source and computed contrast
> math, not guessed). **Nothing was fixed.**

## Findings, ranked by severity

### 1. [HIGH] No keyboard interaction model for any of the 3 autocomplete widgets

`SearchBox.astro` (home), `ComparePicker.astro` (hotel pages), and
`compare.astro`'s own `pick-a`/`pick-b` inputs all follow the same
pattern: typing filters a `role="listbox"` of results, but none of the
three attaches a `keydown` handler to the input. Concretely, for a
keyboard-only user:
- No ArrowDown/ArrowUp to move between suggestions — the only way to
  reach a result is repeated Tab presses (works, since results are real
  `<a>`/`<button>` elements, but doesn't match the autocomplete pattern
  every screen reader user and most sighted keyboard users expect).
- No Escape to close the open list — only a `document` `click` listener
  closes it; a keyboard user who opened the list by typing has no
  keyboard-only way to dismiss it short of tabbing all the way through.
- No `aria-live` region anywhere in any of the 3 implementations, so a
  screen reader user gets **no spoken feedback** that results appeared,
  how many, or that "no hotels found" — the only way to discover this is
  to navigate into the (unannounced) list manually.

### 2. [MODERATE] Incomplete ARIA combobox pattern

All 3 widgets set `role="listbox"` on the results `<ul>` and
`aria-controls`/`aria-expanded` on the input (`compare.astro`'s own
pickers are missing even those two — see finding 6), but:
- List items are plain `<li><a>…</a></li>` (or `<li><button>` in
  `compare.astro`) — never `role="option"`.
- The `<input>` itself is never `role="combobox"` and never carries
  `aria-autocomplete="list"` or `aria-activedescendant`.

A `role="listbox"` with no `role="option"` children and no combobox on
the input is not a complete, recognized ARIA pattern — behavior varies by
screen reader/browser combination rather than being reliably announced as
"N suggestions, use arrow keys."

### 3. [MODERATE] Persona selector: `tablist`/`tab` roles without the tab keyboard model

`ScoreDimensions.astro`'s persona buttons use `role="tablist"` /
`role="tab"` / `aria-selected` — correct roles — but implement none of
the WAI-ARIA Authoring Practices keyboard behavior for that pattern
(arrow-key navigation between tabs, `Home`/`End`, roving `tabindex` so
only the active tab is a Tab stop). Every button stays individually
Tab-focusable and is activated by Enter/Space like a plain button group,
which **works** but doesn't match what a screen reader announces
("tab 1 of 6") — a user who tries the arrow keys the announcement implies
will find nothing happens.

### 4. [MODERATE] Persona switch has no live-region announcement

Clicking a persona button changes the "fit for `<persona>` travelers:
`<n>`/100" line and which of the 6 dimension cards are visually
emphasized/muted (`ScoreDimensions.astro`'s `applyPersona()`) — a
meaningful content change with no `aria-live="polite"` anywhere on the
`.fit-line` or the dims list. A screen reader user who activates a
persona gets no spoken confirmation that anything changed unless they
manually re-navigate to that text afterward.

### 5. [LOW-MODERATE] Border color fails WCAG 1.4.11 non-text contrast where it's the only boundary cue

Computed against the site's actual `:root` tokens (`BaseLayout.astro`):

| Pair | Ratio | WCAG 1.4.11 (3:1, non-text UI boundaries) |
|---|---:|---|
| `--border` #e6e2da on `--bg` #fbfaf8 | **1.24:1** | Fails |
| `--warn` bar-fill #a15c00 on `--border` track #e6e2da | 4.02:1 | Passes |
| `--low` bar-fill #a13a2e on `--border` track #e6e2da | 5.14:1 | Passes |
| `--accent` bar-fill #0f6e5c on `--border` track #e6e2da | 4.77:1 | Passes |

`--border` is used for input-field outlines, `.dim` score-card edges, and
the header divider. Where an element also has its own `--surface`
(#ffffff) fill against the `--bg` page background, the shape is still
perceivable from its fill, softening the practical impact; where an
element relies on the border alone as its only visible edge, 1.24:1 is a
real WCAG failure worth a look, not a token swap made speculatively here.

All **text** contrast pairs checked pass WCAG AA comfortably: body text
16.1:1, muted text 6.3-6.6:1, links 6.17:1, the `--warn` semantic color
4.98:1 — no text-contrast issue found anywhere. Focus indicators are
visible: inputs get an explicit 2px `--accent` outline (6.17:1 contrast);
nothing in the codebase resets the browser's default focus ring
elsewhere (checked — no `outline: none` anywhere), so every other
interactive element keeps its native focus indicator.

### 6. [LOW, code-quality with an accessibility consequence] Three independent copies of the same widget have drifted apart

`SearchBox.astro` and `ComparePicker.astro` are near-identical
implementations (same debounce, same fetch, same markup shape) with
matching `aria-expanded`/`aria-controls` wiring. `compare.astro` writes a
**third**, inline version (`setupPicker()`) for its own two pickers —
and that third copy is missing `aria-expanded`/`aria-controls` entirely,
alongside every issue above. Consolidating to one shared component
wouldn't fix findings 1-4, but would guarantee whatever accessibility
baseline gets fixed later applies uniformly instead of needing the same
fix applied three times (and re-drifting the next time only one copy is
touched).

## What's already solid (checked, not assumed)

- No `outline: none` reset anywhere — default focus rings survive on
  every element that doesn't get an explicit, visible replacement.
- Explicit `<label>` elements (visually hidden or visible) on every
  search/compare input — none rely on `placeholder` alone.
- Text contrast passes AA everywhere checked, with real margin (lowest is
  4.98:1 against a 4.5:1 bar).
- `noindex`/`aria-label="Legal"` and similar semantic landmarks are used
  correctly elsewhere in `BaseLayout.astro` (footer nav has
  `aria-label="Legal"`).

## Not evaluated this pass

- Screen-reader software testing (VoiceOver/NVDA/JAWS) — this audit is
  markup/ARIA/contrast review, not an assistive-technology walkthrough.
- The map component (`MAP_ENABLED` is off; nothing to audit yet).
- Mobile touch-target sizing (no automated check run; the persona buttons
  and search results look adequately sized on inspection but weren't
  measured against the 44×44px guideline pixel-by-pixel).

No fix was applied for any finding above, per this session's instruction —
report only.
