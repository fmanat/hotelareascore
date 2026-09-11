"""Fail-closed institution exclusion, before hotel/brand allowances (ADR-016).

Matches are reasons for withholding a record, not verified claims about it.
Bare Home/House/hostel are deliberately not evidence of an institution.
"""
from __future__ import annotations

import json
import logging
import re
import unicodedata
from functools import lru_cache
from pathlib import Path

RULES_PATH = Path(__file__).with_name("institution_rules.json")
LOGGER = logging.getLogger(__name__)


def normalize_name(name: str) -> str:
    # Preserve non-Latin script and its vowel signs (especially Thai/Tamil).
    text = unicodedata.normalize("NFKC", name).lower()
    chars = []
    latin = False
    for ch in unicodedata.normalize("NFD", text):
        if unicodedata.combining(ch):
            if not latin:
                chars.append(ch)
        else:
            latin = "LATIN" in unicodedata.name(ch, "")
            chars.append(ch)
    text = unicodedata.normalize("NFC", "".join(chars))
    text = re.sub("['’‘ʼ`＇]", "", text)
    text = re.sub(r"[\W_]+", " ", text, flags=re.UNICODE) if text.isascii() else "".join(
        " " if unicodedata.category(ch)[0] in "PZ" else ch for ch in text
    )
    return " ".join(text.split())


@lru_cache(maxsize=1)
def _rules():
    data = json.loads(RULES_PATH.read_text(encoding="utf-8"))
    if data.get("version") != 1 or not data.get("rules"):
        raise ValueError("Invalid institution rules; refusing to publish")
    result = []
    for rule in data["rules"]:
        if rule["match"] not in {"word", "substring"} or not rule["terms"]:
            raise ValueError("Invalid institution match rule")
        terms = [normalize_name(term) for term in rule["terms"]]
        pattern = "(?:" + "|".join(re.escape(t) for t in terms) + ")"
        if rule["match"] == "word":
            pattern = r"(?<!\w)" + pattern + r"(?!\w)"
        result.append((rule, re.compile(pattern)))
    return result


@lru_cache(maxsize=1)
def reviewed_hotels() -> list[dict]:
    return json.loads(RULES_PATH.read_text(encoding="utf-8")).get("reviewed_hotels", [])


@lru_cache(maxsize=1)
def quarantined_records() -> dict[str, dict]:
    records = json.loads(RULES_PATH.read_text(encoding="utf-8")).get("quarantined_records", [])
    return {key: record for record in records for key in (record["id"], record["slug"])}


def institution_matches(name: str | None, hotel_id: str | None = None) -> list[dict[str, str]]:
    """Return all reason/language/matched-term evidence for the audit log."""
    text = normalize_name(name or "")
    matches = [
        {"reason": rule["reason"], "language": rule["language"], "term": match.group()}
        for rule, pattern in _rules()
        if (match := pattern.search(text))
    ]
    # Once quarantined, a renamed/nameless source record cannot slip back in.
    if record := quarantined_records().get(hotel_id):
        return matches or [{"reason": record["reason"], "language": "record", "term": "quarantined_id"}]
    for hotel in reviewed_hotels():
        if hotel_id in (hotel["id"], hotel["slug"]) and text == normalize_name(hotel["name"]):
            return [m for m in matches if m["reason"] not in hotel["allowed_reasons"]]
    return matches


def assert_no_institutions(rows, *, context: str) -> None:
    """Block stale ETL/export inputs too, regardless of indexing flags."""
    excluded = [
        {"id": row["id"], "name": row.get("name"), "matches": matches}
        for row in rows if (matches := institution_matches(row.get("name"), row["id"]))
    ]
    if excluded:
        LOGGER.error("Institution exclusion in %s: %s", context, json.dumps(excluded, ensure_ascii=False))
        raise ValueError(f"{context}: {len(excluded)} institution candidate(s); purge and audit before export")
