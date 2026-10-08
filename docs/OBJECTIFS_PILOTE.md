# Objectifs EDT/RH — 7 octobre 2026

Base distante vérifiée : `b41b044`, fusion de la PR nº 10. Aucune PR ouverte au
démarrage. Priorité : interactions utiles et retours exacts. Drive désactivé,
aucun déploiement, un seul lot par cycle.

| Objectif | Problème observé / hypothèse | Bénéfice | Priorité, coût / risque | Dépendances | Critère mesurable | État |
|---|---|---|---|---|---|---|
| I4 — Export contextuel d'une version | Observé : version consultable mais export seulement disponible dans le parcours d'import | Obtenir le fichier de la version réellement sélectionnée | 1, faible / faible | I3/PR10 | V1/V2 donnent le contenu et nom Vn attendus sans changement SQLite | Vérifié : 65 tests + 15 sous-tests, revue indépendante acceptée |
| D5 — Petit écran et clavier | Limite observée : pas de navigateur disponible | Actions accessibles à 360 px et au clavier | 2, moyen / faible | Navigateur utilisable | Focus logique, actions visibles, contraste texte 4,5:1 | Bloqué pour validation visuelle |
| L3 — Restauration conservatrice | Hypothèse : restauration ancienne menace corrections | Conserver mémoire locale | 3, moyen / élevé | Diagnostic SQLite temporaire, Drive simulé | Ancienneté/corruption/interruption sans perte | Différé |

D1/PR5, D2a/PR6, D3a/PR7, D3b/PR8, I2/PR9 et I3/PR10 sont intégrés : ne pas les refaire.

## Lot I4 et attribution

Branche `lab/version-export`. Développeur : `edt_history_ui.py` et test d'export.
Responsable : documents et validation. Pilote/Éclaireur et vérificateur : lecture seule.

Le téléchargement réutilise les helpers Excel existants et cible l'identifiant de
la version sélectionnée. Le nom contient l'emploi et Vn ; l'action est désactivée
sans séance et ne modifie ni version active ni SQLite. Aucune dépendance ajoutée.
