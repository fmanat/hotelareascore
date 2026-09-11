"""Readable proper names, never translation or proof of establishment identity."""
import json
import unicodedata
from anyascii import anyascii

VERSION = '1.0.0-anyascii-0.3.3'

def scripts(text):
    found=set()
    for ch in unicodedata.normalize('NFKC',text or ''):
        if not ch.isalpha():continue
        name=unicodedata.name(ch,'UNKNOWN')
        found.add(next((s for s in ('LATIN','HIRAGANA','KATAKANA','CYRILLIC','GREEK','HANGUL','THAI','ARABIC','HEBREW','CJK') if s in name),'OTHER'))
    return found

def is_readable_latin(text):
    return bool(text and sum(ch.isalpha() for ch in text)>=2 and scripts(text)=={'LATIN'})

def source_latin(names):
    if isinstance(names,str):names=json.loads(names)
    if not isinstance(names,dict):return None
    candidates=[]
    common=names.get('common') or {}
    if isinstance(common,dict):
        for language,value in common.items():
            if isinstance(value,str) and is_readable_latin(value):
                candidates.append((0 if language.startswith('en') else 1,language,value.strip()))
    for rule in names.get('rules') or []:
        # Exclude historical, short/alternate aliases and scoped names.
        if rule.get('variant') not in ('common','official'):continue
        if any(rule.get(k) for k in ('between','side','perspectives')):continue
        value=rule.get('value');language=rule.get('language') or ''
        if isinstance(value,str) and is_readable_latin(value):
            candidates.append((0 if language.startswith('en') else 1,language,value.strip()))
    return sorted(candidates)[0][2] if candidates else None

def present_name(original, names=None):
    original=(original or '').strip()
    script=scripts(original)
    def result(latin,method,eligible):
        return {'display_name':f'{latin} ({original})' if latin and latin!=original else original,
                'name_latin':latin,'name_method':method,'name_index_eligible':eligible,'name_display_version':VERSION}
    if is_readable_latin(original):return result(original,'source_primary_latin',True)
    latin=source_latin(names)
    if latin:return result(latin,'source_alternative_latin',True)
    # Character-by-character romanization is useful only for these scripts.
    # Han/Thai/Arabic/etc require language/context; retain original, noindex.
    supported={'LATIN','HIRAGANA','KATAKANA','CYRILLIC','GREEK','HANGUL'}
    if script and script<=supported:
        latin=anyascii(original)
        # Never silently drop an unknown letter or replace a symbol with words.
        complete=all(anyascii(ch) for ch in original if ch.isalpha())
        if complete and is_readable_latin(latin):return result(latin,'transliteration_approximate',True)
    return result(None,'original_only_unreliable_transliteration',False)

def unique_name_sources(rows):
    """Facts lack POI ids: use alternatives only if all same-name sources agree."""
    alternatives={}
    for name,names in rows:
        alternatives.setdefault(name,set()).add(source_latin(names))
    return {name:{'common':{'en':next(iter(values))}} for name,values in alternatives.items() if len(values)==1 and next(iter(values))}


def display_fields(original, names=None):
    """Compact display-only metadata for POIs; provenance stays in source snapshots."""
    got=present_name(original,names)
    if got['display_name']==original:return {}
    return {k:got[k] for k in ('display_name','name_method')}
