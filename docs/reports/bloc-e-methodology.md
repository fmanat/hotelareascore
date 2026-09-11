# Bloc E — Annexe des calculs de recherche

Rapport seulement ; scripts exécutés dans `/tmp`, aucune intégration applicative.
Depuis la racine, environnement Python du projet avec `PYTHONPATH=src`. Les chemins absolus ci-dessous sont ceux de la session ; les adapter au checkout. Exécuter les trois extraits dans cet ordre. Aucun scoring/export/publication appelé. Les caches de recherche restent locaux ; les SHA-256 et les résultats sont archivés dans le JSON.

## Extraction STAC places / land_use / land

```python
import sys,json
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0,'/Users/jvb/hotelareascore/src')
sys.path.insert(0,'/Users/jvb/hotelareascore/scripts')
from audit_brand_contacts import fetch
from hotelareascore.config import load_cities
from hotelareascore import overture
root=Path('/Users/jvb/hotelareascore');out=root/'data/research/bloc-e';out.mkdir(parents=True,exist_ok=True)
release_id=json.loads((root/'web/src/data/meta.json').read_text())['release']
cat=fetch('https://stac.overturemaps.org/catalog.json');rel=fetch(next(l['href'] for l in cat['links'] if release_id in l['href']))
items={};provenance={'release':release_id,'city_assets':{},'schemas':{}}
for theme in ('places','base'):
 collection=fetch(next(l['href'] for l in rel['links'] if l.get('title')==theme))
 for link in collection['links']:
  if link['rel']!='child':continue
  name=link.get('title') or link['href'].rstrip('/').split('/')[-2]
  child=fetch(link['href'])
  typename=child['id'].split('/')[-1]
  # STAC ids are e.g. base/land_use; inspect actual title/id.
  key='place' if theme=='places' else next((t for t in ('land_use','land') if child['id']==t or child['id'].endswith('/'+t) or child['id'].endswith('_'+t)),None)
  if key is None:
   key=next((t for t in ('land_use','land') if '/'+t+'/' in link['href'] or '/'+t+'.' in link['href']),None)
  print('collection',theme,child['id'],key,flush=True)
  if key not in ('place','land_use','land'):continue
  with ThreadPoolExecutor(max_workers=4) as pool:items[key]=list(pool.map(fetch,[l['href'] for l in child['links'] if l['rel']=='item']))
con=overture.connect();con.execute('SET threads=4')
pattern='stadium|arena|convention|conference|exhibition|expo|airport|golf|beach|ski|national_park|nature_reserve|wildlife|amusement|water_park|hospital|medical_center|college|university|campus|casino'
for city_id,city in load_cities().items():
 folder=out/city_id;folder.mkdir(exist_ok=True);b=city.bbox;provenance['city_assets'][city_id]={}
 for kind in ('place','land_use','land'):
  urls=[i['assets']['aws']['href'] for i in items[kind] if i['bbox'][0]<=b[2] and i['bbox'][2]>=b[0] and i['bbox'][1]<=b[3] and i['bbox'][3]>=b[1]]
  if not urls:raise ValueError((city_id,kind,'no assets'))
  provenance['city_assets'][city_id][kind]=urls
  path=folder/(kind+'.parquet')
  if path.exists():print(city_id,kind,'cached',flush=True);continue
  print(city_id,kind,len(urls),'assets',flush=True)
  schema=con.execute('DESCRIBE SELECT * FROM read_parquet(?)',[urls]).fetchall();provenance['schemas'][kind]=[[r[0],r[1]] for r in schema]
  if kind=='place':
   con.execute('''CREATE OR REPLACE TEMP TABLE extracted AS SELECT id,names.primary AS name,taxonomy.primary AS category,taxonomy.hierarchy AS hierarchy,
     bbox.xmin AS lon,bbox.ymin AS lat,confidence,operating_status,websites FROM read_parquet(?)
     WHERE bbox.xmin BETWEEN ? AND ? AND bbox.ymin BETWEEN ? AND ? AND regexp_matches(taxonomy.primary,?)''',[urls,b[0],b[2],b[1],b[3],pattern])
  else:
   pred="(class IN ('golf_course','driving_range','theme_park','water_park','stadium','hospital','clinic','university','college','national_park','nature_reserve','state_park','protected_landscape_seascape','wilderness_area','strict_nature_reserve','airfield','beach_resort') OR subtype='winter_sports')" if kind=='land_use' else "class='beach'"
   con.execute(f'''CREATE OR REPLACE TEMP TABLE extracted AS SELECT id,names.primary AS name,subtype,class,geometry,bbox FROM read_parquet(?)
    WHERE bbox.xmin<=? AND bbox.xmax>=? AND bbox.ymin<=? AND bbox.ymax>=? AND {pred}''',[urls,b[2],b[0],b[3],b[1]])
  tmp=path.with_suffix('.tmp.parquet');con.execute('COPY extracted TO ? (FORMAT PARQUET)',[str(tmp)]);tmp.replace(path)
  print(city_id,kind,con.execute('SELECT count(*) FROM extracted').fetchone()[0],flush=True)
  (out/'provenance.json').write_text(json.dumps(provenance,indent=2)+'\n')
(out/'provenance.json').write_text(json.dumps(provenance,indent=2)+'\n')
```

## Complément catégories événementielles

```python
import sys,json
from pathlib import Path
sys.path.insert(0,'/Users/jvb/hotelareascore/src')
from hotelareascore.config import load_cities
from hotelareascore import overture
root=Path('/Users/jvb/hotelareascore');out=root/'data/research/bloc-e';con=overture.connect();con.execute('SET threads=2')
for cid,city in load_cities().items():
 folder=out/cid;folder.mkdir(exist_ok=True);p=folder/'events.parquet'
 if p.exists():continue
 urls=json.loads((root/'data/etl/2026-08-19.0'/cid/'source-names-provenance.json').read_text())['assets'];b=city.bbox
 con.execute('''CREATE OR REPLACE TEMP TABLE events AS SELECT id,names.primary AS name,taxonomy.primary AS category,taxonomy.hierarchy AS hierarchy,
 bbox.xmin AS lon,bbox.ymin AS lat,confidence,operating_status,websites FROM read_parquet(?)
 WHERE bbox.xmin BETWEEN ? AND ? AND bbox.ymin BETWEEN ? AND ? AND regexp_matches(taxonomy.primary,'event|meeting|banquet|convention|conference|exhibition')''',[urls,b[0],b[2],b[1],b[3]])
 con.execute('COPY events TO ? (FORMAT PARQUET)',[str(p)]);print(cid,con.execute('SELECT category,count(*) FROM events GROUP BY category').fetchall(),flush=True)
```

## Mesure et tableaux

```python
import sys,json
from pathlib import Path
from collections import Counter
sys.path.insert(0,'/Users/jvb/hotelareascore/src')
from hotelareascore.config import load_cities
from hotelareascore.geo import project_sql
from hotelareascore import overture
root=Path('/Users/jvb/hotelareascore');data=root/'data/research/bloc-e';release='2026-08-19.0';con=overture.connect()
families={
 'stadium_arena':{'radius':1000,'area':20000,'classes':['stadium']},
 'congress':{'radius':750,'area':None,'classes':[]},
 'expo':{'radius':750,'area':None,'classes':[]},
 'airport':{'radius':1500,'area':None,'classes':[]},
 'golf':{'radius':500,'area':300000,'classes':['golf_course']},
 'beach':{'radius':250,'area':10000,'classes':['beach']},
 'ski':{'radius':1000,'area':100000,'classes':['downhill','nordic','ski_jump','snow_park']},
 'national_park':{'radius':500,'area':1000000,'classes':['national_park','nature_reserve','state_park','wilderness_area','strict_nature_reserve','protected_landscape_seascape']},
 'theme_park':{'radius':750,'area':50000,'classes':['theme_park','water_park']},
 'hospital':{'radius':500,'area':20000,'classes':['hospital']},
 'campus':{'radius':500,'area':100000,'classes':['university','college']},
 'casino':{'radius':500,'area':None,'classes':[]}}
def family(cat):
 if cat and ('stadium' in cat or cat in ('hockey_arena','stadium_arena')):return 'stadium_arena'
 return {'event_venue':'congress','exhibition_and_trade_fair_venue':'expo','airport':'airport','golf_course':'golf','golf_club':'golf','beach':'beach','ski_resort':'ski','national_park':'national_park','nature_reserve':'national_park','wildlife_sanctuary':'national_park','amusement_park':'theme_park','water_park':'theme_park','hospital':'hospital','childrens_hospital':'hospital','college_university':'campus','casino':'casino'}.get(cat)
result={'release':release,'purpose':'report_only_not_a_hotel_classifier','thresholds':families,'cities':{},'owner_cases':[]}
allmatches=[];sample=[]
for cid,city in load_cities().items():
 folder=data/cid
 if not all((folder/(f+'.parquet')).exists() for f in ('place','land_use','land','events')):print(cid,'not ready',flush=True);continue
 con.execute('CREATE OR REPLACE TEMP TABLE points AS SELECT * FROM read_parquet(?) UNION SELECT * FROM read_parquet(?)',[str(folder/'place.parquet'),str(folder/'events.parquet')])
 cats=dict(con.execute('SELECT category,count(*) FROM points GROUP BY category').fetchall())
 pointcounts=Counter();pc=[]
 for cat,n in cats.items():
  f=family(cat)
  if f:pointcounts[f]+=n;pc.append((cat,f,families[f]['radius']))
 con.execute('CREATE OR REPLACE TEMP TABLE mapping(category VARCHAR, family VARCHAR, radius DOUBLE)')
 con.executemany('INSERT INTO mapping VALUES (?,?,?)',pc)
 con.execute(f'''CREATE OR REPLACE TEMP TABLE p AS SELECT p.*,m.family,m.radius,{project_sql('ST_Point(p.lon,p.lat)',city)} AS geom FROM points p JOIN mapping m USING(category)''')
 con.execute(f'''CREATE OR REPLACE TEMP TABLE h AS SELECT h.id,h.name,h.accommodation_type,h.lat,h.lon,s.walkability_density,{project_sql('ST_Point(h.lon,h.lat)',city)} AS geom
 FROM read_parquet(?) h JOIN read_parquet(?) s ON h.id=s.hotel_id''',[str(root/'data/etl'/release/cid/'hotels.parquet'),str(root/'data/etl'/release/cid/'hotel_scores.parquet')])
 con.execute('CREATE OR REPLACE TEMP TABLE polygons AS SELECT *,\'land_use\' AS source FROM read_parquet(?) UNION ALL SELECT *,\'land\' AS source FROM read_parquet(?)',[str(folder/'land_use.parquet'),str(folder/'land.parquet')])
 con.execute(f'''CREATE OR REPLACE TEMP TABLE a AS SELECT id,name,subtype,class,source,{project_sql('geometry',city)} AS geom FROM polygons WHERE ST_IsValid(geometry) AND ST_GeometryType(geometry) IN ('POLYGON','MULTIPOLYGON')''')
 con.execute('ALTER TABLE a ADD COLUMN area DOUBLE');con.execute('UPDATE a SET area=ST_Area(geom)')
 # All types remain research candidates; only class+surface proxy, not asserted major venues.
 con.execute('CREATE OR REPLACE TEMP TABLE matches(hotel_id VARCHAR,family VARCHAR,anchor_id VARCHAR,anchor_name VARCHAR,anchor_area DOUBLE,distance_m DOUBLE)')
 famreport={}
 for f,cfg in families.items():
  classes=cfg['classes']
  polygons_n=con.execute('SELECT count(*) FROM a WHERE class IN (SELECT unnest(?))',[classes]).fetchone()[0] if classes else 0
  nmajor=con.execute('SELECT count(*) FROM a WHERE class IN (SELECT unnest(?)) AND area>=?',[classes,cfg['area']]).fetchone()[0] if classes else 0
  if classes:
   con.execute('''INSERT INTO matches SELECT h.id,?,a.id,a.name,a.area,ST_Distance(h.geom,a.geom) FROM h JOIN a ON ST_DWithin(h.geom,a.geom,?) WHERE a.class IN (SELECT unnest(?)) AND a.area>=?''',[f,cfg['radius'],classes,cfg['area']])
  naive=con.execute('''SELECT count(DISTINCT h.id) FROM h JOIN p ON ST_DWithin(h.geom,p.geom,p.radius) WHERE p.family=? AND p.confidence>=0.8 AND coalesce(p.operating_status,'open')!='permanently_closed' ''',[f]).fetchone()[0]
  famreport[f]={'places':pointcounts[f],'land_polygons':polygons_n,'polygons_above_area_floor':nmajor,'nearby_accommodation_polygon_candidates':con.execute('SELECT count(DISTINCT hotel_id) FROM matches WHERE family=?',[f]).fetchone()[0],'naive_point_nearby_accommodation':naive}
 con.execute('''CREATE OR REPLACE TEMP TABLE naive AS SELECT DISTINCT h.id FROM h JOIN p ON ST_DWithin(h.geom,p.geom,p.radius) WHERE p.confidence>=0.8 AND coalesce(p.operating_status,'open')!='permanently_closed' ''')
 counts={}
 for scope,where in [('all_accommodations','TRUE'),('hotel_type',"accommodation_type='hotel'")]:
  total,isolated,poly,ipoly,naive,inaive=con.execute(f'''SELECT count(*),count(*) FILTER(WHERE walkability_density<=55),
   count(*) FILTER(WHERE id IN (SELECT hotel_id FROM matches)),count(*) FILTER(WHERE walkability_density<=55 AND id IN (SELECT hotel_id FROM matches)),
   count(*) FILTER(WHERE id IN (SELECT id FROM naive)),count(*) FILTER(WHERE walkability_density<=55 AND id IN (SELECT id FROM naive)) FROM h WHERE {where}''').fetchone()
  counts[scope]={'total':total,'isolated':isolated,'polygon_anchor_candidates':poly,'isolated_with_polygon_anchor':ipoly,'isolated_without_polygon_anchor':isolated-ipoly,'naive_point_anchor_candidates':naive,'isolated_with_naive_point_anchor':inaive}
 # Nearest candidate per isolated hotel; keep IDs for inspectable evidence, not web exports.
 rows=con.execute('''SELECT h.id,h.name,h.accommodation_type,h.walkability_density,m.family,m.anchor_id,m.anchor_name,m.anchor_area,m.distance_m FROM matches m JOIN h ON h.id=m.hotel_id WHERE h.walkability_density<=55 QUALIFY row_number() OVER(PARTITION BY h.id ORDER BY m.distance_m,m.anchor_id)=1 ORDER BY h.walkability_density,h.id''').fetchall()
 columns=['id','name','accommodation_type','walkability_density','anchor_family','anchor_id','anchor_name','anchor_area_m2','distance_m']
 for row in rows:allmatches.append({'city':cid,**dict(zip(columns,row))})
 sample.extend([{'city':cid,**dict(zip(columns,row))} for row in rows[:3]])
 airport=con.execute("SELECT id,name,confidence,lat,lon FROM p WHERE family='airport' ORDER BY confidence DESC,name LIMIT 8").fetchall()
 result['cities'][cid]={'counts':counts,'families':famreport,'category_counts':cats,'polygon_class_counts':{str(a)+':'+str(b):n for a,b,n in con.execute('SELECT subtype,class,count(*) FROM polygons GROUP BY subtype,class').fetchall()},'airport_sample':[dict(zip(['id','name','confidence','lat','lon'],r)) for r in airport]}
 if cid in ('bangkok','new_york'):
  cond="name ILIKE '%Hilton Bangkok Suvarnabhumi%'" if cid=='bangkok' else "id='c6278881-6e4a-423e-8e44-c8316203d1d1'"
  for row in con.execute(f'''SELECT h.id,h.name,h.accommodation_type,h.walkability_density,a.id,a.name,a.class,a.area,ST_Distance(h.geom,a.geom) d FROM h CROSS JOIN a WHERE {cond.replace('name ILIKE','h.name ILIKE').replace("id='c627", "h.id='c627")} AND a.class IN ('golf_course','stadium') ORDER BY d LIMIT 4''').fetchall():result['owner_cases'].append({'city':cid,**dict(zip(['id','name','accommodation_type','walkability_density','anchor_id','anchor_name','anchor_class','area_m2','distance_m'],row))})
 print(cid,counts,flush=True)
result['isolated_anchor_candidates']=allmatches;result['inspection_candidates']=sample
(data/'measurements.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
```

