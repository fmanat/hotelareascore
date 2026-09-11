#!/usr/bin/env python3
"""Fetch source names for retained hotels and named why-fact POIs; no re-ingestion."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from hotelareascore.config import ETL_DIR, load_cities
from hotelareascore import overture
from audit_brand_contacts import fetch

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--release',required=True)
    args=parser.parse_args()
    catalog=fetch('https://stac.overturemaps.org/catalog.json')
    release=fetch(next(l['href'] for l in catalog['links'] if args.release in l['href']))
    places=fetch(next(l['href'] for l in release['links'] if l.get('title')=='places'))
    collection=fetch(next(l['href'] for l in places['links'] if l['rel']=='child'))
    with ThreadPoolExecutor(max_workers=4) as pool:
        items=list(pool.map(fetch,[l['href'] for l in collection['links'] if l['rel']=='item']))
    con=overture.connect();con.execute('SET threads=4')
    for city_id,city in load_cities().items():
        folder=ETL_DIR/args.release/city_id;out=folder/'source-names.parquet'
        if out.exists():print(city_id,'cached',flush=True);continue
        b=city.bbox
        urls=[i['assets']['aws']['href'] for i in items if i['bbox'][0]<=b[2] and i['bbox'][2]>=b[0] and i['bbox'][1]<=b[3] and i['bbox'][3]>=b[1]]
        if not urls:raise ValueError(f'No source assets for {city_id}')
        con.execute('''CREATE OR REPLACE TEMP TABLE wanted AS
          SELECT id FROM read_parquet(?) UNION
          SELECT id FROM read_parquet(?) WHERE name IN (SELECT DISTINCT name FROM read_parquet(?))''',
          [str(folder/'hotels.parquet'),str(folder/'pois.parquet'),str(folder/'nearby_facts.parquet')])
        print(city_id,'wanted',con.execute('SELECT count(*) FROM wanted').fetchone()[0],flush=True)
        con.execute('''CREATE OR REPLACE TEMP TABLE source_names AS SELECT id, names.primary AS name, to_json(names) AS names_json
          FROM read_parquet(?) WHERE bbox.xmin BETWEEN ? AND ? AND bbox.ymin BETWEEN ? AND ? AND id IN (SELECT id FROM wanted)''',
          [urls,b[0],b[2],b[1],b[3]])
        tmp=out.with_suffix('.tmp.parquet');con.execute('COPY source_names TO ? (FORMAT PARQUET)',[str(tmp)]);tmp.replace(out)
        (folder/'source-names-provenance.json').write_text(json.dumps({'release':args.release,'assets':urls,'purpose':'name_display_only','rows':con.execute('SELECT count(*) FROM source_names').fetchone()[0]},indent=2)+'\n')
        print(city_id,'written',flush=True)
if __name__=='__main__':main()
