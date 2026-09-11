"""Bloc B: property identity boundaries, every barrier, and inert diagnostics."""
import importlib.util
import json
from pathlib import Path
import sys

import duckdb
import pytest

from hotelareascore import ingest, overture, publication, webdata, validate
from hotelareascore.brands import brand_matches, config, quarantined_records
from hotelareascore.config import get_city
from hotelareascore.entity_qa import is_likely_non_hotel
from test_institutions import node

ROOT = Path(__file__).resolve().parents[1]
POSITIVE = [
    'ALL Accor', 'ALL', 'Accor Live Limitless', 'ALL – Accor Live Limitless',
    'Marriott Bonvoy', 'Marriott Bonvoy Barcelona', 'World of Hyatt',
    'IHG One Rewards', 'Hilton Honors', 'Hilton HHonors', 'Wyndham Rewards',
    'Choice Privileges', 'Club Marriott', 'Premier Club Rewards London',
    'ＡＬＬ　Ａｃｃｏｒ', 'Hilton Corporate Office', 'Hyatt Regional Office',
    'Marriott HQ', 'Hotel Brand Headquarters', 'Kempinski Global Sales Office',
    'Hilton Reservation Worldwide', 'Accor Reservation Services',
    'Browns Hotel Group', 'Pan Pacific Hotels Group', 'InterContinental Hotels Group',
    'Accor Hotels', 'Wyndham Hotels & Resorts', 'Marriott International Inc.',
    'Hilton Paris — siège social', 'Accor bureau commercial',
    'Hilton sede centrale', 'Hyatt ufficio vendite',
    'Marriott oficinas centrales', 'Accor oficina de ventas',
    'Hilton seu central', 'Hyatt oficina de vendes',
    'Accor escritório central', 'Hilton escritório de vendas',
    'Marriott hoofdkantoor', 'Accor verkoopkantoor',
    'ホテル東京本社', 'ホテル東京営業所', '東京ホテル予約センター',
    '万豪酒店总部', '希爾頓酒店總部', '酒店预订中心',
    'โรงแรม สำนักงานใหญ่', 'โรงแรมสำนักงานขาย',
    'فندق المقر الرئيسي', 'فندق مكتب المبيعات',
    'Hotel ibu pejabat', 'Hotel pejabat jualan',
    'விடுதி தலைமை அலுவலகம்', 'விடுதி விற்பனை அலுவலகம்',
    'Hotel Maple by Marriott Corporate Office',
    'Hotel Marriott Bonvoy', 'The Official Hotel World of Hyatt',
    '雅高心悦界', '万豪旅享家', '凯悦天地', '希尔顿荣誉客会',
    '洲际优悦会', '温德姆奖赏计划', 'ヒルトン・オナーズ',
    'ワールド オブ ハイアット', 'マリオット ボンヴォイ',
    'Groupe hôtelier Exemple', 'Grupo hotelero Ejemplo', 'Grup hoteler Exemple',
    'Gruppo alberghiero Esempio', 'Grupo hoteleiro Exemplo', 'Voorbeeld Hotelgroep',
    'مجموعة فنادق', 'Kumpulan Hotel Contoh', 'ஹோட்டல் குழுமம்',
    'H10 Hotels', 'Minor Hotels', 'Eurostars Hotel Company', 'Frasers Hospitality',
]
NEGATIVE = [
    'Marriott', 'Hilton', 'Hyatt', 'Wyndham Hotel', 'Choice Apartments',
    'Home Hotel', 'Home House', 'Youth Hostel', 'International Budget Hostel',
    'Hotel MidMost Barcelona by Majestic Hotel Group',
    'Hotel Midas Roma, a member of Barceló Hotel Group',
    'Windsor Suites Bangkok, Managed By Accor',
    '8 On Claymore Singapore - Managed By Accor',
    'The Creekside Hotel Dubai an Accor Hotel',
    'Hotel Maple, Marriott Bonvoy', 'Hotel Maple, World of Hyatt',
    'Hotel Maple – ALL Accor', 'Maple Apartments by Marriott Bonvoy',
    'Old Post Office Hotel', 'The Office Hotel', 'Vicoloft Sales',
    'The Bell Office Suites', 'Armed Forces Officers Club And Hotel',
    'Hotel Wing International Shimbashi Onarimon', 'Hilton International Hotel Dubai',
    'All Seasons Hotel', 'ALL INN', 'Royal Group Hotel', 'House of Choice',
    'Holiday Inn Newark International Airport by IHG',
]


@pytest.mark.parametrize('name', POSITIVE)
def test_non_establishment_overrides_brand_allowances(name):
    assert brand_matches(name)
    assert is_likely_non_hotel(name)


@pytest.mark.parametrize('name', NEGATIVE)
def test_property_names_and_affiliations_are_preserved(name):
    assert not brand_matches(name)


@pytest.mark.parametrize('h', config()['reviewed_hotels'], ids=lambda h:h['name'])
def test_reviewed_property_alias_is_exact_and_cannot_allow_an_office(h):
    assert brand_matches(h['name'])
    assert not brand_matches(h['name'],h['id'])
    assert not brand_matches(h['name'],h['slug'])
    assert brand_matches(h['name'],'other')
    assert brand_matches(h['name']+' Corporate Office',h['id'])


def test_ingestion_excludes_before_dedupe_and_logs(monkeypatch,tmp_path):
    con=duckdb.connect()
    con.execute('CREATE TABLE source (id VARCHAR,name VARCHAR,lat DOUBLE,lon DOUBLE,confidence DOUBLE,n_sources INTEGER,taxonomy_primary VARCHAR)')
    con.executemany('INSERT INTO source VALUES (?,?,48.8,2.3,0.9,2,?)',[
        ('program','ALL Accor','hotel'),('office','Hilton Corporate Office','hotel'),
        ('good','Home House Hostel','hostel')])
    monkeypatch.setattr(overture,'connect',lambda:con)
    monkeypatch.setattr(overture,'check_schema',lambda *a:None)
    monkeypatch.setattr(ingest,'_hotels_raw_sql',lambda *a:'SELECT * FROM source')
    for name in ('_poi_sql','_segment_sql','_green_spaces_sql'):
        monkeypatch.setattr(ingest,name,lambda *a:'SELECT 1 AS id')
    monkeypatch.setattr(ingest,'city_dir',lambda *a:tmp_path)
    result=ingest.ingest_city('paris',overture.Release('fixture'))
    assert con.execute('SELECT id FROM read_parquet(?)',[str(tmp_path/'hotels.parquet')]).fetchall()==[('good',)]
    assert result['brand_excluded_count']==2
    assert {r['id'] for r in result['brand_exclusions']}=={'program','office'}
    assert all(r['matches'] and r['action']=='exclude_pending_review' for r in result['brand_exclusions'])


@pytest.mark.parametrize('status',['draft','noindex','indexable'])
def test_publication_blocks_even_non_indexable_pages(tmp_path,status):
    with publication.connect(tmp_path/'pub.sqlite') as con:
        with pytest.raises(ValueError):
            publication.set_status(con,'hotel','x',status,'test','test',hotel_name='ALL Accor')
        publication.set_status(con,'hotel','x','retired','excluded','test',hotel_name='ALL Accor')


def test_stale_etl_is_rejected_before_missing_scores(tmp_path,monkeypatch):
    con=duckdb.connect()
    con.execute("COPY (SELECT 'x' AS id,'ALL Accor' AS name) TO ? (FORMAT PARQUET)",[str(tmp_path/'hotels.parquet')])
    with pytest.raises(ValueError,match='purge and audit'):
        webdata._fetch_hotels(con,tmp_path)


def test_validation_rejects_stale_dataset_before_scores(tmp_path,monkeypatch):
    folder=tmp_path/'fixture/paris'
    folder.mkdir(parents=True)
    con=duckdb.connect()
    con.execute("COPY (SELECT 'x' AS id,'Marriott Bonvoy' AS name) TO ? (FORMAT PARQUET)",[str(folder/'hotels.parquet')])
    monkeypatch.setattr(validate,'ETL_DIR',tmp_path)
    monkeypatch.setattr(overture,'connect',lambda:con)
    with pytest.raises(ValueError,match='purge and audit'):
        validate.validate_city('paris',overture.Release('fixture'))


def test_city_aggregate_rejects_stale_non_static_hotel(tmp_path,monkeypatch):
    folder=tmp_path/'fixture/paris'
    folder.mkdir(parents=True)
    con=duckdb.connect()
    con.execute("COPY (SELECT 'x' AS id,'ALL Accor' AS name) TO ? (FORMAT PARQUET)",[str(folder/'hotels.parquet')])
    (folder/'hotel_scores.parquet').touch()
    (folder/'city_baseline.json').write_text('{}')
    monkeypatch.setattr(webdata,'ETL_DIR',tmp_path)
    monkeypatch.setattr(overture,'connect',lambda:con)
    with pytest.raises(ValueError,match='city aggregate paris'):
        webdata._city_page_aggregate('paris',overture.Release('fixture'),set())


def test_python_node_parity_for_every_rule_exception_and_quarantine():
    cases=[[n,None] for n in POSITIVE+NEGATIVE]
    cases += [[t,None] for r in config()['rules'] for t in r['terms']]
    cases += [[h['name'],key] for h in config()['reviewed_hotels'] for key in (h['id'],h['slug'],'wrong')]
    cases += [[n,key] for key in quarantined_records() for n in (None,'Renamed Hotel')]
    result=node("import {brandMatches} from './web/scripts/brand-guard.mjs'; import fs from 'node:fs'; console.log(JSON.stringify(JSON.parse(fs.readFileSync(0,'utf8')).map(([n,id])=>brandMatches(n,id))));",input=json.dumps(cases))
    assert result.returncode==0,result.stderr
    assert json.loads(result.stdout)==[brand_matches(n,key) for n,key in cases]


@pytest.mark.parametrize('file,record',[
    ('src/data/hotels-paris.json',{'id':'x','name':'ALL Accor','publication_status':'noindex'}),
    ('public/data/search-index-barcelona-a.json',{'name':'Marriott Bonvoy'}),
    ('src/data/city-pages.json',{'representative_hotels':[{'name':'ALL Accor','slug':None}]}),
    ('src/data/hotels-london.json',{'name':'Good Hotel','comparable':[{'name':'Hilton Honors'}]}),
])
def test_build_blocks_stale_exports(tmp_path,file,record):
    (tmp_path/'src/data').mkdir(parents=True)
    (tmp_path/'public/data').mkdir(parents=True)
    (tmp_path/file).write_text(json.dumps([record]))
    result=node(f"import {{checkBrandExports}} from './web/scripts/brand-guard.mjs'; checkBrandExports({json.dumps(str(tmp_path))});")
    assert result.returncode!=0
    assert 'Non-establishment brand candidates' in result.stderr


def test_pinned_ids_are_rejected_without_or_with_changed_name(tmp_path):
    assert quarantined_records()
    with publication.connect(tmp_path/'pub.sqlite') as con:
        for key in quarantined_records():
            assert brand_matches(None,key)
            assert brand_matches('Renamed Hotel',key)
            with pytest.raises(ValueError):
                publication.set_status(con,'hotel',key,'noindex','test','test')


def audit_module():
    sys.path.insert(0,str(ROOT/'scripts'))
    spec=importlib.util.spec_from_file_location('exclude_brands',ROOT/'scripts/exclude_brands.py')
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_generic_signal_is_tri_state_and_never_activates_exclusion():
    module=audit_module()
    rows=[{'id':str(i),'name':n,'lon':2.3,'lat':48.8,'address_country':'GB','address_freeform':'1 Main St'}
          for i,n in enumerate(['Hilton North','Hilton South','Independent Hotel'])]
    absent={f:['', ' ', None] for f in ('phones','emails','websites','socials')}
    contacts={'0':absent,'1':{**absent,'websites':['https://example.com']}}
    counts=module.attribute_diagnostic(rows,get_city('paris'),contacts)['counts']
    assert (counts['contact_unknown'],counts['contact_absent'],counts['contact_present'])==(1,1,1)
    assert counts['same_group_duplicate_coordinates']==2
    assert counts['all_three_confirmed']==1
    assert all(not brand_matches(r['name'],r['id']) for r in rows)
    # Missing address is NOT an incoherent address; unknown group is NOT a match.
    rows=[{**r,'address_country':None,'address_freeform':None} for r in rows]
    counts=module.attribute_diagnostic(rows,get_city('paris'),{})['counts']
    assert counts['address_incoherent']==0 and counts['address_incomplete']==3
    assert counts['all_three_confirmed']==0


def test_committed_exports_are_clean():
    result=node("import {checkBrandExports} from './web/scripts/brand-guard.mjs'; checkBrandExports('./web');")
    assert result.returncode==0,result.stderr
