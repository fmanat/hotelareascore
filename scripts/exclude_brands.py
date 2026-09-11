#!/usr/bin/env python3
"""Bloc B: whole-dataset audit/purge plus a NON-ACTIVE attribute diagnostic."""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
import duckdb
from hotelareascore.brands import brand_matches, config, group_for_name, RULES_PATH
from hotelareascore.config import ETL_DIR, load_cities
from hotelareascore.slug import hotel_slug
from exclude_institutions import read_rows, write_json, purge_etl, purge_web

DIAGNOSTIC_DEFINITIONS = {
    'address_incoherent': 'Proxy only: explicit address_country differs from configured city country. Cross-border coverage can be legitimate; not proof of a bad address.',
    'contact_absent': 'All four source arrays (phones, emails, websites, socials) retrieved, with no non-empty value. Presence does not verify contact validity.',
    'same_group_duplicate_coordinates': 'Distinct IDs, exactly equal source lon/lat, group inferred from structured source brand or known name aliases. Unresolved groups never cluster.',
    'all_three_confirmed': 'Intersection of the three observed proxies, not a confirmed non-establishment.',
    'any_observed_signal': 'Union of the three proxies; diagnostic only, no eligibility effect.',
}


def attribute_diagnostic(rows, city, contacts):
    """Tri-state contacts; exact coordinates, known group, distinct source IDs.

    A missing street is incomplete, NOT incoherent. Locality/region differences
    can be legitimate suburbs (notably NYC metro) and are not exclusion evidence.
    No heuristic result is consumed by brand_matches or any publication path.
    """
    groups = {}
    clusters = defaultdict(list)
    for row in rows:
        source = contacts.get(row['id'])
        brand = json.loads(source.get('brand_json') or 'null') if source else None
        brand_name = ((brand or {}).get('names') or {}).get('primary')
        group = group_for_name(brand_name) if brand_name else 'unresolved'
        if group == 'unresolved':
            group = group_for_name(row['name'])
        if group == 'unresolved' and brand_name:
            group = 'source_brand:' + brand_name
        groups[row['id']] = group
        if group != 'unresolved':
            clusters[(row['lon'],row['lat'],group)].append(row['id'])
    counts = Counter({k:0 for k in ('scanned','address_incomplete','address_incoherent','contact_present','contact_absent','contact_unknown','group_known','group_unknown','same_group_duplicate_coordinates','any_observed_signal','all_three_confirmed','all_three_possible_with_unknown_contact')})
    details = []
    for r in rows:
        counts['scanned'] += 1
        source = contacts.get(r['id'])
        fields = ('phones','emails','websites','socials')
        if source is None or any(f not in source for f in fields):
            contact = 'unknown'
        else:
            contact = 'present' if any(str(v).strip() for f in fields for v in (source[f] or []) if v is not None) else 'absent'
        incomplete = not (r.get('address_freeform') or '').strip()
        country = (r.get('address_country') or '').strip().upper()
        # Only explicit country conflicts; unknown countries remain unknown.
        incoherent = bool(country and country != city.country)
        group = groups[r['id']]
        duplicate_ids = clusters.get((r['lon'],r['lat'],group), [])
        duplicate = len(set(duplicate_ids)) > 1
        counts['address_incomplete'] += incomplete
        counts['address_incoherent'] += incoherent
        counts['contact_'+contact] += 1
        counts['group_unknown' if group == 'unresolved' else 'group_known'] += 1
        counts['same_group_duplicate_coordinates'] += duplicate
        counts['all_three_confirmed'] += incoherent and contact == 'absent' and duplicate
        counts['all_three_possible_with_unknown_contact'] += incoherent and contact != 'present' and duplicate
        observed = incoherent or contact == 'absent' or duplicate
        counts['any_observed_signal'] += observed
        if observed:
            details.append({'id':r['id'],'name':r['name'],'group':group,'address_incoherent':incoherent,
                            'address_country':country,'contact':contact,'same_coordinate_ids':duplicate_ids if duplicate else [],
                            'action':'diagnostic_only_no_exclusion'})
    return {'counts':dict(counts),'records':details}


def audit(con, release_dir):
    result = {'release':release_dir.name,'rules_sha256':hashlib.sha256(RULES_PATH.read_bytes()).hexdigest(),
              'report_path':'docs/reports/bloc-b-brands.md','cities':{},'exclusions':[],
              'reviewed_hotels':config()['reviewed_hotels'], 'generic_signal':{'enabled':False,'definitions':DIAGNOSTIC_DEFINITIONS,'cities':{}}}
    pinned = {r['id']:r for r in config()['quarantined_records']}
    for city_id, city in load_cities().items():
        path = release_dir/city_id/'hotels.parquet'
        rows = read_rows(con,path)
        hits = []
        for r in rows:
            matches = brand_matches(r['name'],r['id'])
            if matches:
                review = pinned.get(r['id'],{})
                hits.append({'city_id':city_id,'id':r['id'],'name':r['name'],'slug':hotel_slug(r['name'],r['id']),
                             'address':r.get('address_freeform'),'lon':r['lon'],'lat':r['lat'],
                             'matches':matches,'primary_reason':matches[0]['reason'],
                             'group':review.get('group',matches[0]['group']),
                             'review_status':review.get('review_status','name_signal_pending_review'),
                             'sources':review.get('sources',[]),'review_note':review.get('review_note'),
                             'review_query':review.get('review_query'),
                             'action':'exclude_pending_review'})
        result['exclusions'].extend(hits)
        result['cities'][city_id] = {'scanned':len(rows),'excluded':len(hits),'remaining':len(rows)-len(hits),
            'by_primary_reason':dict(sorted(Counter(h['primary_reason'] for h in hits).items())),
            'by_group':dict(sorted(Counter(h['group'] for h in hits).items())),
            'input_sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
        contact_path = release_dir/city_id/'brand-contact-audit.parquet'
        contacts = {r['id']:r for r in read_rows(con,contact_path)} if contact_path.exists() else {}
        diagnostic = attribute_diagnostic(rows,city,contacts)
        excluded_ids = {h['id'] for h in hits}
        diagnostic['remaining_counts'] = attribute_diagnostic([r for r in rows if r['id'] not in excluded_ids],city,contacts)['counts']
        diagnostic['source_contacts_sha256'] = hashlib.sha256(contact_path.read_bytes()).hexdigest() if contact_path.exists() else None
        result['generic_signal']['cities'][city_id] = diagnostic
    result['totals'] = {k:sum(c[k] for c in result['cities'].values()) for k in ('scanned','excluded','remaining')}
    result['by_group'] = dict(sorted(Counter(h['group'] for h in result['exclusions']).items()))
    result['requested_groups'] = {g:result['by_group'].get(g,0) for g in ('Accor','Marriott','Hyatt','IHG','Hilton','Wyndham','Choice')}
    diagnostics = list(result['generic_signal']['cities'].values())
    result['generic_signal']['totals'] = {k:sum(d['counts'][k] for d in diagnostics) for k in diagnostics[0]['counts']}
    result['generic_signal']['remaining_totals'] = {k:sum(d['remaining_counts'][k] for d in diagnostics) for k in diagnostics[0]['counts']}
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--release', default=json.loads((ROOT/'web/src/data/meta.json').read_text())['release'])
    parser.add_argument('--apply',action='store_true')
    parser.add_argument('--report',type=Path,default=ROOT/'docs/reports/bloc-b-brands.json')
    args = parser.parse_args()
    release_dir = ETL_DIR/args.release
    con = duckdb.connect()
    result = audit(con,release_dir)
    if args.report.exists() and not result['totals']['excluded']:
        print('No brand candidates remain; preserving the pre-purge audit.')
        return
    write_json(args.report,result)
    if args.apply:
        unreviewed = [h['id'] for h in result['exclusions'] if h['id'] not in {r['id'] for r in config()['quarantined_records']}]
        if unreviewed:
            raise ValueError(f'Persist quarantine IDs and review log before purge: {unreviewed}')
        purge_etl(con,release_dir,result,family='brand')
        purge_web(result,release_dir,matcher=brand_matches)
        write_json(args.report,result)
        assert audit(con,release_dir)['totals']['excluded'] == 0
    print(json.dumps({'totals':result['totals'],'cities':result['cities'],'groups':result['by_group'],
                      'generic':result['generic_signal']['totals']},indent=2))


if __name__ == '__main__':
    main()
