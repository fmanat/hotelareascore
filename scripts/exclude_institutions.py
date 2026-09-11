#!/usr/bin/env python3
"""Audit all configured cities and optionally purge institution candidates.

No score calculation, cohort replacement, indexing or deployment. Kept scores
are copied byte-for-value; city aggregates are recomputed from the kept rows.
Backups of every changed ETL file are retained under institution-backup/.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
import duckdb
from hotelareascore.config import DIMENSIONS, ETL_DIR, load_cities
from hotelareascore.institutions import institution_matches, RULES_PATH, reviewed_hotels
from hotelareascore import publication
from hotelareascore.slug import hotel_slug


def read_rows(con, path):
    cursor = con.execute('SELECT * FROM read_parquet(?)', [str(path)])
    cols = [c[0] for c in cursor.description]
    return [dict(zip(cols, row)) for row in cursor.fetchall()]


def audit(con, release_dir):
    result = {'release': release_dir.name, 'rules_sha256': hashlib.sha256(RULES_PATH.read_bytes()).hexdigest(), 'cities': {}, 'exclusions': [], 'reviewed_hotels': reviewed_hotels()}
    for city in load_cities():
        path = release_dir/city/'hotels.parquet'
        rows = read_rows(con, path)  # Missing city = fail closed; never partial success.
        hits = []
        for row in rows:
            matches = institution_matches(row['name'], row['id'])
            if matches:
                hits.append({'city_id':city, 'id':row['id'], 'name':row['name'], 'slug':hotel_slug(row['name'],row['id']), 'matches':matches, 'primary_reason':matches[0]['reason'], 'action':'exclude_pending_review'})
        result['exclusions'].extend(hits)
        result['cities'][city] = {'scanned':len(rows), 'excluded':len(hits), 'remaining':len(rows)-len(hits), 'by_primary_reason':dict(sorted(Counter(h['primary_reason'] for h in hits).items())), 'input_sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
    result['totals'] = {key:sum(c[key] for c in result['cities'].values()) for key in ('scanned','excluded','remaining')}
    return result


def backup(path, family="institution"):
    dest = path.parent/f"{family}-backup"/path.name
    dest.parent.mkdir(exist_ok=True)
    if not dest.exists():
        shutil.copy2(path, dest)


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')


def purge_etl(con, release_dir, result, *, family="institution"):
    for city in load_cities():
        hits = [r for r in result['exclusions'] if r['city_id'] == city]
        if not hits:
            continue
        folder = release_dir/city
        con.execute('CREATE OR REPLACE TEMP TABLE excluded (id VARCHAR)')
        con.executemany('INSERT INTO excluded VALUES (?)', [(h['id'],) for h in hits])
        for filename, key in [('hotels.parquet','id'),('hotel_scores.parquet','hotel_id'),('nearby_facts.parquet','hotel_id')]:
            path = folder/filename
            # Every dependent artifact must exist; fail before a build on partial ETL.
            backup(path, family)
            con.execute(f'CREATE OR REPLACE TEMP TABLE kept AS SELECT * FROM read_parquet(?) WHERE "{key}" NOT IN (SELECT id FROM excluded)', [str(path)])
            temporary = path.with_suffix('.purged.parquet')
            con.execute('COPY kept TO ? (FORMAT PARQUET)', [str(temporary)])
            temporary.replace(path)
        path = folder/'manifest.json'
        backup(path, family)
        manifest = json.loads(path.read_text())
        manifest['hotels_after_dedupe'] = result['cities'][city]['remaining']
        manifest[f'{family}_excluded_count'] = len(hits)
        manifest[f'{family}_exclusions'] = hits
        manifest[f'{family}_rules_sha256'] = result['rules_sha256']
        manifest[f'{family}_purge_note'] = f'Post-ingest removal; source ingestion time and existing scores unchanged. See {family}-backup for pre-purge artifacts.'
        write_json(path, manifest)
        scores = folder/'hotel_scores.parquet'
        fields = [f'avg({d}) AS {d}_mean, median({d}) AS {d}_median' for d in DIMENSIONS]
        cursor = con.execute('SELECT '+','.join(fields)+',avg(balanced_score) AS balanced_mean,median(confidence) AS confidence_median FROM read_parquet(?)', [str(scores)])
        values = dict(zip([c[0] for c in cursor.description], cursor.fetchone()))
        path = folder/'city_baseline.json'
        backup(path, family)
        baseline = json.loads(path.read_text())
        baseline.update({k:round(v,2) if v is not None else None for k,v in values.items()})
        baseline['n_hotels'] = result['cities'][city]['remaining']
        write_json(path, baseline)
        # Do not leave the old QA report claiming a clean, different dataset.
        qa = folder/'validation_report.json'
        if qa.exists():
            backup(qa, family)
            write_json(qa, {'city_id':city, 'status':f'requires_revalidation_after_{family}_purge', 'report':result.get('report_path', 'docs/reports/bloc-a-institutions.md')})
    with publication.connect() as pub:
        for row in result['exclusions']:
            publication.set_status(pub, 'hotel', row['id'], 'retired', f"{family} exclusion: {row['primary_reason']}; see audit report", f'system:exclude_{family}')


def purge_web(result, release_dir, web_root=ROOT/'web', *, matcher=institution_matches):
    excluded_ids = {r['id'] for r in result['exclusions']}
    excluded_slugs = {r['slug'] for r in result['exclusions']}
    removed = Counter(result.get('removed_web_references_by_file', {}))
    def clean(obj, context):
        if isinstance(obj, list):
            return [value for item in obj if (value := clean(item, context)) is not None]
        if not isinstance(obj, dict):
            return obj
        if (obj.get('id') in excluded_ids or obj.get('slug') in excluded_slugs
                or matcher(obj.get('name'), obj.get('id') or obj.get('slug'))):
            removed[context] += 1
            return None
        return {k: v if k in ('nearby_facts','reason_codes') else clean(v, context) for k,v in obj.items()}
    for folder in (web_root/'src/data', web_root/'public/data'):
        for path in sorted(folder.glob('*.json')):
            original = json.loads(path.read_text())
            filtered = clean(original, f"web/{path.relative_to(web_root)}")
            if filtered != original:
                # Match the existing compact export format to keep diffs local.
                path.write_text(json.dumps(filtered, ensure_ascii=False), encoding='utf-8')
    # Update only aggregates; preserve the staged static-page selection.
    path = web_root/'src/data/city-baselines.json'
    baselines = json.loads(path.read_text())
    for city in load_cities():
        if result['cities'][city]['excluded']:
            baselines[city] = json.loads((release_dir/city/'city_baseline.json').read_text())
    path.write_text(json.dumps(baselines, ensure_ascii=False), encoding='utf-8')
    path = web_root/'src/data/city-pages.json'
    pages = json.loads(path.read_text())
    for page in (pages.values() if isinstance(pages,dict) else pages):
        city = page['city_id']
        if result['cities'][city]['excluded']:
            page['n_hotels'] = baselines[city]['n_hotels']
            for dim in DIMENSIONS:
                page['dimensions'][dim]['mean'] = baselines[city][dim+'_mean']
                page['dimensions'][dim]['median'] = baselines[city][dim+'_median']
    path.write_text(json.dumps(pages, ensure_ascii=False), encoding='utf-8')
    result['removed_web_references_by_file'] = dict(removed)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--release', default=json.loads((ROOT/'web/src/data/meta.json').read_text())['release'])
    parser.add_argument('--apply', action='store_true')
    parser.add_argument('--report', type=Path, default=ROOT/'docs/reports/bloc-a-institutions.json')
    args = parser.parse_args()
    con = duckdb.connect()
    release_dir = ETL_DIR/args.release
    result = audit(con, release_dir)
    if args.report.exists() and not result['totals']['excluded']:
        print('No institution candidates remain; preserving the existing pre-purge audit.')
        return
    args.report.parent.mkdir(parents=True, exist_ok=True)
    # Persist the evidence BEFORE removing any row.
    write_json(args.report, result)
    if args.apply:
        purge_etl(con, release_dir, result)
        purge_web(result, release_dir)
        write_json(args.report, result)
        assert audit(con, release_dir)['totals']['excluded'] == 0
    print(json.dumps(result['totals']))


if __name__ == '__main__':
    main()
