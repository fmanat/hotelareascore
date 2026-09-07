// Shared accessible-combobox behavior for the site's 3 autocomplete
// widgets (SearchBox.astro, ComparePicker.astro, compare.astro's own
// pick-a/pick-b). Extracted 2026-09-07 after an accessibility audit
// (docs/reports/phase-4-accessibility-audit.md) found all 3 independent
// hand-written copies had the same gaps -- no keyboard navigation, no
// Escape-to-close, no aria-live announcement, and an incomplete ARIA
// combobox pattern (role="listbox" with no role="option" children and no
// role="combobox" input). One shared implementation means fixing it once
// keeps it fixed everywhere, instead of the 3 copies drifting apart again
// (compare.astro's own copy was already missing aria-expanded/
// aria-controls that the other two had).
//
// Follows the WAI-ARIA Authoring Practices combobox pattern: focus never
// leaves the input; the active suggestion is tracked virtually via
// aria-activedescendant and announced through a visually-hidden
// aria-live region, not by moving real DOM focus into the list.

export interface AutocompleteConfig<T> {
  input: HTMLInputElement;
  resultsEl: HTMLUListElement;
  /** Already-filtered matches for `query` (caller owns loading/filtering/
   * slicing its own index -- this module only handles the UI/keyboard/ARIA
   * layer). */
  search: (query: string) => Promise<T[]> | T[];
  label: (item: T) => string;
  meta: (item: T) => string;
  onSelect: (item: T) => void;
  minLength?: number;
  debounceMs?: number;
  emptyMessage?: string;
  /** Boundary for the "click outside closes the list" listener. Defaults
   * to `input.parentElement`. */
  containerEl?: HTMLElement | null;
}

let liveRegionSeq = 0;

function ensureLiveRegion(after: HTMLElement): HTMLElement {
  const existing = after.nextElementSibling;
  if (existing instanceof HTMLElement && existing.dataset.autocompleteLive === 'true') {
    return existing;
  }
  const region = document.createElement('div');
  region.dataset.autocompleteLive = 'true';
  region.id = `autocomplete-live-${++liveRegionSeq}`;
  region.setAttribute('aria-live', 'polite');
  region.setAttribute('aria-atomic', 'true');
  region.style.position = 'absolute';
  region.style.width = '1px';
  region.style.height = '1px';
  region.style.overflow = 'hidden';
  region.style.clipPath = 'inset(50%)';
  after.insertAdjacentElement('afterend', region);
  return region;
}

export function setupAutocomplete<T>(cfg: AutocompleteConfig<T>): void {
  const { input, resultsEl } = cfg;
  const minLength = cfg.minLength ?? 2;
  const debounceMs = cfg.debounceMs ?? 120;
  const emptyMessage = cfg.emptyMessage ?? 'No hotels found in our index.';
  const containerEl = cfg.containerEl ?? input.parentElement;

  if (!resultsEl.id) resultsEl.id = `autocomplete-results-${++liveRegionSeq}`;
  resultsEl.setAttribute('role', 'listbox');
  const liveRegion = ensureLiveRegion(resultsEl);

  input.setAttribute('role', 'combobox');
  input.setAttribute('aria-autocomplete', 'list');
  input.setAttribute('aria-haspopup', 'listbox');
  input.setAttribute('aria-expanded', 'false');
  input.setAttribute('aria-controls', resultsEl.id);

  let items: T[] = [];
  let activeIndex = -1;

  function optionId(i: number): string {
    return `${resultsEl.id}-option-${i}`;
  }

  function close(): void {
    resultsEl.hidden = true;
    input.setAttribute('aria-expanded', 'false');
    input.removeAttribute('aria-activedescendant');
    activeIndex = -1;
  }

  function setActive(i: number): void {
    if (items.length === 0) return;
    activeIndex = Math.max(0, Math.min(i, items.length - 1));
    input.setAttribute('aria-activedescendant', optionId(activeIndex));
    resultsEl.querySelectorAll('li[role="option"]').forEach((li, idx) => {
      const active = idx === activeIndex;
      li.classList.toggle('active', active);
      li.setAttribute('aria-selected', String(active));
      if (active) (li as HTMLElement).scrollIntoView({ block: 'nearest' });
    });
  }

  function selectItem(item: T): void {
    input.value = cfg.label(item);
    close();
    resultsEl.innerHTML = '';
    cfg.onSelect(item);
  }

  function render(query: string): void {
    resultsEl.innerHTML = '';
    activeIndex = -1;
    input.removeAttribute('aria-activedescendant');

    if (query.length < minLength) {
      close();
      liveRegion.textContent = '';
      return;
    }
    if (items.length === 0) {
      const li = document.createElement('li');
      li.className = 'empty';
      li.textContent = emptyMessage;
      resultsEl.appendChild(li);
      resultsEl.hidden = false;
      input.setAttribute('aria-expanded', 'true');
      liveRegion.textContent = emptyMessage;
      return;
    }
    const frag = document.createDocumentFragment();
    items.forEach((item, i) => {
      const li = document.createElement('li');
      li.id = optionId(i);
      li.setAttribute('role', 'option');
      li.setAttribute('aria-selected', 'false');
      const label = document.createElement('span');
      label.textContent = cfg.label(item);
      li.appendChild(label);
      const metaText = cfg.meta(item);
      if (metaText) {
        const meta = document.createElement('span');
        meta.className = 'meta';
        meta.textContent = metaText;
        li.appendChild(meta);
      }
      li.addEventListener('mousedown', (e) => {
        // mousedown (not click) fires before the input's blur, so a
        // click-outside/blur handler elsewhere can't close the list out
        // from under this selection.
        e.preventDefault();
        selectItem(item);
      });
      li.addEventListener('mouseenter', () => setActive(i));
      frag.appendChild(li);
    });
    resultsEl.appendChild(frag);
    resultsEl.hidden = false;
    input.setAttribute('aria-expanded', 'true');
    liveRegion.textContent = `${items.length} result${items.length === 1 ? '' : 's'} available.`;
  }

  let debounceTimer: number | undefined;
  input.addEventListener('input', () => {
    const query = input.value.trim().toLowerCase();
    window.clearTimeout(debounceTimer);
    debounceTimer = window.setTimeout(async () => {
      items = query.length < minLength ? [] : await cfg.search(query);
      render(query);
    }, debounceMs);
  });

  input.addEventListener('keydown', (e) => {
    switch (e.key) {
      case 'ArrowDown':
        // Also reopens the list from a cached, still-valid `items` if it
        // was closed by Escape without the query changing -- standard
        // combobox behavior, not just "do nothing while closed".
        if (items.length > 0) {
          e.preventDefault();
          if (resultsEl.hidden) {
            resultsEl.hidden = false;
            input.setAttribute('aria-expanded', 'true');
          }
          setActive(activeIndex + 1);
        }
        break;
      case 'ArrowUp':
        if (!resultsEl.hidden && items.length > 0) {
          e.preventDefault();
          setActive(activeIndex - 1);
        }
        break;
      case 'Enter':
        if (!resultsEl.hidden && activeIndex >= 0 && items[activeIndex]) {
          e.preventDefault();
          selectItem(items[activeIndex]);
        }
        break;
      case 'Escape':
        if (!resultsEl.hidden) {
          e.preventDefault();
          close();
        }
        break;
    }
  });

  document.addEventListener('click', (e) => {
    if (!(e.target instanceof Node)) return;
    if (containerEl && !containerEl.contains(e.target)) close();
  });
}
