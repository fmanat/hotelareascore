"""Accommodation identity, not a score adjustment (ADR-019)."""
import re
from .institutions import normalize_name

VERSION = '1.0.0'
LABELS = {'hotel':'Hotel', 'aparthotel':'Aparthotel', 'serviced-apartment':'Serviced apartment',
          'whole-home':'Whole home', 'hostel':'Hostel', 'guesthouse-B&B':'Guesthouse / B&B', 'unknown':'Accommodation type unconfirmed'}

def classify_accommodation(row):
    name = normalize_name(row.get('name') or '')
    operator = normalize_name(row.get('brand_name') or '')
    category = row.get('taxonomy_primary') or ''
    def found(pattern):
        return re.search(pattern,name)
    def result(kind,reason):
        return {'accommodation_type':kind, 'accommodation_type_label':LABELS[kind],
                'accommodation_type_reason':reason, 'accommodation_type_version':VERSION}
    # Specific whole-unit evidence overrides generic hotel taxonomy/chain names.
    if found(r'\boyo\b.*\bhome\b') or found(r'\b(entire (home|apartment|house)|whole home|holiday home|vacation rental|[1-9]\s*(br|bedroom|bed)\b.*apartment)\b'):
        return result('whole-home','explicit_whole_unit_name')
    if 'blueground' in name or 'blueground' in operator:
        return result('whole-home','furnished_rental_operator_blueground')
    if category in ('hostel', 'youth_hostel') or found(r'\b(youth hostel|hostel|albergue|ostello|jeugdherberg)\b'):
        return result('hostel','hostel_category_or_name')
    if found(r'\b(aparthotel|apart hotel|apartment hotel|residence hoteliere|hotel apartments)\b') or category=='aparthotel':
        return result('aparthotel','explicit_aparthotel')
    if category in ('service_apartment','serviced_apartment') or found(r'\bserviced apartments?\b'):
        return result('serviced-apartment','serviced_apartment_category_or_name')
    if category in ('bed_and_breakfast','guest_house') or found(r'\b(bed and breakfast|b and b|guesthouse|guest house|chambres d hotes)\b'):
        return result('guesthouse-B&B','guesthouse_category_or_name')
    if found(r'\b(apartment|apartments|appartement|apartamento|appartamento|holiday homes)\b'):
        return result('whole-home','apartment_name_without_hotel_service_evidence')
    if any(re.search(r'\b'+brand+r'\b',name+' '+operator) for brand in ('sonder','domio')):
        # Mixed portfolios: never invent reception/service from an operator.
        return result('unknown','mixed_operator_requires_property_evidence')
    if category in ('hotel','motel'):
        return result('hotel','overture_hotel_taxonomy_not_reception_verification')
    if category=='resort' and found(r'\bhotel\b'):
        return result('hotel','resort_category_with_explicit_hotel_name')
    return result('unknown','insufficient_or_ambiguous_accommodation_evidence')

def annotate_table(con, table):
    """Add derived columns to an internal ETL table; no source-row removal."""
    cursor=con.execute(f'SELECT * FROM {table}')
    cols=[c[0] for c in cursor.description]
    rows=[dict(zip(cols,r)) for r in cursor.fetchall()]
    con.execute('CREATE OR REPLACE TEMP TABLE _accommodation (id VARCHAR, accommodation_type VARCHAR, accommodation_type_label VARCHAR, accommodation_type_reason VARCHAR, accommodation_type_version VARCHAR)')
    if rows:
        con.executemany('INSERT INTO _accommodation VALUES (?,?,?,?,?)',[(r['id'],*classify_accommodation(r).values()) for r in rows])
    existing=[c for c in cols if c.startswith('accommodation_type')]
    select='h.*'+(' EXCLUDE ('+','.join(existing)+')' if existing else '')
    con.execute(f'CREATE OR REPLACE TEMP TABLE _typed AS SELECT {select}, a.* EXCLUDE(id) FROM {table} h JOIN _accommodation a USING(id)')
    con.execute(f'CREATE OR REPLACE TABLE {table} AS SELECT * FROM _typed')
