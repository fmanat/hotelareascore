# STATE.md — état du projet

> Source de vérité pour chaque reprise. Les règles sont dans AGENTS.md/CLAUDE.md.
> Mise à jour : mission de nuit du 2026-09-12. Historique détaillé dans les rapports et ADR.

## Digest de nuit — G → C → D → E, arrêt obligatoire à E

**G, C et D sont sur origin/main avec leurs cinq jobs CI verts. E est le
rapport livré dans le commit de clôture de ce bloc ; son hash et sa CI sont
à lire dans le journal Git/Actions. F n’a pas été commencé : l’instruction
« PRODUIS LE RAPPORT ET ARRÊTE-TOI » de E exige un nouveau GO.**
Aucun déploiement, login OAuth, dashboard, nouveau projet Pages, flag,
indexation, sitemap public, compte ou dépense pendant cette mission.

| Bloc | Commit poussé | Résultat |
|---|---|---|
| G | `6a2af23` | Wrangler 4.131.1 + `make deploy`, exclusivement projet existant `staycontext` ; procédure manuelle prête, jamais exécutée |
| C | `f0a8ea3` | 33 779 hébergements typés, 24 452 `hotel` ; seul ce type est éligible, sans activation |
| D | `6db8b1c` | 170 noms débloqués, dont 145 hôtels ; affichage Latin (Original) hôtels/POI, slugs conservés |
| E | commit de ce rapport | 12 villes : 2 874 hôtels isolés, 623 proches d’une emprise candidate, 2 251 sans emprise observée ; **pas des identités/fonctions confirmées** |
| F | aucun | Cohorte 200, vérification externe et pack v3 **non réalisés**, en attente du GO après E |

**G — incident de production.** La connexion Git Pages est cassée selon le
propriétaire ; production figée sur `77e49b3`, donc A/B non servis. Dernier
contrôle demandé : Singapore Boys’ Home encore HTTP 200 le 2026-09-11 à
21:14:34 UTC, dix minutes après le premier contrôle. CI verte ≠ déploiement.
Le propriétaire doit suivre le [runbook](reports/phase-4-launch-runbook.md),
faire `web/node_modules/.bin/wrangler login` puis `make deploy` et
`make verify-prod`, et contrôler la disparition réelle des pages A/B.
Aucun déclenchement Cloudflare forcé. Projet de production : **staycontext**.

**C — répartition :** 24 452 hôtels, 266 aparthotels, 1 049 appartements
avec services, 950 logements entiers, 2 237 hostels, 3 298 guesthouses/B&B,
1 527 inconnus. Tous restent cherchables avec leur type. OYO Home du
propriétaire classé logement entier ; aucun bannissement global d’OYO.
14 Sonder/Domio inconnus à vérifier. 2 412 candidats théoriques parmi les
rejected lodging ; **zéro ré-ingestion**, aucune promesse de récupération.
[Rapport et ventilation 12 villes](reports/bloc-c-accommodation.md), ADR-019.

**D — noms :** 4 824 noms non latins examinés, 170 romanisés ; 4 669 noms
restent inéligibles, incluant les noms numériques/manquants. Variantes
Overture prioritaires ; fallback AnyAscii limité aux écritures documentées.
Han/kanji, thaï, arabe, etc. sans variante fiable restent originaux/noindex.
La lisibilité ne prouve pas une identité d’hôtel. 18 occurrences de POI
utilisent une variante source latine. Aucun slug ni score changé.
[Rapport D](reports/bloc-d-names.md), [options FR, rapport seulement](reports/i18n-options.md), ADR-020.
Validation finale du code : **464 tests + 1 xfail historique**, typecheck
propre, build **15 721 pages**, assertions SEO, **64 E2E** desktop/mobile ;
[CI D verte](https://github.com/fmanat/hotelareascore/actions/runs/34655189217).

**E — étude seulement :** sur 33 779 hébergements, 4 151 isolés, 885 avec
emprise candidate, 3 266 sans. Sous-ensemble hôtel : 2 874 / 623 / 2 251.
Congrès/expo/aéroport civil/casino insuffisamment couverts par les polygones ;
« sans emprise » ne permet donc pas d’affirmer « mal placé ».
12 contre-exemples de POI vérifiés (échantillon choisi, pas un taux global).
Hilton golf : une identité dans le golf, un doublon à 1 525 m ; Sheraton
East Rutherford : ancienne identité et point à 1 687 m du stade, échoue au
rayon proposé. **Une simple géométrie ne passe pas tous les cas propriétaire.**
[Rapport E](reports/bloc-e-anchors.md), [données et ambiguïtés](reports/bloc-e-anchors.json).
Aucune implémentation d’ancrage ; scores 1.2.1 inchangés.

## Décisions en attente du propriétaire

- Déployer manuellement G, puis vérifier A/B en production.
- Lire E et donner le GO avant toute implémentation et reprise de F.
  Les seuils du rapport sont des hypothèses de mesure, pas des décisions produit.
- F devra reconstruire les 200 depuis zéro avec tous les gates, exclure les
  ancres en attente, vérifier extérieurement chaque hôtel/réception avec source,
  livrer le pack v3 de 15 fiches et inscrire ce gate obligatoire dans seo-policy.
  **Le jeu des cinq cas n’est pas validé 5/5 et aucun pack v3 n’existe encore.**
- Ambigus à revoir dans F : les **26 quarantaines B** ([liste](reports/bloc-b-brands.md)),
  B&B Maru Shelter, Refuge Hostel, Halfway House Farm, appartement Health Care City
  ([A](reports/bloc-a-institutions.md)) ; aucune réhabilitation effectuée.
  Ajouter les 14 opérateurs mixtes de C, les deux coordonnées Hilton et
  l’identité/position Sheraton de E. Le POI Shell Bangkok reste ambigu dans E.
- Phase 4 : compléter les mentions légales de FrenchSquare Ltd (numéro de
  société, siège, contact, dates et droit applicable), valider la nouvelle
  cohorte et son échantillon, connecter GSC, autoriser explicitement l’indexation.

## A/B — acceptés par contre-audit externe avant la mission

A (`1d4e4ef`) : **46 / 33 966 exclusions** d’institutions ; 1 825 Home/House
et 1 061 hostel conservés au checkpoint A. ADR-016 et [rapport](reports/bloc-a-institutions.md).
B (`fbbc0c4`, clôture `ef39fb9`) : **141 / 33 920 exclusions**, 33 779 conservés ;
5 programmes, 63 bureaux, 73 marques ombrelles. **26 incertains quarantainés**,
11 alias d’établissements protégés. [Rapport](reports/bloc-b-brands.md), ADR-017.
Le signal générique B reste **mesuré, non activé** : OR 273 avant B / 269 après,
AND 0 ; les 158 pays MY dans la bbox Singapore ne prouvent pas une mauvaise adresse.
L’ancienne cohorte 200 n’a plus que 197 identités survivantes après A/B ;
ancien pack v2, proposition et dry-run 214 URL sont **obsolètes**.

## Phase et risques conservés

Phase 3 close (GO 2026-09-07), Phase 4 bloquée sur les éléments ci-dessus.
12 villes, release utilisé **2026-08-19.0**, score_version **1.2.1**.
Transit/restaurants/nightlife gelés. Quietness et family_convenience sont des
proxies minces à modérés, pas des dimensions robustement validées ; family
Spearman 0,5052, variations fortes par ville (ADR-009). Labels golden set
produits par IA, non vérifiés par le propriétaire (`tests/golden/LABELS-PROVENANCE.md`).
Aucun nouveau calibrage sans revue explicite. Tous les flags restent OFF.

Les gates A/B/C/D ne résolvent pas tous les défauts d’identité : noms non
latins de non-hôtels, sous-établissements passant l’allowlist, coordonnées
erronées restent possibles. Les spécimens historiques sont dans
[destination-name-mismatch-audit.md](reports/destination-name-mismatch-audit.md)
et les rapports Phase 3 ; ne pas les considérer tous corrigés. D n’est pas
un classificateur sémantique multilingue. E remplace l’ancienne étude d’ancrage.

Pas de récupération automatique de rejected lodging : décision propriétaire
conservée ; les recherches sans résultat via `search_events` seront le KPI
par ville après lancement. Supabase non provisionné bloque encore le diff
mensuel de scores ; POI lourds restent hors serving DB. Affiliations attendent
le site et son trafic. Projections de trafic non validées ; AI Overviews à
mesurer au jour 90 (seo-policy/validation). CSP reste Report-Only ; www→apex
reste ouvert, canonicals présents. Pas de nouvelle action sur ces chantiers.

Ancienne boucle de surveillance **arrêtée sur ordre propriétaire** ; ne pas
la relancer. Les idées hors mission (a11y, outil golden-labeler, analytics,
redirection www, etc.) restent non autorisées : voir
[pre-launch-readiness](reports/pre-launch-readiness.md). Aucun chantier ajouté.

## Coûts et références

Septembre 2026 : **0 € engagé cette mission**, dépendances gratuites, aucun
service ajouté. Budget propriétaire inchangé (≤200 € setup, ≤50 €/mois).
Marque StayContext / staycontext.com ; code interne hotelareascore (ADR-012).
Historique des décisions : ADR-001 à ADR-020 et rapports datés ; Git/Actions
font foi pour les commits effectivement poussés et leur validation.
