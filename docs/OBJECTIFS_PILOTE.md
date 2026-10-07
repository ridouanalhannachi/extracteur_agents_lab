# Agent Pilote — objectifs EDT/RH

## Cadre et état examiné — 2026-10-07

Dépôt exclusif : `ridouanalhannachi/extracteur_agents_lab`.
Base : `d31e253` (`main`, fusion de la PR nº 6). Le responsable a confirmé que
les PR nº 1 à 6 sont fusionnées et qu'aucune PR n'est ouverte au début du cycle.
D1 et D2a sont donc intégrés ; leurs résultats consignés restent des preuves
historiques et non des tests exécutés pendant ce cycle.

La priorité explicite du 6 octobre reste le design et l'ergonomie. Pas de
migration de framework, de nouvelle dépendance, de déploiement ni de modification
du dépôt d'origine. Drive reste désactivé. Les fusions par PR du laboratoire sont
autorisées après validation de la version exacte et respect des protections ;
aucun push direct sur `main`.

## Objectifs actifs (maximum cinq)

| Priorité / objectif | Problème observé ou hypothèse | Bénéfice utilisateur | Coût / risque | Dépendances | Critère mesurable | État |
|---|---|---|---|---|---|---|
| 1 — D3a : repères import → correction → enregistrement/export | **Observé dans `app.py`** : la barre latérale affiche « 1. Fichiers », « 2. PDF scannés », puis « 3. Export » alors qu'elle ne contient aucune action d'export ; la correction est le deuxième onglet et l'enregistrement le quatrième. Les actions existantes sont donc présentées dans un ordre difficile à anticiper. | Comprendre dès l'arrivée où déposer un document, où corriger les séances et où enregistrer ou exporter le résultat. | Faible à moyen / modéré : conserver les mêmes widgets, clés, données et actions métier. | D1 et D2a intégrés ; composants Streamlit natifs ; fixture assainie. | Les étapes existantes sont nommées et ordonnées sans faux bouton ; AppTest contrôle le guide avant import, les tests structurels contrôlent onglets, états et clés ; suite complète réussie. Une capture navigateur reste nécessaire pour déclarer le rendu visuel validé. | **Vérifié localement et accepté indépendamment : 49 tests** |
| 2 — D3b : validation et conservation après correction | **Observé** : l'import est mémorisé automatiquement avant l'éditeur détaillé ; après correction, l'utilisateur doit employer « Enregistrer comme nouvelle version » dans un autre onglet. **Hypothèse à vérifier** : cette séparation peut faire croire que les corrections sont déjà conservées. | Savoir sans ambiguïté si la version corrigée est enregistrée avant de quitter ou d'exporter. | Moyen / modéré à élevé : risque direct sur les versions et la persistance. | D3a ; socle L1 ; diagnostic séparé avant changement métier. | Sur données fictives, corriger une séance, enregistrer, rouvrir puis exporter conserve exactement la correction ; les états non enregistré/enregistré sont distincts et aucun succès distant n'est annoncé. | Proposé, hors lot D3a |
| 3 — D4 : états vides, erreurs et sauvegardes explicites | **Hypothèse** : la cohérence des messages entre écrans reste à auditer ; L2a interdit déjà les remplacements distants. | Distinguer absence de données, erreur et enregistrement local confirmé. | Moyen / modéré : ne pas annoncer une réussite non établie. | D3b ; garde L2a ; Drive désactivé. | Parcours vide, correction non enregistrée, succès local et échec simulé couverts ; aucun faux succès distant ; mémoire intacte. | Proposé |
| 4 — D5 : petits écrans et accessibilité | **Limite confirmée** : D1 et D2a n'ont pas été inspectés dans un navigateur réel ; comportement clavier, focus et affichage étroit restent inconnus. | Utiliser les fonctions principales sur un petit écran et au clavier, avec libellés et contrastes lisibles. | Moyen / faible à modéré : ajustements CSS/structure à garder légers. | Lots D1 à D4 ; navigateur réellement disponible. | À 360 px, aucune action principale n'est masquée ; ordre de focus logique, libellés accessibles et contraste texte/fond ≥ 4,5:1 pour le texte normal. | Proposé |
| 5 — L3 : restauration conservatrice | **Hypothèse conservée** : une base distante valide mais ancienne peut menacer les corrections locales ; aucun nouveau défaut reproduit dans ce cycle. | Restaurer sans perdre les dernières corrections. | Moyen / élevé : remplacement de base. | Diagnostic séparé ; SQLite temporaire et Drive simulé uniquement. | Simulations d'interruption, corruption et ancienneté ; comparer séances, versions, validations et intégrité locale. | Proposé, différé après priorités design |

## Socle design intégré à préserver

- D1 — accueil et navigation : intégré via PR nº 5 à `58ac343` ; 39 tests
  historiques. Le rendu navigateur/mobile n'a pas été vérifié.
- D2a — catalogue et filtres de l'historique : intégré via PR nº 6 à
  `d31e253` ; 43 tests historiques. Le rendu navigateur/mobile et le clavier
  n'ont pas été vérifiés.

Ces lots ne sont plus des objectifs actifs et ne doivent pas être recommencés
sans défaut reproduit.

## Lot retenu et fichiers attribués

Un seul lot : **D3a — repères import → correction → enregistrement/export**, sur
la branche `lab/design-import-guidance`. Le lot réorganise uniquement la
présentation des fonctions déjà présentes dans l'écran « Emplois du temps » :
libellés de la barre latérale, guide d'étapes et ordre/titres des zones ou onglets
concernés. Il n'ajoute aucune fonction, statistique ou dépendance.

Hors lot : algorithmes d'extraction, règles de complétude, auto-enregistrement,
création/activation des versions, contenu du classeur Excel, assistant local,
requêtes SQLite, Drive et autres modules. D3a ne prétend pas résoudre l'hypothèse
de conservation formulée dans D3b.

- Pilote : uniquement `docs/OBJECTIFS_PILOTE.md` et `docs/BACKLOG_LAB.md`.
- Développeur : `app.py` et un nouveau test UI ciblé ; préserver les clés de
  widgets, les appels métier et les conditions d'activation des actions.
- Vérificateur indépendant : lecture du diff exact et exécution des tests ciblés
  puis complets ; aucun fichier attribué en écriture.
- Éclaireur : `docs/VEILLE_TECHNIQUE.md` uniquement ; rechercher une technologie
  seulement si un défaut concret l'exige. Les composants Streamlit natifs
  suffisent a priori.
- Responsable : `docs/JOURNAL_LAB.md`, `docs/REPRISE_AGENTS.md`, publication et
  fusion conditionnelle via PR ; aucune modification directe de `main` et aucun
  déploiement.

## Critères d'acceptation D3a

1. Avant import, l'écran indique trois étapes cohérentes : importer, corriger et
   vérifier, puis enregistrer ou exporter ; les libellés distinguent clairement
   l'enregistrement local de l'export Excel.
2. La barre latérale ne présente plus « Export » comme une section contenant une
   action lorsqu'elle ne contient qu'une explication ; aucun bouton fictif n'est
   ajouté.
3. Après chargement d'une fixture fictive, les actions existantes de correction,
   enregistrement de version et téléchargement restent accessibles, avec les
   mêmes conditions d'activation et les mêmes effets métier.
4. Aucun changement n'affecte extraction, données éditées, persistance, versions,
   synchronisation désactivée ou octets exportés ; test ciblé et suite complète
   réussis sur l'arbre exact.
5. Une comparaison avant/après n'est déclarée que si l'interface peut être lancée
   et capturée dans un vrai navigateur. AppTest seul prouve la structure et le
   parcours automatisé, pas le rendu visuel, le mobile ou le focus clavier.
