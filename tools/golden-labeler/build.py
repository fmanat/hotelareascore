"""Build the publishable golden-set labeling tool from template.html +
tests/golden/selection.json.

Deliberately strips selection.json down to identity-only fields before
embedding them (id, name, city, locality, lat, lon) — the tool must stay
blind (docs/scoring.md §4.1): confidence, balanced_score and the selection
rationale live in selection.json for methodology/audit purposes, never in
the page a labeler sees.

Usage:
    python3 tools/golden-labeler/build.py
    # then publish the resulting dist/golden-labeler.html as an Artifact
    # with capabilities: {"db": {}, "downloads": true}
"""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parent.parent

TEMPLATE_PATH = HERE / "template.html"
SELECTION_PATH = REPO_ROOT / "tests" / "golden" / "selection.json"
OUTPUT_PATH = HERE / "dist" / "golden-labeler.html"

BLIND_FIELDS = ("id", "name", "city", "locality", "lat", "lon")


def build() -> Path:
    selection = json.loads(SELECTION_PATH.read_text(encoding="utf-8"))
    blind_hotels = [{k: h[k] for k in BLIND_FIELDS} for h in selection]

    template = TEMPLATE_PATH.read_text(encoding="utf-8")
    if "__HOTELS_JSON__" not in template:
        raise ValueError("template.html is missing the __HOTELS_JSON__ placeholder")

    out = template.replace("__HOTELS_JSON__", json.dumps(blind_hotels, ensure_ascii=False))
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(out, encoding="utf-8")
    return OUTPUT_PATH


if __name__ == "__main__":
    path = build()
    print(f"wrote {path} ({len(path.read_text())} bytes)")
