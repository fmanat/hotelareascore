# Bloc B — marques sans établissement

Date : 2026-09-11. Release Overture : `2026-08-19.0`. Périmètre : les 12 villes complètes, après les exclusions du Bloc A. Décision : [ADR-017](../adr/017-brand-establishment-exclusion.md).

**33 920 entrées examinées ; 141 exclues du dataset ; 33 779 conservées.** Les exclusions comprennent 5 programmes de fidélité, 63 noms de bureaux/sièges/gestion et 73 marques ombrelles. Ce sont des motifs de détection, pas 141 identités toutes confirmées : 56 sont corroborées par une source web, 59 portent explicitement un nom de bureau, et **26 restent incertaines et sont mises en quarantaine**. Les sources historiques établissent une identité de société, pas son activité actuelle.

Onze alias de véritables établissements sont conservés après vérification. Aucun signal générique d’attributs n’est activé. Aucun score conservé ni aucune formule ne change.

## Comptages par ville et groupe

| Ville | Scannées | Exclues | Conservées |
|---|---:|---:|---:|
| london | 4389 | 25 | 4364 |
| bangkok | 7540 | 23 | 7517 |
| paris | 3577 | 9 | 3568 |
| rome | 5033 | 3 | 5030 |
| barcelona | 1715 | 11 | 1704 |
| amsterdam | 1070 | 5 | 1065 |
| lisbon | 1287 | 5 | 1282 |
| sydney | 1077 | 10 | 1067 |
| tokyo | 2745 | 11 | 2734 |
| dubai | 2065 | 5 | 2060 |
| new_york | 2189 | 15 | 2174 |
| singapore | 1233 | 19 | 1214 |
| **Total** | **33 920** | **141** | **33 779** |

Groupes des programmes demandés, tous motifs confondus :

| Ville | Accor | Marriott | Hyatt | IHG | Hilton | Wyndham | Choice | Autres / indéterminés |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| london | 3 | 2 | 1 | 1 | 1 | 0 | 0 | 17 |
| bangkok | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 22 |
| paris | 2 | 1 | 0 | 0 | 0 | 0 | 0 | 6 |
| rome | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 2 |
| barcelona | 1 | 2 | 0 | 0 | 0 | 0 | 0 | 8 |
| amsterdam | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 3 |
| lisbon | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 5 |
| sydney | 2 | 0 | 1 | 0 | 0 | 0 | 0 | 7 |
| tokyo | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 11 |
| dubai | 0 | 1 | 0 | 1 | 0 | 0 | 0 | 3 |
| new_york | 0 | 3 | 1 | 0 | 0 | 0 | 0 | 11 |
| singapore | 0 | 3 | 0 | 1 | 2 | 0 | 0 | 13 |

Ventilation exhaustive des autres groupes et des motifs par ville : [audit JSON](bloc-b-brands.json), champs `cities.*.by_group` et `by_primary_reason`. Les 141 lignes individuelles y portent ID, nom, adresse, coordonnées, motif, groupe, statut de revue et sources. `unresolved` signifie attribution de groupe indéterminée ; le record Ramada International historique n’est pas attribué automatiquement à Wyndham.

Détail exhaustif par ville :

- **london** : Accor 3; Arora 1; Clermont 1; Concorde 1; Crown 1; Dorchester 1; Hilton 1; Hyatt 1; IHG 1; Kempinski 1; London Hotel Group 1; Lords 1; Marriott 2; Maybourne 1; PPHE 1; Ramada International (operator unresolved) 1; Resident 1; Shaftesbury 1; Splendid 1; unresolved 3.
- **bangkok** : Best Western 2; Chada 1; Club Med 1; Fortune 1; Griffin 1; Hyatt 1; Kasemkij 1; Mida 1; Minor 2; NNR Nishitetsu 1; Nongnooch 1; Royal Cliff 1; Santhiya 1; Thai Hotel Group 1; Tongsai Bay 1; Veranda 1; unresolved 5.
- **paris** : Accor 2; Hotusa 1; Les Grillons 1; Louvre 1; Marriott 1; Peninsula 1; Regetel 1; Warwick 1.
- **rome** : Hilton 1; Hotusa 1; Roscioli 1.
- **barcelona** : Accor 1; Acta 1; H10 1; Hotusa 2; Marriott 2; SB Hotels 1; Sercotel 1; Sunotel 1; unresolved 1.
- **amsterdam** : Accor 1; Eden 1; IHG 1; Vincent 1; WIN 1.
- **lisbon** : Browns 1; Discovery 2; Euroconfort 1; Real Hotels 1.
- **sydney** : Accor 2; Constellation 1; Gallagher 1; Hyatt 1; Kingfisher 1; NLG 1; Red Star 2; unresolved 1.
- **tokyo** : Asaya 1; BAY HOTEL 1; Hakuba Alps 1; Kanucha 1; Koyo 1; Kusatsu Now 1; Otsuka Shokai 1; Sunvalley 1; Tokyo West 1; Urashima 1; unresolved 1.
- **dubai** : Al Hayat 1; Byblos 2; IHG 1; Marriott 1.
- **new_york** : Bridgeton 1; Denihan 1; Hyatt 1; Mandarin Oriental 1; Marriott 3; Mint House 1; Morgans 1; Real Hospitality 1; Sonder 1; unresolved 4.
- **singapore** : Aurora 1; Beaufort 1; Frasers 1; Hilton 2; IHG 1; MGM 1; Madras 1; Marriott 3; Meritus 1; Millennium & Copthorne 1; Pan Pacific 1; Park Hotel Group 1; Prince 1; Semhotel 1; unresolved 2.

## Programmes et établissements : frontières de détection

Les sept familles demandées sont testées même lorsqu’aucune occurrence n’existe dans cette release. Les programmes présents sont ALL Accor (Paris), Marriott Bonvoy (Barcelone), Hyatt Thailand (canal World of Hyatt en Thaïlande), Club Marriott (Singapour) et Premier Club Rewards (Londres). Sources des définitions :

- [ALL / Accor Live Limitless](https://all.accor.com/a/en/loyalty-program/accor-live-limitless-hotel-loyalty-program.html), [Marriott Bonvoy](https://www.marriott.com/loyalty/terms/default.mi), [World of Hyatt](https://world.hyatt.com/content/gp/en/program-overview.html), [IHG One Rewards](https://www.ihg.com/intercontinental/content/us/en/loyalty).
- [Hilton Honors](https://www.hilton.com/en/hilton-honors/), [Wyndham Rewards](https://www.wyndhamhotels.com/wyndham-rewards), [Choice Privileges](https://media.choicehotels.com/choice-privileges-press-kit), [Club Marriott](https://www.myclubmarriott.com/), [Hyatt Thailand](https://page.line.me/hyatt_thailand).
- Alias locaux vérifiés : [ALL chinois](https://all.accor.com/a/zh.html), [Marriott chinois](https://www.marriott.com.cn/loyalty.mi), [Hyatt chinois](https://world.hyatt.com/content/gp/zh-hans/program-overview.html), [Hyatt japonais](https://world.hyatt.com/content/gp/ja/program-overview.html?os=0), [Hilton japonais](https://www.hilton.com/ja/hilton-honors/), [IHG chinois](https://www.ihg.com.cn/onerewards/content/cn/zh/home), [Wyndham chinois](https://www.wyndhamhotels.com/zh-cn/wyndham-rewards), [Marriott japonais](https://www.marriott.com/ja/loyalty/redeem.mi).

Les bureaux et groupes couvrent anglais, français, espagnol, catalan, italien, portugais, néerlandais, arabe, japonais, chinois, thaï, malais et tamoul. Une affiliation après un nom d’établissement reste admise (`Hotel Maple, Marriott Bonvoy`, `Hotel Midas Roma, a member of Barceló Hotel Group`). `Hotel Marriott Bonvoy` seul reste exclu : « Hotel » ne suffit pas à créer une identité d’établissement.

Exceptions limitées à **ID + nom exact + motif** ; un suffixe « Corporate Office » annule la protection. Un nom de groupe n’est jamais autorisé globalement parce qu’un hôtel partage ce nom.

| Alias source conservé | Établissement / preuve |
|---|---|
| Parvena Hotel Group | [Parvena Ratchada is bookable at the exact source street and number; group wording is an alias.](https://www.booking.com/hotel/th/rachdaa-erschiednch.en-gb.html) |
| Hilton Italiana | [Property operator at Rome Cavalieri exact address; not evidence of a separate group office.](https://romecavalieri.com/personal-data-collection-information/) |
| Nikko Hotels International | [Grand Nikko Tokyo Daiba at 2-6-1 Daiba. Retain property-address alias; do not globally allow the umbrella name.](https://dmo-tokyo-odaiba.jp/en/facilities/detail.php?id=100019) |
| Bayview International | [Sydney Boulevard Hotel at 90 William Street, managed by Bayview; property-address alias.](https://www.cnsneurosurgery.com.au/wp-content/uploads/2015/11/East-Sydney-Private-Hospital-Special-CNS-Neurosurgery-2015.pdf) |
| Louvre Hotels Group complexe hotelier Suresnes | [Name explicitly identifies the Suresnes hotel complex; same 15 Boulevard Henri Sellier property address. Headquarters separately identified at 1 Place des Degres. Retrieved Overture website points specifically to Campanile Paris Ouest Pont de Suresnes.](https://www.kactus.com/fr/lieux/campanile-paris-ouest-pont-de-suresnes) |
| NH Hotels Group | [Source 69 Deu i Mata matches NH Collection Constanza 69-99; preserve this property-address alias only, no global allowance. Retrieved Overture contact has the exact Constanza property URL and phone 932811500.](https://www.nh-collection.com/en/hotel/nh-collection-barcelona-constanza) |
| Eurostars Hotels | [Eurostars Lex / Ikonik Lex: source address Buenos Aires 49-51 and phone 933318679 both match the named property.](https://www.eurostarshotels.com/Collection/files/eurostars%20hotels%202010-2011.pdf) |
| Eurostars Hotels | [Dorma / Eurostars Ramblas Boqueria: exact 91-93 Rambla de Sant Josep and 933435461 phone match.](https://www.eurostarshotels.co.uk/dorma-ramblas-boqueria.html) |
| Gargallo Hotels | [Casa Lit Barcelona: exact Arc del Teatre 58; source phone 934517923 corroborated by the Barcelona hotel guild programme https://mesqhotels.cat/wp-content/uploads/2026/06/OR-STH-Programa-Online-2026-2.pdf .](https://www.casalitbarcelona.com/IT/contatti.html) |
| Dorchester Collection | [Plaza Athenee: exact 25 Avenue Montaigne property address, distinct from the London group office.](https://www.dorchestercollection.com/fr/paris/hotel-plaza-athenee) |
| Dorchester Collection | [Hotel Eden: exact Via Ludovisi 49 property address, distinct from the London group office.](https://media.dorchestercollection.com/wp-content/uploads/2025/10/98f471598f7754d5fd9e2358e3fea650.pdf) |

Cas contrastés : Dorchester Collection à Londres est le bureau de Lansdowne House ; les lignes Paris (Plaza Athénée) et Rome (Eden) sont conservées. H10 Hotels à Numància 185, premier étage, est le siège ; les hôtels H10 nommés restent admis. NH Hotels Group à Barcelone possède dans Overture le numéro et l’URL précis de NH Collection Constanza. Le site Overture de Louvre Suresnes vise précisément le Campanile, alors que le siège Louvre est ailleurs.

Autres noms examinés sans élargir arbitrairement une interdiction : les contacts citizenM renvoient à de vrais établissements ([Champs-Élysées](https://www.marriott.com/en-us/hotels/parce-citizenm-paris-champs-elysees/overview/), [CDG](https://www.marriott.com/en-gb/hotels/parcg-citizenm-paris-charles-de-gaulle-airport/overview/)). Leur localisation reste un sujet distinct. Marriott Vacation Club exploite aussi un [établissement à Bangkok](https://www.marriottvacationclubs.com/experiences/resorts/marriott-vacation-club-at-the-empire-place.html) : ce nom n’est pas assimilé automatiquement à Bonvoy. Le contact source Aman Resorts vise [Aman Nai Lert Bangkok](https://www.aman.com/hotels/aman-nai-lert-bangkok), donc aucune interdiction globale du nom Aman n’est ajoutée.

## Cas encore douteux : exclure et journaliser

Les 26 lignes suivantes sont retirées sans prétendre que leur absence d’établissement a été démontrée. Les recherches sans correspondance probante ne deviennent pas une preuve négative. Adresses et requêtes de revue figurent dans le JSON ; les sources ne valent que pour ce qu’elles établissent.

| Ville | Entrée | Résultat de revue |
|---|---|
| london | Arora Holdings | Matching identity is not sufficiently established as an individual hotel. Withheld pending an exact property match; no assertion of fraud or of non-existence.  |
| london | Hilton International Franchise Limited | Matching identity is not sufficiently established as an individual hotel. Withheld pending an exact property match; no assertion of fraud or of non-existence.  |
| london | Hyatt Holdings | Matching identity is not sufficiently established as an individual hotel. Withheld pending an exact property match; no assertion of fraud or of non-existence.  |
| london | Accor London | Matching identity is not sufficiently established as an individual hotel. Withheld pending an exact property match; no assertion of fraud or of non-existence. [Source 1](https://www.sevenoaks.gov.uk/download/downloads/id/28/hotel_futures_study_2007_update.pdf) |
| london | Ramada International | Matching identity is not sufficiently established as an individual hotel. Withheld pending an exact property match; no assertion of fraud or of non-existence. Source website points to Marriott; do not attribute this historic corporate record to Wyndham on the brand word alone. [Source 1](https://www.bizseek.co.uk/ramada-international-020-7591-1100) |
| london | Concorde Hotels International | Matching identity is not sufficiently established as an individual hotel. Withheld pending an exact property match; no assertion of fraud or of non-existence. Directory corroborates name/address but does not establish a specific hotel. [Source 1](https://www.bizseek.co.uk/concorde-hotels-international_2q-020-7630-1704) |
| london | Crown Group of Hotels | Matching identity is not sufficiently established as an individual hotel. Withheld pending an exact property match; no assertion of fraud or of non-existence. [Source 1](https://crowngroupofhotels.com/contact/) |
| london | Lords Group of Hotels | Matching identity is not sufficiently established as an individual hotel. Withheld pending an exact property match; no assertion of fraud or of non-existence.  |
| london | Marriott Hotels | Barnards Inn, 86 Fetter Lane is listed as Marriott Hotels International registered address; no individual bookable property established. Quarantine only this ID. [Source 1](https://www.vat-lookup.co.uk/verify/vat_check.php/VATNumber/GB310227363) |
| bangkok | Minor Hotels | Group reservations office on Soi Rubia/Sukhumvit 42; truncated source address does not establish a specific property. [Source 1](https://www.minorhotelgroup-news.com/eblast/16/edm_7day/) |
| bangkok | Thai Hotel Group | Matching identity is not sufficiently established as an individual hotel. Withheld pending an exact property match; no assertion of fraud or of non-existence. [Source 1](https://data.creden.co/company/general/0105563004901) |
| paris | Groupe Hotelier Les Grillons | Registry identifies headquarters, but historic hotel activity also exists at 60 Rue Sedaine (Hotel Le Grillon Sedaine / Bourgogne). Cannot distinguish property alias from company record. Exclude pending verification; not a confirmed non-hotel. [Source 1](https://annuaire-entreprises.data.gouv.fr/etablissement/51840126000022) |
| rome | Eurostars Italia SRL | Possible Saint Paul property alias, but source address 45 conflicts with hotel 43 and the source URL stpaul.it does not establish the property. Withheld pending exact identity verification. [Source 1](https://saint-paul.hotelinroma.com/location.html) |
| rome | Hilton Italia SPA | Matching identity is not sufficiently established as an individual hotel. Withheld pending an exact property match; no assertion of fraud or of non-existence. [Source 1](https://www.impresaitalia.info/kk04586572/hilton-italia-spa/roma.aspx) |
| barcelona | Accor Hoteles España | Matching identity is not sufficiently established as an individual hotel. Withheld pending an exact property match; no assertion of fraud or of non-existence.  |
| barcelona | Marriott Hotels International | Matching identity is not sufficiently established as an individual hotel. Withheld pending an exact property match; no assertion of fraud or of non-existence.  |
| lisbon | Browns Hotel Group | Matching identity is not sufficiently established as an individual hotel. Withheld pending an exact property match; no assertion of fraud or of non-existence. [Source 1](https://www.brownshotelgroup.com/en/) |
| dubai | Intercontinental Hotel Group Accommodation | Matching identity is not sufficiently established as an individual hotel. Withheld pending an exact property match; no assertion of fraud or of non-existence. [Source 1](https://www.bayut.com/property-market-analysis/transactions/rent/apartments/dubai/dubai-silicon-oasis-dso/intercontinental-hotel-group-accommodation/) |
| dubai | Al Hayat Group of Hotels Sharjah | Matching identity is not sufficiently established as an individual hotel. Withheld pending an exact property match; no assertion of fraud or of non-existence. [Source 1](https://www.linkedin.com/posts/al-hayat-hotel-74296624b_sharjah-uae-special-offer-al-hayat-activity-6986305946754924545-VJxT) |
| new_york | Bridgeton Holdings | Matching identity is not sufficiently established as an individual hotel. Withheld pending an exact property match; no assertion of fraud or of non-existence. [Source 1](https://commercialobserver.com/2023/09/riyad-bank-refinances-tribeca-hotel-with-60m-loan/) |
| new_york | Hyatt Corporation | Matching identity is not sufficiently established as an individual hotel. Withheld pending an exact property match; no assertion of fraud or of non-existence.  |
| new_york | Marriott International | Matching identity is not sufficiently established as an individual hotel. Withheld pending an exact property match; no assertion of fraud or of non-existence.  |
| singapore | MGM Grand International | Matching identity is not sufficiently established as an individual hotel. Withheld pending an exact property match; no assertion of fraud or of non-existence.  |
| singapore | Hilton International | Matching identity is not sufficiently established as an individual hotel. Withheld pending an exact property match; no assertion of fraud or of non-existence. [Source 1](https://www.bizapore.com/en/hilton-international-asia-pacific-pte-6737-7780) |
| singapore | Beaufort International Hotels | Matching identity is not sufficiently established as an individual hotel. Withheld pending an exact property match; no assertion of fraud or of non-existence. [Source 1](https://www.bizapore.com/en/beaufort-international-hotels-singapore-6820-6789) |
| singapore | Madras Group Of Hotels | Matching identity is not sufficiently established as an individual hotel. Withheld pending an exact property match; no assertion of fraud or of non-existence.  |

Deux risques de faux positif restent explicites : Eurostars Italia SRL pourrait être un alias du Saint Paul voisin (43 contre 45 Via Vito Volterra) ; Groupe Hôtelier Les Grillons partage une adresse ayant aussi une activité hôtelière ([registre public](https://annuaire-entreprises.data.gouv.fr/etablissement/51840126000022), [bail d’hôtel](https://www.annonces-legales.fr/consultation/ile-de-france/paris-75/avocat-141608)). L’identité exacte n’est pas assez établie : quarantaine conformément à la consigne. **Ce rapport ne revendique donc pas zéro faux positif sur les 26 cas incertains.**

## Signal générique — chiffré, désactivé

Lecture des attributs originaux via les assets GeoParquet du catalogue STAC de la même release : **33 920 / 33 920 lignes retrouvées**, aucun contact inconnu faute de collecte. Les quatre tableaux `phones`, `emails`, `websites`, `socials` sont examinés ; présence signifie seulement au moins une valeur non vide, sans vérifier que le contact fonctionne. Ces attributs sont optionnels dans le [schéma Overture](https://docs.overturemaps.org/schema/reference/places/place/).

| Ville | Adresse incomplète | Écart pays¹ | Sans contact | Coordonnées identiques même groupe² | Union | Intersection des 3 |
|---|---:|---:|---:|---:|---:|---:|
| london | 521 | 0 | 0 | 4 | 4 | 0 |
| bangkok | 1473 | 0 | 0 | 8 | 8 | 0 |
| paris | 120 | 0 | 10 | 0 | 10 | 0 |
| rome | 132 | 0 | 0 | 0 | 0 | 0 |
| barcelona | 74 | 0 | 0 | 0 | 0 | 0 |
| amsterdam | 45 | 0 | 1 | 0 | 1 | 0 |
| lisbon | 41 | 0 | 0 | 0 | 0 | 0 |
| sydney | 69 | 0 | 0 | 0 | 0 | 0 |
| tokyo | 273 | 0 | 0 | 0 | 0 | 0 |
| dubai | 409 | 0 | 0 | 75 | 75 | 0 |
| new_york | 97 | 0 | 13 | 4 | 17 | 0 |
| singapore | 121 | 158 | 0 | 0 | 158 | 0 |
| **Total** | 3375 | 158 | 24 | 91 | 273 | 0 |

¹ Proxy d’incohérence : pays de l’adresse différent du pays nominal de la ville. **Les 158 écarts sont tous `MY` dans le périmètre Singapore** : ce périmètre déborde sur la Malaisie. Ce ne sont donc pas 158 adresses prouvées fausses. L’absence de rue est comptée séparément ; les différences de région/localité, dont le New Jersey, ne sont pas assimilées à une incohérence. Aucune vérification géographique adresse/coordonnées complète n’est revendiquée.

² 91 **entrées**, pas 91 paires : IDs distincts, égalité exacte latitude/longitude, groupe déduit de la marque structurée Overture en priorité, puis d’alias connus. 4 120 entrées ont un groupe identifié ; 29 800 restent indéterminées. Un groupe indéterminé n’est pas traité comme « indépendant » et ne forme aucun cluster. Les marques source non rattachées à un parent restent distinctes : détection non exhaustive des conglomérats et des doublons légèrement décalés.

**Impact hypothétique avant purge :** règle OR = 273 entrées ; règle AND = 0. Après les exclusions B : OR = 269, AND = 0 (24 sans contact, 87 coordonnées dupliquées, 158 écarts de pays). La règle OR retirerait notamment des établissements malais légitimes ; recommandation : **ne pas l’activer**. Les contacts sont présents pour les 141 exclusions B : leur existence ne démontre pas une identité hôtelière. `generic_signal.enabled` reste `false` ; aucun appel de ce diagnostic sur les chemins ingestion/publication/build.

## Purge et vérification

- Retrait physique des 141 hôtels, de leurs scores et faits proches ; statuts de publication retirés. Sauvegardes locales `brand-backup/` ; les sauvegardes et journaux A sont conservés.
- Retrait de 141 entrées du moteur global et des shards ; **38 pages hôtel supprimées** (15 700 restantes). 327 références supprimées dans les fichiers hôtel comprennent les cartes et les comparaisons ; 5 références dans les pages ville. Build total : **15 721 pages**.
- Une entrée supplémentaire de la proposition pilote historique est retirée du dataset : ALL Accor. 197 / 200 identités historiques subsistent après A+B ; le CSV historique reste une trace, pas une liste publiable. Reconstruction attendue au Bloc F.
- Comparaison SQL bidirectionnelle `EXCEPT ALL` des lignes conservées avec les sauvegardes : hôtels, scores et faits inchangés. Jointures complètes hôtels/scores, bornes, versions, coordonnées, unicité, baselines et absence des familles A/B contrôlées sur les 12 villes.
- **419 tests réussis, 1 échec attendu préexistant**, dont **135 tests B**. Tests positifs de programmes/bureaux multilingues, 30 noms légitimes, 11 exceptions réelles, ingestion avant dédoublonnage, publication même noindex, ETL obsolète, agrégats de ville, exports, parité Python/JavaScript et maintien de l’inactivité du signal générique.
- `PYTHONPATH=src make validate CITY=all RELEASE=2026-08-19.0` : 12 villes OK, y compris le contrôle distant des catégories Overture.
- Typecheck : 0 erreur, 0 avertissement. Build réel et assertions SEO réussis sur 15 721 pages. Commit `fbbc0c4` poussé : [les cinq jobs CI sont verts](https://github.com/fmanat/hotelareascore/actions/runs/34651434836), dont les E2E.

Reproduction (avec les artefacts de la release présents) :

```bash
python3 scripts/audit_brand_contacts.py --release 2026-08-19.0
python3 scripts/exclude_brands.py --release 2026-08-19.0
# --apply effectue la purge ; les IDs doivent être journalisés auparavant.
make test
npm --prefix web run typecheck
npm --prefix web run build
(cd web && python3 scripts/seo_assertions.py)
```

Le JSON conserve les hashes des règles et des 12 inputs avant purge, les hashes et la provenance STAC des contacts, les diagnostics individuels et les suppressions par fichier. Le script préserve le rapport initial lors d’un second passage sans candidat ; les backups permettent de retrouver le périmètre initial. Pas de nouvelle dépendance payante, ni de requête par visite.

## Production — contrôle demandé avant B

Premier GET à 21:04:20 UTC le 11 septembre 2026 ; second à **21:14:34 UTC**, soit plus de dix minutes après : `/hotel/singapore-boys-home-3ba67d6c` répond encore **200** avec le titre de la page scorée. GitHub ne montre aucun déploiement (`deployments: []`). Cela ne permet pas de conclure si Cloudflare a lancé un build ; cela montre que la nouvelle suppression n’était pas servie à ce contrôle. **Aucun déclenchement, retry ou changement Cloudflare forcé.** Le propriétaire traite ce point dans son dashboard. La CI verte ne vaut pas confirmation de mise en production.

**Aucun travail sur C–F entrepris.**
