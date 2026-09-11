#!/usr/bin/env python3
"""Reproducible metadata-only Bloc C backfill, preserving rows, scores and slugs."""
import argparse
from collections import Counter
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
import duckdb
from hotelareascore.accommodation import classify_accommodation, annotate_table, LABELS
from hotelareascore.config import load_cities
from hotelareascore.slug import hotel_slug
from exclude_institutions import read_rows, backup, write_json

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('release_dir',type=Path)
    parser.add_argument('--apply',action='store_true')
    args=parser.parse_args()
    con=duckdb.connect()
    report={'release':args.release_dir.name,'cities':{},'totals':{},'mixed_operator_review':[]}
    by_id={}; by_slug={}
    for city in load_cities():
        folder=args.release_dir/city
        rows=read_rows(con,folder/'hotels.parquet')
        contacts={r['id']:r for r in read_rows(con,folder/'brand-contact-audit.parquet')}
        counts=Counter()
        for row in rows:
            brand=json.loads(contacts.get(row['id'],{}).get('brand_json') or 'null')
            row['brand_name']=((brand or {}).get('names') or {}).get('primary')
            annotation=classify_accommodation(row)
            by_id[row['id']]=annotation; by_slug[hotel_slug(row['name'],row['id'])]=annotation
            counts[annotation['accommodation_type']]+=1
            if annotation['accommodation_type_reason']=='mixed_operator_requires_property_evidence':
                report['mixed_operator_review'].append({'city':city,'id':row['id'],'name':row['name']})
        qa=json.loads((folder/'validation_report.json').read_text())
        rejected=qa.get('rejected_lodging_by_type',{})
        # Taxonomy alone can label these as nonhotel; lodging has no property evidence.
        report['cities'][city]={'total':len(rows),'types':{k:counts[k] for k in LABELS},'rejected_lodging_by_type':rejected,
          'potential_whole_home_recovery_report_only':rejected.get('holiday_rental_home',0)+rejected.get('cottage',0)+rejected.get('cabin',0),
          'unresolved_generic_lodging':rejected.get('lodging',0)}
        if args.apply:
            path=folder/'hotels.parquet';backup(path,'accommodation')
            con.execute('CREATE OR REPLACE TABLE hotels AS SELECT * FROM read_parquet(?)',[str(path)])
            cols=[d[0] for d in con.execute('SELECT * FROM hotels LIMIT 0').description]
            if 'brand_name' not in cols: con.execute('ALTER TABLE hotels ADD COLUMN brand_name VARCHAR')
            con.executemany('UPDATE hotels SET brand_name=? WHERE id=?',[(r['brand_name'],r['id']) for r in rows])
            annotate_table(con,'hotels')
            temporary=path.with_suffix('.typed.parquet');con.execute('COPY hotels TO ? (FORMAT PARQUET)',[str(temporary)]);temporary.replace(path)
    report['totals']={k:sum(c['types'][k] for c in report['cities'].values()) for k in LABELS}
    if args.apply:
        def visit(value):
            if isinstance(value,list):
                for item in value:visit(item)
            elif isinstance(value,dict):
                annotation=by_id.get(value.get('id')) or by_slug.get(value.get('slug'))
                if annotation:
                    value.update(annotation)
                    if annotation['accommodation_type']!='hotel' and value.get('publication_status')=='indexable':value['publication_status']='noindex'
                for k,child in list(value.items()):
                    if k not in ('nearby_facts','reason_codes'):visit(child)
        for directory in ('web/src/data','web/public/data'):
            for path in (ROOT/directory).glob('*.json'):
                original=path.read_text();value=json.loads(original);visit(value)
                # Preserve existing export formatting.
                formatted=json.dumps(value,ensure_ascii=False,indent=2)+'\n' if '\n ' in original else json.dumps(value,ensure_ascii=False,separators=(',',':'))+'\n'
                if json.loads(original)!=value:path.write_text(formatted)
    write_json(ROOT/'docs/reports/bloc-c-accommodation.json',report)
    lines=['# Bloc C — accommodation types','',f'Release {args.release_dir.name}; all 12 city datasets after A/B. Metadata only: no rows re-ingested or removed, no scores/slugs changed. Only `hotel` may pass the type gate; every other type remains searchable and noindex. Category is not external reception verification.','',
      '| City | Total | '+' | '.join(LABELS)+' |','|---|'+'---:|'*(len(LABELS)+1)]
    for city,c in report['cities'].items():lines.append('| '+city+' | '+str(c['total'])+' | '+' | '.join(str(c['types'][k]) for k in LABELS)+' |')
    lines+=['| **Total** | '+str(sum(report['totals'].values()))+' | '+' | '.join(str(report['totals'][k]) for k in LABELS)+' |','',
      '## Rules and limitations','',
      'Explicit whole-unit names override generic hotel taxonomy. OYO Home is whole-home; OYO alone never changes type. Blueground furnished rentals are whole-home. Sonder/Domio without explicit property evidence are unknown; the JSON companion logs these cases. Apartments without service evidence are conservatively whole-home (this describes the available evidence, not a verified operating model). Hostel, B&B, serviced apartment and aparthotel are distinct. Home/House alone never changes hotel classification. Unknown is deliberately not guessed from lodge/inn/resort alone. Guesthouse/B&B remains noindex: the supplied data cannot establish staffed reception.',
      '', 'Sources: [OYO owner case](https://www.oyorooms.com/ae/192806/), [Blueground](https://www.theblueground.com/), [Overture taxonomy](https://docs.overturemaps.org/schema/reference/places/types/taxonomy/).',
      '', '## Rejected lodging: report only, no re-ingestion','',
      'The classifier cannot establish that generic `lodging` entries are real hotels. Named/property-level review would be needed. Holiday rental home/cottage/cabin could become searchable whole homes after A/B and all ingestion QA, never automatically indexable hotels. Counts below are taxonomy-only upper bounds; they have NOT passed exclusions, deduplication or external verification.',
      '', '| City | Rejected lodging | Generic unresolved lodging | Potential whole-home candidates |','|---|---:|---:|---:|']
    for city,c in report['cities'].items():lines.append(f"| {city} | {sum(c['rejected_lodging_by_type'].values())} | {c['unresolved_generic_lodging']} | {c['potential_whole_home_recovery_report_only']} |")
    lines+=['','No automatic recovery of the large Bangkok/NY/SG generic-lodging pool is justified. Zero recovered/ingested in this block.','']
    (ROOT/'docs/reports/bloc-c-accommodation.md').write_text('\n'.join(lines))
    print(json.dumps(report['totals']))

if __name__=='__main__':main()
