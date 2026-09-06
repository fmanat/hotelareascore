# Rapport de décision — Phase 0bis (validation de la demande)

**Date : 06/09/2026 · Rédigé par Claude (recherches web effectuées en session) ·
Décision requise : GO / PIVOT / NO-GO du propriétaire**

## Méthode et limites (à lire d'abord, honnêtement)

J'ai échantillonné ~10 requêtes représentatives des 3 clusters de
`docs/validation.md` via recherche web, plus une recherche de concurrents
directs. Deux limites : (1) mes résultats approchent la composition des SERP
Google mais ne montrent ni le Maps pack ni les **AI Overviews** — or les AI
Overviews répondent probablement aujourd'hui à une partie de ces requêtes,
c'est LE risque non mesuré de ce rapport ; (2) aucune donnée de volume de
recherche (pas d'outil gratuit fiable accessible en session). Le verdict est
donc directionnel, pas définitif.

## Résultats par cluster

### Cluster 1 — `{hôtel} location` (l'hypothèse d'acquisition d'origine)

- **Grandes chaînes** (testé : Premier Inn County Hall, Hoxton Shoreditch) :
  SERP verrouillées par les OTA (Expedia, Hotels.com, Kayak) et leurs pages
  d'avis. Personne ne *répond* à la question, mais le terrain est saturé de
  domaines très forts. **Opportunité : 0–1.**
- **Boutique/indépendants** (testé : Memmo Alfama) : les OTA sont là, mais des
  **petits sites de curation indépendants rankent** (secretplaces,
  greatsmallhotels, joandso, timetomomo). Preuve d'existence que le long-tail
  hôtel indépendant est jouable — exactement le pari 70/30 de
  `docs/seo-policy.md §2`. Personne n'y répond avec des données, uniquement de
  la prose marketing. **Opportunité : 2.**

### Cluster 2 — intention de zone par ville (le gagnant net)

Testé : `quiet area to stay in London`, `where to stay in Lisbon without a
car`, `best area to stay in Bangkok first time near BTS`, `is Sukhumvit a good
area`.
- Les SERP sont tenues par : blogs de voyage indépendants (earthtrekkers,
  santorinidave, geekyexplorer, thaiest…), contenu SEO d'hôtels
  auto-promotionnel (Georgian House, Eccleston Square), guides OTA génériques,
  et **forums** (Fodors — un fil de 2003 ranke encore).
- Aucun acteur ne répond avec des données calculées. Les incumbents sont des
  blogs solo — battables par un outil réellement utile.
- Des sites tenus par une seule personne dominent ces requêtes → un nouveau
  domaine peut percer sur ce cluster. **Opportunité : 2–3 sur toutes les
  requêtes testées.**

### Cluster 3 — intention outil (`hotel location checker`…)

Aucun outil dédié ne ranke ; uniquement des listicles génériques de très basse
qualité (« 7 things to check before booking »). Le concept est inoccupé, mais
le volume de recherche sur ces formulations est incertain. **Opportunité : 2,
volume non prouvé.**

### Pépite trouvée en passant

Un fil **Tripadvisor du forum Londres** où un voyageur demande explicitement
« un site de walkability score pour comparer des quartiers » à Londres — et la
communauté répond en substance « ça n'existe pas, utilise Google Maps à la
main, Walk Score ne marche bien qu'aux US ». C'est la demande exacte de notre
produit, formulée par un utilisateur réel, restée sans offre hors
Amérique du Nord.

## Concurrence directe (complète le scan §2.3)

- **Walk Score** (Redfin) : le cousin méthodologique. Scores limités
  US/Canada/Australie ; a tenté des intégrations hôtelières (Expedia/AARP
  2011, Hipmunk 2012) aujourd'hui mortes ; vend une API voyage. Sa critique
  publique documentée (ignore les barrières physiques, le contexte routier)
  est précisément ce que nos 6 dimensions + proxy calme corrigent.
- Aucun produit « surroundings calculés au niveau hôtel, mondial » trouvé.
  L'angle reste inoccupé.

## Lecture des critères (`docs/validation.md §3`)

- **KILL ?** Non — les conditions kill exigent zéro requête à opportunité ≥ 2
  ET aucun gap concurrentiel. On observe l'inverse sur les clusters 2 et 3, et
  le gap concurrentiel est réel et documenté.
- **PIVOT ?** Partiellement — le signal est nettement plus fort sur
  l'intention *ville/zone* que sur les requêtes hôtel de chaîne. Mais le plan
  actuel intègre déjà cette asymétrie : pages ville toujours indexables,
  pages hôtel limitées à une cohorte pilote mesurée, biaisée indépendants.
  Le plan tel qu'écrit EST déjà le pivot doux que les données suggèrent.
- **GO ?** La condition « cluster ville montre un long-tail clair » est
  remplie sur l'échantillon. Reste la seconde condition, qui n'appartient
  qu'au propriétaire : accepter que le Stage A (~300 visites/j) rapporte
  ~124 €/mois au cas médian, que les mois 1–6 sont une expérience et pas un
  revenu, et le budget temps de §2.5.

## Recommandation

**GO conditionnel, avec deux inflexions :**
1. Considérer les **pages ville/zone comme le centre de gravité SEO
   principal** dès la Phase 4 (elles étaient déjà « toujours indexables » —
   on assume désormais qu'elles portent l'acquisition), la cohorte pilote
   hôtels restant l'expérience mesurée qu'elle était.
2. Ajouter aux mesures de la cohorte (J+90) une **vérification AI Overviews**
   : noter, pour chaque requête suivie dans GSC, si un AI Overview y répond.
   C'est le risque n°1 non mesuré aujourd'hui.

**Ce qui reste à faire par le propriétaire avant d'enregistrer le GO :**
une passe de 30–45 min sur Google réel (connecté à rien, navigation privée)
pour vérifier deux choses que je ne vois pas : la présence d'AI Overviews sur
~10 des requêtes ci-dessus, et l'autocomplete (taper `hilton london loc…`,
`quiet area to stay in…` et noter ce que Google propose — proxy de volume).
Si les AI Overviews répondent déjà proprement à la majorité des requêtes du
cluster 2 → repasser en PIVOT (B2B/widget). Sinon → GO, à consigner dans
STATE.md.
