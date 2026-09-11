"""Bloc A: independent regression specimens, ingestion and stale-build barriers."""
import json
import shutil
import subprocess
from pathlib import Path

import duckdb
import pytest

from hotelareascore import ingest, overture, publication, webdata
from hotelareascore.entity_qa import is_likely_non_hotel
from hotelareascore.institutions import institution_matches, reviewed_hotels, quarantined_records, RULES_PATH

ROOT = Path(__file__).resolve().parents[1]
# Synthetic names exercise institution semantics; not assertions about real venues.
POSITIVE = [
    ("en", "Singapore Boys' Home", "child_care"),
    ("en", "Singapore Girls’ Home", "child_care"),
    ("en", "St Mary's Children’s Home", "child_care"),
    ("en", "Hilton Nursing Home", "elder_care"),
    ("en", "The Lodge Care Home", "elder_care"),
    ("en", "Sunrise Retirement Home", "elder_care"),
    ("en", "East Halfway House", "rehabilitation"),
    ("en", "Hotel Youth Detention Centre", "detention"),
    ("en", "Central Correctional Center", "detention"),
    ("en", "Juvenile Remand Centre", "detention"),
    ("en", "House Rehabilitation Centre", "rehabilitation"),
    ("en", "Drug Rehabilitation Center", "rehabilitation"),
    ("en", "Homeless Shelter Hostel", "shelter"),
    ("en", "Women's Refuge", "shelter"),
    ("en", "The Orphanage", "child_care"),
    ("en", "Young Persons Group Home", "child_care"),
    ("en", "HM Prison", "detention"),
    ("en", "Psychiatric Residential Home", "medical_residential"),
    ("en", "Residential Medical Centre", "medical_residential"),
    ("en", "Ｓｉｎｇａｐｏｒｅ Ｂｏｙｓ＇ Ｈｏｍｅ", "child_care"),
    ("en", "Girls’\u00a0Home", "child_care"),
    ("en", "NURSING-HOME", "elder_care"),
    ("en", "Singapore Boys' Hostel", "child_care"),
    ("en", "Andrew and Grace Home", "child_care"),
    ("en", "Ronald McDonald House Moorfields", "medical_residential"),
    ("en", "Care Homes Ltd", "elder_care"),
    ("fr", "Maison d’enfants Saint-Pierre", "child_care"),
    ("fr", "EHPAD Sainte Monique", "elder_care"),
    ("fr", "Maison d’arrêt de Paris", "detention"),
    ("fr", "Centre de rééducation", "rehabilitation"),
    ("fr", "Centre d’hébergement d’urgence", "shelter"),
    ("fr", "Résidence médicalisée", "medical_residential"),
    ("it", "Casa famiglia Aurora", "child_care"),
    ("it", "Villa Rigacci Casa Di Riposo", "elder_care"),
    ("it", "Casa circondariale Regina", "detention"),
    ("it", "Centro di riabilitazione", "rehabilitation"),
    ("it", "Centro di accoglienza", "shelter"),
    ("it", "Residenza sanitaria", "medical_residential"),
    ("es", "Hogar de niños", "child_care"),
    ("es", "Residencia para Mayores Ballesol Mirasierra", "elder_care"),
    ("es", "Centro penitenciario", "detention"),
    ("es", "Centro de rehabilitación", "rehabilitation"),
    ("es", "Albergue social", "shelter"),
    ("es", "Hospital psiquiátrico", "medical_residential"),
    ("ca", "Centre de menors", "child_care"),
    ("ca", "Residència de gent gran", "elder_care"),
    ("ca", "Centre penitenciari", "detention"),
    ("ca", "Centre de rehabilitació", "rehabilitation"),
    ("ca", "Centre d’acollida", "shelter"),
    ("ca", "Centre psiquiàtric", "medical_residential"),
    ("nl", "Het Kindertehuis", "child_care"),
    ("nl", "Woonzorgcentrum Amsterdam", "elder_care"),
    ("nl", "Huis van bewaring", "detention"),
    ("nl", "Revalidatiecentrum Amsterdam", "rehabilitation"),
    ("nl", "Daklozenopvang Amsterdam", "shelter"),
    ("nl", "Beschermd wonen", "medical_residential"),
    ("pt", "Lar de crianças", "child_care"),
    ("pt", "Lar de idosos Lisboa", "elder_care"),
    ("pt", "Estabelecimento prisional", "detention"),
    ("pt", "Centro de reabilitação", "rehabilitation"),
    ("pt", "Centro de acolhimento", "shelter"),
    ("pt", "Unidade de cuidados continuados", "medical_residential"),
    ("ja", "東京児童養護施設", "child_care"),
    ("ja", "東京有料老人ホーム", "elder_care"),
    ("ja", "東京少年院", "detention"),
    ("ja", "東京更生保護施設", "rehabilitation"),
    ("ja", "東京婦人保護施設", "shelter"),
    ("ja", "東京グループホーム", "medical_residential"),
    ("zh", "新加坡孤儿院", "child_care"),
    ("zh", "新加坡養老院", "elder_care"),
    ("zh", "新加坡少年感化院", "detention"),
    ("zh", "新加坡戒毒中心", "rehabilitation"),
    ("zh", "新加坡庇護所", "shelter"),
    ("zh", "新加坡精神病院", "medical_residential"),
    ("th", "บ้านเด็กกำพร้ากรุงเทพ", "child_care"),
    ("th", "บ้านพักผู้สูงอายุ สยามเกษียณ", "elder_care"),
    ("th", "เรือนจำกรุงเทพ", "detention"),
    ("th", "ศูนย์ฟื้นฟูสมรรถภาพกรุงเทพ", "rehabilitation"),
    ("th", "บ้านพักฉุกเฉินกรุงเทพ", "shelter"),
    ("th", "โรงพยาบาลจิตเวชกรุงเทพ", "medical_residential"),
    ("ar", "دار الأيتام دبي", "child_care"),
    ("ar", "دار رعاية المسنين دبي", "elder_care"),
    ("ar", "مركز احتجاز دبي", "detention"),
    ("ar", "مركز إعادة التأهيل دبي", "rehabilitation"),
    ("ar", "دار إيواء دبي", "shelter"),
    ("ar", "مستشفى للأمراض النفسية دبي", "medical_residential"),
    ("ms", "Rumah Anak Yatim Singapura", "child_care"),
    ("ms", "Pusat Jagaan Warga Emas", "elder_care"),
    ("ms", "Pusat Tahanan Singapura", "detention"),
    ("ms", "Pusat Pemulihan Singapura", "rehabilitation"),
    ("ms", "Rumah Perlindungan Singapura", "shelter"),
    ("ms", "Hospital Psikiatri Singapura", "medical_residential"),
    ("ta", "சிறுவர் இல்லம்", "child_care"),
    ("ta", "முதியோர் காப்பகம்", "elder_care"),
    ("ta", "சிறைச்சாலை", "detention"),
    ("ta", "மறுவாழ்வு மையம்", "rehabilitation"),
    ("ta", "பாதுகாப்பு இல்லம்", "shelter"),
    ("ta", "மனநல மருத்துவமனை", "medical_residential"),
]
NEGATIVE = [
    "Home Hotel", "Home House", "Cedar House", "Soho House London",
    "Homewood Suites by Hilton", "Home2 Suites by Hilton", "The Student Hotel",
    "Youth Hostel", "City Stay Hostel Ltd", "YHA London Central",
    "Auberge de jeunesse Paris", "Ostello della Gioventù", "Albergue juvenil",
    "Alberg juvenil Barcelona", "Jeugdherberg Amsterdam", "Pousada de juventude",
    "東京ユースホステル", "บ้านพักนักท่องเที่ยว", "青年旅舍", "فندق دبي",
    "Rumah Tumpangan", "விடுதி", "Guest House Tokyo", "Hotel Home Sweet Home",
    "OYO 985 Home 1BR Lake City Tower, JLT", "The Halfway Inn", "Shelterwood Hotel",
    "Carcereccio Hotel", "Hotel Home Away From Home", "Children's Holiday Hotel",
]


@pytest.mark.parametrize('language,name,reason', POSITIVE)
def test_institution_is_excluded_despite_lodging_or_brand(language, name, reason):
    matches = institution_matches(name)
    assert any(m['language'] == language and m['reason'] == reason for m in matches)
    assert is_likely_non_hotel(name)


@pytest.mark.parametrize('name', NEGATIVE)
def test_tourist_hostels_and_home_house_names_survive(name):
    assert not institution_matches(name)
    assert not is_likely_non_hotel(name)


@pytest.mark.parametrize('hotel', reviewed_hotels(), ids=lambda h: h['name'])
def test_reviewed_collision_requires_exact_identity_and_name(hotel):
    assert institution_matches(hotel['name'])
    assert not institution_matches(hotel['name'], hotel['id'])
    assert not institution_matches(hotel['name'], hotel['slug'])
    assert institution_matches(hotel['name'], 'unreviewed-id')
    assert institution_matches(hotel['name'] + ' Nursing Home', hotel['id'])


def test_quarantined_ids_cannot_return_after_renaming_or_without_a_name(tmp_path):
    for key in quarantined_records():
        assert institution_matches('Renamed Tourist Hotel', key)
        assert institution_matches(None, key)
        assert is_likely_non_hotel(None, key)
        with publication.connect(tmp_path/'pub.sqlite') as con:
            with pytest.raises(ValueError):
                publication.set_status(con, 'hotel', key, 'draft', 'test', 'test')


def test_ingest_excludes_before_dedupe_and_logs_every_reason(monkeypatch, tmp_path):
    con = duckdb.connect()
    con.execute('CREATE TABLE source (id VARCHAR, name VARCHAR, lat DOUBLE, lon DOUBLE, confidence DOUBLE, n_sources INTEGER, taxonomy_primary VARCHAR)')
    con.executemany('INSERT INTO source VALUES (?, ?, 1.3, 103.8, 0.9, 2, ?)', [
        ('bad', "Singapore Boys' Home", 'hotel'),
        ('brand', 'Hilton Nursing Home', 'hotel'),
        ('good', 'Home House Hostel', 'hostel'),
    ])
    monkeypatch.setattr(overture, 'connect', lambda: con)
    monkeypatch.setattr(overture, 'check_schema', lambda *a: None)
    monkeypatch.setattr(ingest, '_hotels_raw_sql', lambda *a: 'SELECT * FROM source')
    for name in ('_poi_sql', '_segment_sql', '_green_spaces_sql'):
        monkeypatch.setattr(ingest, name, lambda *a: 'SELECT 1 AS id')
    monkeypatch.setattr(ingest, 'city_dir', lambda *a: tmp_path)
    result = ingest.ingest_city('singapore', overture.Release('fixture'))
    assert con.execute('SELECT id FROM read_parquet(?)', [str(tmp_path/'hotels.parquet')]).fetchall() == [('good',)]
    assert result['institution_excluded_count'] == 2
    assert {r['id'] for r in result['institution_exclusions']} == {'bad', 'brand'}
    assert all(r['matches'] and r['action'] == 'exclude_pending_review' for r in result['institution_exclusions'])


def test_stale_etl_without_scores_cannot_be_exported(tmp_path):
    con = duckdb.connect()
    con.execute("COPY (SELECT 'bad' AS id, 'Hilton Nursing Home' AS name) TO ? (FORMAT PARQUET)", [str(tmp_path/'hotels.parquet')])
    with pytest.raises(ValueError, match='purge and audit'):
        webdata._fetch_hotels(con, tmp_path)


@pytest.mark.parametrize('status', ['draft', 'noindex', 'indexable'])
def test_publication_rejects_institutions_even_when_not_indexed(tmp_path, status):
    with publication.connect(tmp_path/'pub.sqlite') as con:
        with pytest.raises(ValueError):
            publication.set_status(con, 'hotel', 'bad', status, 'test', 'test', hotel_name="Singapore Boys' Home")
        publication.set_status(con, 'hotel', 'bad', 'retired', 'institution excluded', 'test', hotel_name="Singapore Boys' Home")


def node(script, *, input=None):
    if not shutil.which('node'):
        pytest.skip('Node required for cross-language build guard tests; installed in CI')
    return subprocess.run(['node', '--input-type=module', '-e', script], input=input, capture_output=True, text=True, cwd=ROOT)


def test_python_and_build_guard_agree_on_regression_set_and_all_literals():
    data = json.loads(RULES_PATH.read_text())
    cases = [[name, None] for _, name, _ in POSITIVE] + [[name, None] for name in NEGATIVE]
    cases += [[t, None] for r in data['rules'] for t in r['terms']]
    cases += [[h['name'], key] for h in reviewed_hotels() for key in (h['id'], h['slug'], 'wrong')]
    cases += [[name, key] for key in quarantined_records() for name in (None, 'Renamed Tourist Hotel')]
    result = node("import {institutionMatches} from './web/scripts/institution-guard.mjs'; import fs from 'node:fs'; console.log(JSON.stringify(JSON.parse(fs.readFileSync(0,'utf8')).map(([n,id])=>institutionMatches(n,id))));", input=json.dumps(cases))
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout) == [institution_matches(n, i) for n, i in cases]


@pytest.mark.parametrize('file,record', [
    ('src/data/hotels-singapore.json', {'id':'bad', 'name':"Singapore Boys' Home", 'publication_status':'noindex'}),
    ('public/data/search-index-singapore-a.json', {'id':'bad', 'name':'Hilton Nursing Home'}),
    ('src/data/city-pages.json', {'representative_hotels':[{'slug':'bad', 'name':'EHPAD Sainte Monique'}]}),
    ('src/data/hotels-london.json', {'name':'Safe Hotel', 'comparable':[{'slug':'bad', 'name':'Nursing Home'}]}),
])
def test_build_blocks_all_stale_page_and_search_paths(tmp_path, file, record):
    (tmp_path/'src/data').mkdir(parents=True)
    (tmp_path/'public/data').mkdir(parents=True)
    (tmp_path/file).write_text(json.dumps([record]))
    result = node(f"import {{checkInstitutionExports}} from './web/scripts/institution-guard.mjs'; checkInstitutionExports({json.dumps(str(tmp_path))});")
    assert result.returncode != 0
    assert 'Institution candidates' in result.stderr


def test_committed_exports_cannot_ship_quarantined_records():
    result = node("import {checkInstitutionExports} from './web/scripts/institution-guard.mjs'; checkInstitutionExports('./web');")
    assert result.returncode == 0, result.stderr


def test_purge_removes_null_slug_city_references_and_preserves_tourist_data(tmp_path, monkeypatch):
    import importlib.util
    spec = importlib.util.spec_from_file_location('exclude_institutions', ROOT/'scripts/exclude_institutions.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    monkeypatch.setattr(module, 'load_cities', lambda: {'singapore': None})
    web = tmp_path/'web'
    (web/'src/data').mkdir(parents=True)
    (web/'public/data').mkdir(parents=True)
    (web/'src/data/city-baselines.json').write_text('{}')
    (web/'src/data/city-pages.json').write_text(json.dumps([{
        'city_id':'singapore', 'n_hotels':2,
        'dimensions':{d:{'mean':0,'median':0} for d in module.DIMENSIONS},
        'representative_hotels':[{'name':"Singapore Boys' Home", 'slug':None}, {'name':'Home House Hostel', 'slug':'safe'}],
    }]))
    (web/'public/data/search-index.json').write_text(json.dumps([{'slug':'bad','name':"Singapore Boys' Home"}, {'slug':'safe','name':'Home House Hostel','score':42}]))
    release = tmp_path/'release'
    (release/'singapore').mkdir(parents=True)
    baseline = {'n_hotels':1, **{f'{d}_{kind}':42 for d in module.DIMENSIONS for kind in ('mean','median')}}
    (release/'singapore/city_baseline.json').write_text(json.dumps(baseline))
    result = {'cities':{'singapore':{'excluded':1}},'exclusions':[{'id':'bad-id','slug':'bad'}]}
    module.purge_web(result, release, web)
    assert json.loads((web/'public/data/search-index.json').read_text()) == [{'slug':'safe','name':'Home House Hostel','score':42}]
    page = json.loads((web/'src/data/city-pages.json').read_text())[0]
    assert page['representative_hotels'] == [{'name':'Home House Hostel','slug':'safe'}]
    assert page['n_hotels'] == 1
