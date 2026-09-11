import pytest
from hotelareascore.accommodation import classify_accommodation, annotate_table
from hotelareascore import publication
import duckdb

@pytest.mark.parametrize('name,category,kind', [
    ('OYO 968 Home 2005A Sobha creek Vistas 1BR','hotel','whole-home'),
    ('OYO 577 For Love Hotel','hotel','hotel'),
    ('Super OYO 498 Ladawan Villa','hotel','hotel'),
    ('Home Hotel','hotel','hotel'), ('The House Hotel','hotel','hotel'),
    ('Youth Hostel','hotel','hostel'), ('Blueground Midtown','hotel','whole-home'),
    ('Sonder Midtown','hotel','unknown'), ('Domio Downtown','hotel','unknown'),
    ('Citadines Apart Hotel','hotel','aparthotel'),
    ('Hotel Apartments Downtown','hotel','aparthotel'),
    ('Riverside','service_apartment','serviced-apartment'),
    ('Riverside','bed_and_breakfast','guesthouse-B&B'),
    ('Riverside','guest_house','guesthouse-B&B'),
    ('Riverside','lodging','unknown'), ('Sunshine Apartments','hotel','whole-home'),
    ('Youth','hostel','hostel'), ('Golf Resort','resort','unknown'),
])
def test_types(name,category,kind):
    assert classify_accommodation({'name':name,'taxonomy_primary':category})['accommodation_type'] == kind

def test_source_operator_and_missing_evidence():
    assert classify_accommodation({'name':'Broadway','brand_name':'Blueground','taxonomy_primary':'hotel'})['accommodation_type']=='whole-home'
    assert classify_accommodation({'name':'Home'})['accommodation_type']=='unknown'

@pytest.mark.parametrize('kind',[None,'unknown','aparthotel','serviced-apartment','whole-home','hostel','guesthouse-B&B'])
def test_nonhotel_publication_fails_closed(tmp_path,kind):
    with publication.connect(tmp_path/'pub.sqlite') as con:
        with pytest.raises(ValueError,match='explicitly classified hotel'):
            publication.set_status(con,'hotel','test','indexable','test','test',hotel_name='Test',accommodation_type=kind)
        publication.set_status(con,'hotel','test','noindex','test','test',accommodation_type=kind)

def test_annotation_preserves_rows_and_source_values():
    con=duckdb.connect()
    con.execute("CREATE TABLE hotels AS SELECT 'id' id, 'Home Hotel' AS name, 'hotel' taxonomy_primary, 12.5 lat")
    annotate_table(con,'hotels')
    annotate_table(con,'hotels')
    assert con.execute('SELECT id,name,lat,accommodation_type FROM hotels').fetchall()==[('id','Home Hotel',12.5,'hotel')]
