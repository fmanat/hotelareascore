#!/usr/bin/env python3
"""Bloc D name-only backfill; never replace source names or canonical slugs."""
import argparse
from collections import Counter
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
import duckdb
from hotelareascore.names import present_name, unique_name_sources, scripts
from hotelareascore.config import load_cities
from hotelareascore.slug import hotel_slug
from exclude_institutions import read_rows, backup, write_json

def main():
    parser=argparse.ArgumentParser();parser.add_argument('release_dir',type=Path);parser.add_argument('--apply',action='store_true');args=parser.parse_args()
    con=duckdb.connect();by_id={};by_slug={};sources={};report={'release':args.release_dir.name,'cities':{},'non_latin_hotels':[]}
    for city in load_cities():
        folder=args.release_dir/city
        raw=read_rows(con,folder/'source-names.parquet');source={r['id']:r['names_json'] for r in raw}
        hotels=read_rows(con,folder/'hotels.parquet')
        pois=con.execute('SELECT id,name FROM read_parquet(?) WHERE name IN (SELECT name FROM read_parquet(?))',[str(folder/'pois.parquet'),str(folder/'nearby_facts.parquet')]).fetchall()
        # Include missing source records in agreement checking, not just fetched ones.
        sources[city]=unique_name_sources([(r['name'],source.get(r['id'])) for r in hotels]+[(name,source.get(pid)) for pid,name in pois])
        counts=Counter();methods=Counter();script_counts=Counter()
        for r in hotels:
            got=present_name(r['name'],source.get(r['id']));by_id[r['id']]=got;by_slug[hotel_slug(r['name'],r['id'])]=got
            counts['hotels']+=1;methods[got['name_method']]+=1
            if r['id'] not in source:counts['source_missing']+=1
            if scripts(r['name'])-{'LATIN'}:
                counts['non_latin_before']+=1;script_counts['+'.join(sorted(scripts(r['name'])))]+=1
                if got['name_index_eligible']:
                    counts['name_gate_unlocked']+=1
                    if r['accommodation_type']=='hotel':counts['hotel_type_and_name_unlocked']+=1
                report['non_latin_hotels'].append({'city':city,'id':r['id'],'name':r['name'],'accommodation_type':r['accommodation_type'],**got})
            if not got.get('name_index_eligible',True):counts['name_ineligible']+=1
        factrows=read_rows(con,folder/'nearby_facts.parquet');fm=Counter()
        for f in factrows:fm[present_name(f['name'],sources[city].get(f['name']))['name_method']]+=1
        report['cities'][city]={'counts':dict(counts),'name_methods':dict(methods),'scripts':dict(script_counts),'why_fact_occurrences':len(factrows),'why_fact_methods':dict(fm),'source_rows':len(raw)}
        if args.apply:
            for filename in ('hotels.parquet','pois.parquet'):
                path=folder/filename;backup(path,'names')
                cols=[r[0] for r in con.execute('DESCRIBE SELECT * FROM read_parquet(?)',[str(path)]).fetchall()]
                select='p.*'+(' EXCLUDE(names_json)' if 'names_json' in cols else '')
                con.execute(f'CREATE OR REPLACE TEMP TABLE enriched AS SELECT {select}, s.names_json FROM read_parquet(?) p LEFT JOIN read_parquet(?) s USING(id)',[str(path),str(folder/'source-names.parquet')])
                tmp=path.with_suffix('.names.parquet');con.execute('COPY enriched TO ? (FORMAT PARQUET)',[str(tmp)]);tmp.replace(path)
    report['totals']={key:sum(c['counts'].get(key,0) for c in report['cities'].values()) for key in ('hotels','source_missing','non_latin_before','name_gate_unlocked','hotel_type_and_name_unlocked','name_ineligible')}
    if args.apply:
        def visit(value,city=None):
            if isinstance(value,list):
                for item in value:visit(item,city)
            elif isinstance(value,dict):
                city=value.get('city_id',city)
                if isinstance(value.get('name'),str):
                    got=by_id.get(value.get('id')) or by_slug.get(value.get('slug')) or present_name(value['name'],sources.get(city,{}).get(value['name']))
                    if "rank" in value and "category" in value:
                        got={k:v for k,v in got.items() if k in ("display_name","name_method") and got["display_name"]!=value["name"]}
                    value.update(got)
                    if not got.get('name_index_eligible',True) and value.get('publication_status')=='indexable':value['publication_status']='noindex'
                for k,child in list(value.items()):
                    if k!='reason_codes':visit(child,city)
        for directory in ('web/src/data','web/public/data'):
            for path in (ROOT/directory).glob('*.json'):
                original=path.read_text();value=json.loads(original);visit(value)
                if directory=='web/public/data' and isinstance(value,list):
                    for row in value:
                        for key in list(row):
                            if key.startswith('name_') or (key.startswith('accommodation_type_') and key!='accommodation_type_label'):row.pop(key)
                        if row.get('display_name')==row.get('name'):row.pop('display_name',None)
                def compact_facts(obj):
                    if isinstance(obj,list):
                        for item in obj:compact_facts(item)
                    elif isinstance(obj,dict):
                        if 'rank' in obj and 'category' in obj:
                            for key in list(obj):
                                if key.startswith('name_') and key!='name_method':obj.pop(key)
                            if obj.get('display_name')==obj.get('name'):
                                obj.pop('display_name',None);obj.pop('name_method',None)
                        for child in obj.values():compact_facts(child)
                compact_facts(value)
                formatted=json.dumps(value,ensure_ascii=False,indent=2)+'\n' if '\n ' in original else json.dumps(value,ensure_ascii=False,separators=(',',':'))+'\n'
                if json.loads(original)!=value:path.write_text(formatted)
    write_json(ROOT/'docs/reports/bloc-d-names.json',report)
    print(json.dumps(report['totals']))
if __name__=='__main__':main()
