"""Non-establishment identities, independently of a hotel's brand (ADR-017).

Rules are withholding signals, not assertions that a named company is fake.
The generic attribute diagnostic is deliberately NOT part of this detector.
"""
from functools import lru_cache
import json
import logging
from pathlib import Path
import re

from .institutions import normalize_name

RULES_PATH = Path(__file__).with_name('brand_rules.json')
LOGGER = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def config():
    data = json.loads(RULES_PATH.read_text())
    if data.get('version') != 1 or not data.get('rules'):
        raise ValueError('Invalid brand rules; refusing to publish')
    return data


@lru_cache(maxsize=1)
def compiled_rules():
    result = []
    for rule in config()['rules']:
        if rule['match'] not in ('word', 'substring', 'full') or not rule['terms']:
            raise ValueError('Invalid brand match rule')
        pattern = '(?:' + '|'.join(re.escape(normalize_name(t)) for t in rule['terms']) + ')'
        if rule['match'] == 'word':
            pattern = r'(?<!\w)' + pattern + r'(?!\w)'
        elif rule['match'] == 'full':
            pattern = '^' + pattern + '$'
        result.append((rule, re.compile(pattern)))
    return result


@lru_cache(maxsize=1)
def quarantined_records():
    return {key: r for r in config()['quarantined_records'] for key in (r['id'], r['slug'])}


def has_property_prefix(prefix):
    terms = config()['property_prefix_terms']
    def pattern(items):
        return r'(?<!\w)(?:' + '|'.join(re.escape(normalize_name(t)) for t in items) + r')(?!\w)'
    # "Hotel Marriott Bonvoy" is still just the programme. Require an identity
    # beyond hospitality/affiliation filler, e.g. "Maple Hotel, Marriott Bonvoy".
    remainder = re.sub(pattern(terms + ['the','a','an','official','loyalty','program','programme']), ' ', prefix).strip()
    return bool(re.search(pattern(terms), prefix) and remainder)


def brand_matches(name, hotel_id=None):
    text = normalize_name(name or '')
    matches = []
    for rule, pattern in compiled_rules():
        match = pattern.search(text)
        if not match:
            continue
        # An affiliation following a named property is not an umbrella listing.
        # The exception applies ONLY to group/program rules, never office rules.
        if rule.get('allow_property_prefix') and text[:match.start()].strip():
            prefix = text[:match.start()].strip()
            if has_property_prefix(prefix):
                continue
        matches.append({'reason':rule['reason'], 'group':rule.get('group') or group_for_name(name),
                        'language':rule['language'], 'term':match.group()})
    if record := quarantined_records().get(hotel_id):
        return [{**m, 'group':record['group']} for m in matches] or [{'reason':record['reason'], 'group':record['group'],
                            'language':'record', 'term':'quarantined_id'}]
    for hotel in config()['reviewed_hotels']:
        if hotel_id in (hotel['id'], hotel['slug']) and text == normalize_name(hotel['name']):
            return [m for m in matches if m['reason'] not in hotel['allowed_reasons']]
    return matches


@lru_cache(maxsize=1)
def group_patterns():
    return [(g, re.compile(r'(?<!\w)(?:' + '|'.join(re.escape(normalize_name(a)) for a in aliases) + r')(?!\w)'))
            for g, aliases in config()['groups'].items()]


def group_for_name(name):
    """Name-derived group only; unknown is not silently labelled independent."""
    text = normalize_name(name or '')
    for group, pattern in group_patterns():
        if pattern.search(text):
            return group
    return 'unresolved'


def assert_no_brands(rows, *, context):
    excluded = [{'id':r['id'], 'name':r.get('name'), 'matches':m}
                for r in rows if (m := brand_matches(r.get('name'), r['id']))]
    if excluded:
        LOGGER.error('Non-establishment brand exclusion in %s: %s', context, json.dumps(excluded, ensure_ascii=False))
        raise ValueError(f'{context}: {len(excluded)} non-establishment brand candidate(s); purge and audit before export')
