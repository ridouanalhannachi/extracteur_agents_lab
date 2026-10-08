# Objectifs EDT/RH — 7 octobre 2026

Base distante vérifiée : `a59d3cf`, fusion de la PR nº 11. Aucune PR ouverte au
démarrage. Priorité : interactions utiles et retours exacts. Drive désactivé,
aucun déploiement, un seul lot par cycle.

| Objectif | Problème observé / hypothèse | Bénéfice | Priorité, coût / risque | Dépendances | Critère mesurable | État |
|---|---|---|---|---|---|---|
| I5 — Filtres des séances d'une version | Observé : toutes les séances sont affichées sans recherche ni filtre | Trouver immédiatement une séance dans Vn sans quitter l'Historique | 1, faible / faible | I4/PR11 | Recherche + Jour/Enseignant/Groupe, compteur, reset, état zéro, isolation Vn | Vérifié : 69 tests + 15 sous-tests, revue indépendante acceptée |
| D5 — Petit écran et clavier | Limite observée : pas de navigateur disponible | Actions accessibles à 360 px et au clavier | 2, moyen / faible | Navigateur utilisable | Focus logique, actions visibles, contraste texte 4,5:1 | Bloqué pour validation visuelle |
| L3 — Restauration conservatrice | Hypothèse : restauration ancienne menace corrections | Conserver mémoire locale | 3, moyen / élevé | Diagnostic SQLite temporaire, Drive simulé | Ancienneté/corruption/interruption sans perte | Différé |

D1/PR5, D2a/PR6, D3a/PR7, D3b/PR8, I2/PR9, I3/PR10 et I4/PR11 sont intégrés : ne pas les refaire.

## Lot I5 et attribution

Branche `lab/session-filters`. Développeur : `edt_history_ui.py` et test des filtres.
Responsable : documents et validation. Pilote/Éclaireur et vérificateur : lecture seule.

Les contrôles sont affichés uniquement pour la version principale sélectionnée et
leurs clés sont isolées par emploi/version. Ils filtrent le tableau, jamais l'Excel
complet, SQLite ou l'activation. Aucune dépendance ajoutée.
