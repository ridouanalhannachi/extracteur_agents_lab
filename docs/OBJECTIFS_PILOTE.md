# Objectifs EDT/RH — 7 octobre 2026

Base distante vérifiée : `67df619`, PR 1 à 7 intégrées, aucune PR ouverte au
commencement. Priorité : interactions utiles et retour exact après action.
Un lot par cycle ; uniquement le laboratoire, Drive désactivé, aucun déploiement.

| Objectif | Problème observé / hypothèse | Bénéfice | Priorité, coût / risque | Dépendances | Critère mesurable | État |
|---|---|---|---|---|---|---|
| D3b — État des séances enregistrées | Observé : auto-save avant éditeur, succès manuel transitoire | Savoir si les séances affichées existent sur disque | 1, moyen / modéré | D3a, SQLite, hash canonique existant | Modification → non enregistré ; sauvegarde → Vn ; réexécution conserve état ; erreur sans faux succès ; ancienne version signalée archivée | Vérifié : 55 tests, revue indépendante acceptée |
| I2 — Correction et annulation | Hypothèse : retour arrière difficile, à diagnostiquer | Corriger sans perdre les saisies | 2, moyen / modéré | D3b | Parcours correction/annulation testable sans perte ; diagnostic préalable | Proposé |
| I3 — Actions contextuelles versions | Hypothèse : actions dispersées dans historique | Agir sur la version sélectionnée | 3, moyen / modéré | D3b | Sélection stable et confirmation exacte ; aucune activation implicite | Proposé |
| D5 — Petit écran et clavier | Limite observée : pas de validation navigateur | Actions accessibles à 360 px et au clavier | 4, moyen / faible | Navigateur utilisable | Focus logique, actions visibles, contraste texte 4,5:1 | Proposé |
| L3 — Restauration conservatrice | Hypothèse : restauration ancienne menace corrections | Conserver mémoire locale | 5, moyen / élevé | Diagnostic SQLite temporaire, Drive simulé | Ancienneté/corruption/interruption sans perte | Différé |

D1/PR5, D2a/PR6 et D3a/PR7 sont intégrés : ne pas les refaire.

## Lot D3b et attribution

Branche `lab/design-save-state`. Responsable : `app.py`, `edt_save_state.py`,
`tests/test_save_state.py`, documents de relais. Pilote et vérificateur indépendant :
lecture seule, diagnostic puis revue/tests. Veille exercée par le Pilote : pas de
nouvelle technologie justifiée.

Le statut porte seulement sur les séances de la cible sélectionnée dans l'onglet
Enregistrer / Versions, selon année/période/filière/semestre. Il compare les données
SQLite, pas un drapeau session. Les autres emplois, les éditions Intervenants
(export seul) et la provenance Source PDF/Page ne sont pas couverts par ce statut.
Les opérations métier, clés des widgets, extraction et export restent identiques.
