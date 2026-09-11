#!/usr/bin/env python3
"""Read-only source enrichment for Bloc B diagnostics; never changes hotels.

Discover individual GeoParquet assets via STAC and prune by their bounding
boxes before DuckDB range reads. No wildcard bucket scan, paid API or scoring.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import sys
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from hotelareascore.config import ETL_DIR, load_cities
from hotelareascore import overture


def fetch(url):
    with urllib.request.urlopen(url, timeout=30) as response:
        return json.load(response)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--release', required=True)
    parser.add_argument('--cities', help='Optional comma-separated subset for independent/resumable reads')
    args = parser.parse_args()
    catalog = fetch('https://stac.overturemaps.org/catalog.json')
    link = next(l for l in catalog['links'] if args.release in l['href'])
    release = fetch(link['href'])
    places = fetch(next(l['href'] for l in release['links'] if l.get('title') == 'places'))
    collection = fetch(next(l['href'] for l in places['links'] if l['rel'] == 'child'))
    with ThreadPoolExecutor(max_workers=4) as pool:
        items = list(pool.map(fetch, [l['href'] for l in collection['links'] if l['rel'] == 'item']))
    con = overture.connect()
    con.execute('SET threads=4')
    for city_id, city in load_cities().items():
        if args.cities and city_id not in args.cities.split(','):
            continue
        folder = ETL_DIR / args.release / city_id
        output = folder / 'brand-contact-audit.parquet'
        if output.exists():
            print(city_id, 'existing diagnostic snapshot', flush=True)
            continue
        b = city.bbox
        urls = [i['assets']['aws']['href'] for i in items if
                i['bbox'][0] <= b[2] and i['bbox'][2] >= b[0] and
                i['bbox'][1] <= b[3] and i['bbox'][3] >= b[1]]
        if not urls:
            raise ValueError(f'No source assets for {city_id}')
        con.execute('CREATE OR REPLACE TEMP TABLE wanted AS SELECT id FROM read_parquet(?)', [str(folder/'hotels.parquet')])
        print(city_id, len(urls), 'assets', flush=True)
        con.execute('''CREATE OR REPLACE TEMP TABLE contacts AS
            SELECT id, phones, emails, websites, socials, to_json(brand) AS brand_json
            FROM read_parquet(?) WHERE bbox.xmin BETWEEN ? AND ?
              AND bbox.ymin BETWEEN ? AND ? AND id IN (SELECT id FROM wanted)''',
            [urls, b[0], b[2], b[1], b[3]])
        temporary = output.with_suffix('.tmp.parquet')
        con.execute('COPY contacts TO ? (FORMAT PARQUET)', [str(temporary)])
        temporary.replace(output)
        print(city_id, con.execute('SELECT count(*) FROM contacts').fetchone()[0], 'source rows', flush=True)
        (folder/'brand-contact-audit-source.json').write_text(json.dumps({
            'release':args.release, 'collection':next(l['href'] for l in collection['links'] if l['rel']=='self'),
            'assets':urls, 'purpose':'diagnostic_only',
        }, indent=2)+'\n')


if __name__ == '__main__':
    main()
