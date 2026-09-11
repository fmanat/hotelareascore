import pytest
from hotelareascore.names import present_name, unique_name_sources
from hotelareascore.slug import hotel_slug
from hotelareascore import publication

def test_source_alternative_precedes_romanizer_and_preserves_original():
    name='ホテルCOCO'
    got=present_name(name,{'common':{'fr':'Coco Hôtel','en':'Hotel Coco'}})
    assert got['display_name']=='Hotel Coco (ホテルCOCO)'
    assert got['name_index_eligible'] and got['name_method']=='source_alternative_latin'
    assert hotel_slug(name,'abcdef12345678')=='coco-12345678'

@pytest.mark.parametrize('name',['โรงแรม','埼玉県','東京ホテル','فندق','מלון','होटल','酒店 Hotel','1234',''])
def test_unreliable_or_missing_name_stays_original_and_ineligible(name):
    got=present_name(name)
    assert got['display_name']==name and not got['name_index_eligible']

@pytest.mark.parametrize('name',['ホテルココ','さいたま','Отель Москва','Ξενοδοχείο','호텔'])
def test_supported_phonetic_scripts_are_marked_romanized(name):
    got=present_name(name)
    assert got['name_method']=='transliteration_approximate'
    assert got['display_name'].endswith(f'({name})')
    assert got['name_index_eligible'] and got['name_latin'].isascii()

def test_latin_diacritics_are_not_translated_or_stripped():
    got=present_name('Hôtel Le Méridien')
    assert got['display_name']=='Hôtel Le Méridien' and got['name_index_eligible']

def test_historical_aliases_and_ambiguous_poi_names_are_not_used():
    assert not present_name('東京',{'rules':[{'variant':'historical','value':'Old Tokyo'}]})['name_index_eligible']
    assert unique_name_sources([('東京',{'common':{'en':'Tokyo'}}),('東京',{'common':{'en':'Other Tokyo'}})])=={}
    assert unique_name_sources([('東京',{'common':{'en':'Tokyo'}}),('東京',None)])=={}

def test_publication_needs_explicit_name_gate(tmp_path):
    with publication.connect(tmp_path/'pub.sqlite') as con:
        with pytest.raises(ValueError,match='Latin name'):
            publication.set_status(con,'hotel','test','indexable','test','test',accommodation_type='hotel')
