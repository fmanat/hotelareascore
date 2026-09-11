# Bloc E — Hôtels d’ancrage : étude, pas implémentation

2026-09-12 · Overture **2026-08-19.0** · 12 villes entières dans leurs bbox de projet · données après A/B/C/D.

**ARRÊT OBLIGATOIRE : aucun classificateur d’ancrage livré, aucun score ni statut de publication modifié. F attend le GO propriétaire après ce rapport.** Le type pourra changer la présentation, jamais les scores (ADR-015). Les seuils ci-dessous sont des hypothèses de mesure réversibles, pas une décision produit.

## Résultat exploitable et limite décisive

Parmi **24 452 entrées de type hôtel**, **2 874** ont `walkability_density <= 55` : **623** sont à proximité d’une emprise candidate suffisamment grande ; **2 251** restent isolées sans ancre observée par cette méthode. Sur les **33 779 hébergements**, ces chiffres sont **4 151 / 885 / 3 266**. Au total, isolés ou non, **4 910 hôtels** (6 839 hébergements) ont une emprise candidate.

Ce ne sont **pas** 623 hôtels d’ancrage confirmés contre 2 251 hôtels « mal placés » confirmés. La taille d’un polygone ne démontre ni importance, ni accès, ni fonction de séjour ; quatre familles sont insuffisamment observables dans cette extraction. Pour affirmer « isolé sans ancre », il faudra une vérification externe des grandes ancres et de leur accès. Sans cela, on pénaliserait notamment les hôtels d’aéroport/congrès. Le nombre de vrais ancrages parmi les candidats n’est pas établi ; les faux négatifs ne sont pas bornés par cette étude.

Le comparateur naïf (catégorie de point + confidence ≥ 0,8 + rayon) attache **22 764 / 24 452 hôtels**, dont **1 827 isolés** : résultat manifestement trop permissif pour un gate. Douze contre-exemples vérifiés montrent des mauvaises identités de POI ; ils ne mesurent pas un taux de faux positifs représentatif.

## Ce qu’Overture fournit réellement

Extraction des assets AWS découverts dans le catalogue STAC du release utilisé par le projet, avec filtrage spatial. `places/place` fournit identité, nom, taxonomie, point, confidence, contacts et statut ; les schémas observés sont archivés dans le JSON. Il ne fournit pas dans ces colonnes la capacité, le nombre de lits hospitaliers, passagers, étudiants, trous de golf, fréquentation, entrée publique ni chemin piéton. `confidence` ne certifie pas la bonne catégorie, le bon géocodage ou le caractère majeur.

`base/land_use` fournit les géométries et classes ci-dessous ; **la plage vient de `base/land`, pas de `land_use`**. Les classes `airfield` observées sont militaires et ne constituent pas un inventaire d’aéroports civils. Aucune classe dédiée exploitable pour congrès, expo ou casino n’a été trouvée dans le schéma de ce release. Les catégories places `event_venue` sont génériques (mariages, salles d’hôtel, etc.), pas une preuve de centre de congrès. Les prestataires événementiels sont exclus du calcul.

Sources officielles : [places](https://docs.overturemaps.org/schema/reference/places/place/), [guide places](https://docs.overturemaps.org/guides/places/), [land_use](https://docs.overturemaps.org/schema/reference/base/land_use/), [classes](https://docs.overturemaps.org/schema/reference/base/types/land_use_class/). Les observations de release priment sur une documentation qui évolue.

## Familles, seuils d’étude et faux positifs attendus

La colonne « majeur à vérifier » est une proposition à discuter, **non disponible automatiquement dans Overture**, non activée. Distance à la géométrie réelle projetée en mètres, zéro à l’intérieur ; aucune distance au centroïde de bbox. Surface minimale = proxy de présélection, jamais preuve de capacité.

| Famille | Places retenus | Emprise réellement mesurée | Surface / rayon | Majeur à vérifier ; faux positifs / manques |
|---|---|---|---|---|
| Stade/arène | catégories stadium, hockey_arena | stadium | 2 ha / 1 km | Proposition ≥10 000 places ; terrains scolaires assez grands, petites arènes couvertes manquées |
| Congrès | event_venue, très ambigu | aucune | aucun / 750 m, points seulement | ≥1 000 congressistes ; salles de mariage et ballrooms, bureaux d’organisation |
| Expo | exhibition_and_trade_fair_venue | aucune | aucun / 750 m, points seulement | ≥10 000 m² d’exposition ; organisateurs et petites galeries |
| Aéroport | airport | aucune civile fiable | aucun / 1,5 km, points seulement | ≥1 million passagers/an ou terminal civil majeur vérifié ; boutiques, bureaux, autres villes, aviation privée |
| Golf | golf_course, golf_club | golf_course | 30 ha / 500 m | 18 trous ; practice exclu, grands terrains sans accès depuis l’hôtel |
| Plage | beach | land: beach | 1 ha / 250 m | plage publique de loisirs ; vasière, rive non baignable, clôtures |
| Ski | ski_resort | downhill, nordic, ski_jump, snow_park | 10 ha / 1 km | domaine skiable de destination ; tremplin seul, pistes sèches, indoor majeur sous le seuil |
| Parc national | national_park, nature_reserve, wildlife_sanctuary | national_park, nature_reserve, state_park, wilderness_area, strict_nature_reserve, protected_landscape_seascape | 100 ha / 500 m | protection officielle + accès ; réserve fermée, proximité d’une frontière sans entrée |
| Parc à thème | amusement_park, water_park | theme_park, water_park | 5 ha / 750 m | destination publique ; équipements locaux, grands parcs indoor manqués |
| Grand hôpital | hospital, childrens_hospital | hospital | 2 ha / 500 m | ≥300 lits ou centre de référence ; cliniques, administrations, absence d’accueil des visiteurs |
| Campus | college_university | university, college | 10 ha / 500 m | ≥5 000 étudiants ou campus de destination ; bureaux, résidence, campus urbain compact manqué |
| Casino | casino | aucune | aucun / 500 m, points seulement | établissement physique majeur licencié ; bookmakers, clubs de jeux, bureaux |

Exemples de données « majeur » à sourcer hors Overture : [MetLife, 82 500 places](https://www.metlifestadium.com/stadium/about-metlife-stadium), [ExCeL, surfaces des halls](https://www.excel.london/organiser/venue-spaces/event-halls), [Palais des Congrès de Paris, auditorium de 3 723 places](https://www.viparis.com/nos-lieux/palais-des-congres-de-paris/espaces). Pas d’appel externe à chaque page vue.

## Comptage par ville

Les colonnes d’ancrage ci-dessous sont des **candidats**, pas des confirmations web. « Sans » signifie sans polygone admissible dans les familles mesurées. Le JSON donne aussi tous les hébergements et les 885 candidats isolés avec IDs, ancre, distance et surface.

| Ville | Hébergements | Hôtels | Hôtels isolés | Isolés avec emprise candidate | Isolés sans emprise | Tous hôtels avec emprise | Tous hôtels via points naïfs |
|---|---:|---:|---:|---:|---:|---:|---:|
| london | 4364 | 3120 | 558 | 124 | 434 | 865 | 2791 |
| bangkok | 7517 | 5660 | 844 | 85 | 759 | 1103 | 5141 |
| paris | 3568 | 3198 | 160 | 34 | 126 | 715 | 3145 |
| rome | 5030 | 2658 | 215 | 97 | 118 | 423 | 2581 |
| barcelona | 1704 | 1061 | 61 | 25 | 36 | 175 | 1047 |
| amsterdam | 1065 | 780 | 102 | 12 | 90 | 44 | 709 |
| lisbon | 1282 | 869 | 37 | 19 | 18 | 357 | 851 |
| sydney | 1067 | 712 | 126 | 41 | 85 | 195 | 634 |
| tokyo | 2734 | 2234 | 79 | 28 | 51 | 206 | 2218 |
| dubai | 2060 | 1462 | 291 | 85 | 206 | 283 | 1197 |
| new_york | 2174 | 1788 | 265 | 34 | 231 | 243 | 1625 |
| singapore | 1214 | 910 | 136 | 39 | 97 | 301 | 825 |

## Couverture par famille et par ville

Chaque cellule = **points / polygones au-dessus du seuil / hébergements proches de ces polygones**. Les points incluent ici toutes les confidences pour décrire la source ; le comparateur naïf applique ensuite ≥0,8 et écarte les fermetures définitives. Zéro polygone n’implique pas zéro ancre réelle. Comptes non additifs : plusieurs familles peuvent concerner un même hôtel. Détail des classes, surfaces et catégories dans le JSON.

| Ville | stadium_arena | congress | expo | airport | golf | beach | ski | national_park | theme_park | hospital | campus | casino |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| london | 508 / 21 / 255 | 370 / 0 / 0 | 48 / 0 / 0 | 308 / 0 / 0 | 239 / 131 / 106 | 144 / 22 / 43 | 6 / 0 / 0 | 217 / 16 / 25 | 253 / 2 / 8 | 1381 / 66 / 430 | 1635 / 16 / 410 | 347 / 0 / 0 |
| bangkok | 938 / 9 / 371 | 46 / 0 / 0 | 2 / 0 / 0 | 486 / 0 / 0 | 92 / 21 / 66 | 151 / 0 / 0 | 7 / 0 / 0 | 152 / 1 / 29 | 116 / 4 / 15 | 5433 / 36 / 706 | 2543 / 21 / 463 | 53 / 0 / 0 |
| paris | 257 / 5 / 108 | 41 / 0 / 0 | 6 / 0 / 0 | 70 / 0 / 0 | 27 / 2 / 3 | 40 / 0 / 0 | 2 / 0 / 0 | 9 / 1 / 0 | 93 / 1 / 14 | 505 / 34 / 645 | 918 / 5 / 98 | 24 / 0 / 0 |
| rome | 183 / 8 / 210 | 15 / 0 / 0 | 3 / 0 / 0 | 47 / 0 / 0 | 6 / 3 / 3 | 32 / 0 / 0 | 2 / 0 / 0 | 20 / 7 / 197 | 62 / 2 / 9 | 303 / 19 / 496 | 589 / 4 / 91 | 99 / 0 / 0 |
| barcelona | 187 / 3 / 95 | 40 / 0 / 0 | 9 / 0 / 0 | 34 / 0 / 0 | 8 / 1 / 2 | 237 / 14 / 28 | 4 / 0 / 0 | 14 / 2 / 22 | 53 / 1 / 3 | 321 / 10 / 128 | 309 / 3 / 8 | 29 / 0 / 0 |
| amsterdam | 40 / 2 / 22 | 32 / 0 / 0 | 5 / 0 / 0 | 14 / 0 / 0 | 9 / 2 / 3 | 26 / 0 / 0 | 2 / 0 / 0 | 9 / 3 / 8 | 16 / 0 / 0 | 86 / 5 / 24 | 283 / 2 / 3 | 17 / 0 / 0 |
| lisbon | 51 / 8 / 74 | 5 / 0 / 0 | 3 / 0 / 0 | 31 / 0 / 0 | 5 / 0 / 0 | 47 / 0 / 0 | 0 / 0 / 0 | 3 / 1 / 31 | 22 / 0 / 0 | 196 / 12 / 458 | 301 / 2 / 22 | 3 / 0 / 0 |
| sydney | 89 / 11 / 141 | 84 / 0 / 0 | 15 / 0 / 0 | 74 / 0 / 0 | 60 / 19 / 30 | 275 / 15 / 52 | 7 / 0 / 0 | 125 / 5 / 31 | 41 / 0 / 0 | 279 / 14 / 43 | 654 / 6 / 56 | 15 / 0 / 0 |
| tokyo | 233 / 5 / 144 | 247 / 0 / 0 | 15 / 0 / 0 | 14 / 0 / 0 | 110 / 1 / 0 | 34 / 2 / 0 | 17 / 0 / 0 | 21 / 0 / 0 | 228 / 3 / 33 | 2759 / 15 / 40 | 809 / 10 / 56 | 175 / 0 / 0 |
| dubai | 54 / 3 / 38 | 19 / 0 / 0 | 4 / 0 / 0 | 149 / 0 / 0 | 22 / 14 / 73 | 268 / 73 / 185 | 1 / 0 / 0 | 15 / 5 / 5 | 107 / 3 / 38 | 464 / 10 / 95 | 217 / 10 / 12 | 0 / 0 / 0 |
| new_york | 267 / 13 / 39 | 718 / 0 / 0 | 24 / 0 / 0 | 285 / 0 / 0 | 87 / 45 / 11 | 290 / 81 / 11 | 5 / 0 / 0 | 111 / 19 / 89 | 212 / 0 / 0 | 1266 / 64 / 72 | 1555 / 33 / 103 | 63 / 0 / 0 |
| singapore | 101 / 12 / 254 | 31 / 0 / 0 | 0 / 0 / 0 | 129 / 0 / 0 | 46 / 18 / 27 | 154 / 14 / 15 | 0 / 0 / 0 | 54 / 3 / 4 | 140 / 4 / 44 | 647 / 19 / 121 | 473 / 16 / 23 | 26 / 0 / 0 |

La couverture est celle des bbox du projet, pas celle des régions aéroportuaires complètes. Les polygones intersectant la bbox sont pris entiers, mais les points hors bbox et les polygones entièrement hors bbox ne sont pas extraits : effet de bord supplémentaire pour un hôtel en limite. Les classes non sélectionnées et les catégories non reconnues ne sont pas présumées absentes du monde réel. Les skis existent bien dans `places` et `land_use` ; l’ancienne conclusion « pas de ski » était trop forte.

## Contre-exemples vérifiés, un par ville

Échantillon **choisi pour tester les erreurs**, 12 mauvaises identités/catégories d’aéroport confirmées sur 12 cas choisis. Ce n’est ni 100 % de faux positifs dans la population, ni une validation des 623 hôtels. Les voisins peuvent avoir une vraie autre ancre ; leur nombre mesure seulement l’exposition à ce point erroné. Onze passent le seuil confidence ≥0,8 ; le cas Bangkok ci-dessous ne le passe pas.

| Ville | Point Overture | Confidence | Hébergements à ≤1,5 km | Constat et source primaire |
|---|---|---:|---:|---|
| london | Marrakech Menara Airport | 0.974 | 18 | Aéroport marocain placé à Londres. [Source](https://www.onda.ma/en/Our-Airports/Marrakech-M%C3%A9nara-Airport) |
| bangkok | London Heathrow Airport | 0.715 | 16 | Aéroport britannique placé à Bangkok ; confidence < 0,8, donc déjà écarté du test naïf. [Source](https://www.heathrow.com/transport-and-directions) |
| paris | Le Bistrot de l’Estrapade | 0.994 | 324 | Restaurant, pas un aéroport. [Source](https://bistrotlestrapade.fr/fr) |
| rome | Aeroporto Londra Heathrow | 0.930 | 16 | Aéroport britannique placé à Rome. [Source](https://www.heathrow.com/transport-and-directions) |
| barcelona | Aeropuerto de Madrid | 0.927 | 14 | Aéroport de Madrid placé à Barcelone. [Source](https://www.aena.es/es/aerolineas/aeropuertos-y-destinos/nuestros-aeropuertos/adolfo-suarez-madrid-barajas.html) |
| amsterdam | Luchtverkeersleiding Nederland | 0.952 | 6 | Bureau du contrôle aérien, pas un aéroport indépendant. [Source](https://www.lvnl.nl/organisatie/onze-locaties) |
| lisbon | Snpvac | 0.911 | 23 | Siège du syndicat du personnel navigant, pas un aéroport. [Source](https://site.snpvac.pt/contacto/) |
| sydney | Tullarmarine  Airport Melbourne | 0.899 | 26 | Identité de Melbourne placée à Sydney ; proximité possible du vrai SYD, ne prouve pas un faux ancrage hôtel. [Source](https://www.melbourneairport.com.au/) |
| tokyo | 高松空港 | 0.971 | 18 | Aéroport de Takamatsu, Kagawa, placé à Tokyo. [Source](https://www.pa.skr.mlit.go.jp/general/status/outline/airport_takamatsu.html) |
| dubai | Dubai Airport Freezone Metro Station | 0.980 | 16 | Station de métro G13, pas un aéroport. [Source](https://www.rta.ae/wps/portal/rta/ae/public-transport/metro-stations-map) |
| new_york | Sydney International Airport | 0.812 | 4 | Identité australienne placée à JFK ; ne prouve pas que les hôtels voisins soient sans fonction aéroportuaire. [Source](https://www.sydneyairport.com/info-sheet/privacy) |
| singapore | Changi Airport MRT Station | 0.938 | 10 | Station MRT, pas un aéroport indépendant ; le vrai Changi existe à proximité. [Source](https://www.changiairport.com/en/at-changi/transport-and-directions/getting-to-changi-airport.html) |

Autre cas Bangkok **ambigu**, jamais promu en ancre : `b4949eee-95ee-465f-969a-4a81b71f57f9`, `เชลล์ สนามบินน้ำ`, confidence 0,980. Le nom évoque une station Shell mais la recherche officielle ne confirme pas cette adresse exacte. À revoir après GO.

Même les emprises ont des faux positifs de « majeur » : **Riggin Field**, 49 043 m², dépasse 2 ha mais relève des équipements scolaires/locaux ; la surface ne le transforme pas en MetLife. [Règles municipales d’utilisation](https://ecode360.com/27003448). Cela justifie une liste d’ancres vérifiées plutôt qu’un simple seuil de surface. Aucun taux de faux positifs des polygones n’est annoncé : il demanderait un échantillon aléatoire stratifié vérifié, absent de cette étude.

## Les deux cas propriétaire — et pourquoi un gate géométrique seul échouerait

**Hilton Bangkok Suvarnabhumi Golf Resort & Spa.** L’[hôtel officiel](https://www.hilton.com/en-gb/hotels/bkksvhi-hilton-bangkok-suvarnabhumi-golf-resort-and-spa/golf/) annonce l’accès au Summit Windmill, 18 trous. L’ID `af88de0a-b52f-4b25-bbe1-66a09d3145cd`, walkability 10,84, est **dans** l’emprise golf de 686 899 m² : distance **0 m**, candidat détecté. Mais le même nom existe sous `7c6f8dea-135f-4696-a8b7-39f8f006edd8`, walkability 50,72, à **1 525 m** de cette emprise : non détecté à 500 m. Doublon/coordonnées à résoudre avant F ; ne pas élargir le rayon pour cacher l’incohérence. L’identité du polygone sans nom est inférée de la position et du site hôtelier, non fournie dans son champ `name`.

**Sheraton Hotel, East Rutherford, NJ**, ID `c6278881-6e4a-423e-8e44-c8316203d1d1`, walkability 0,99. Son point (-74,095024 ; 40,809471) est à **1 687 m** de l’emprise `New York New Jersey Stadium` (54 930 m², ID `97dc4f33-4e03-3c97-872c-01598fd1cb62`) et à 1 639 m de Riggin Field. **Il échoue au rayon stade de 1 km.** L’ancien [Sheraton au 2 Meadowlands Plaza](https://bpgsconstruction.com/property/sheraton-hotel-2/) est maintenant présenté comme [The Park Hotel at Meadowlands par l’office de tourisme](https://mlcvb.com/meeting_facilities/the-park-hotel-at-meadowlands/), à proximité de MetLife. Le dossier indique une identité ancienne et un géocodage à vérifier, pas une preuve que ce séjour soit sans fonction. Aucun renommage ni déplacement effectué.

## Décision et reprise

Recommandation à soumettre au propriétaire : inventaire d’ancres majeures vérifiées, avec source et accès, puis contrôle des hôtels voisins et présentation explicite de la fonction ; scores **strictement inchangés**. Ne pas activer le comparateur naïf, ni qualifier automatiquement de « mal placé » un hôtel sans polygone. Les seuils, leur calibration et toute présentation attendent le GO. Coût engagé : **0 €**, aucune dépendance/service payant ajouté.

**F non commencé conformément à l’arrêt explicite de E.** Pas de nouvelle cohorte de 200, pas de vérification externe 200/200, pas de pack v3. Le jeu de cinq cas n’est donc **pas validé 5/5** : A/B/C ont leurs tests, D son gate de lisibilité ; E montre qu’une simple géométrie manque un doublon Hilton et le point Sheraton. Il faut traiter ces ambiguïtés avant de déclarer le futur gate bon. Aucune des quarantaines A/B n’est réhabilitée par ce rapport.

## Reproductibilité et intégrité

[Résultats JSON](bloc-e-anchors.json) : 12 villes, deux périmètres, 12 familles, 885 candidats isolés, sources externes, schémas, assets STAC et SHA-256 des extractions et entrées ETL. [Annexe de calcul](bloc-e-methodology.md) : code de recherche exécuté hors application. Aucun module d’ancrage, champ web, ré-ingestion, score, statut, flag ou sitemap ajouté. Le seuil d’isolement 55 est repris de l’étude antérieure pour comparaison, sans prétendre que les six dimensions soient toutes des densités (la tranquillité est notamment un proxy inverse).

Cette étude remplace les mesures de [l’ancienne faisabilité](destination-type-detection-feasibility.md), qui utilisait des centroïdes de bbox et une population antérieure à A/B. Les rayons, filtres de taille et périmètres diffèrent : ne pas comparer les totaux comme une évolution de qualité à méthode constante.
