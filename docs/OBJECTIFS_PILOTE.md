# Objectifs EDT/RH — 7 octobre 2026

Base distante vérifiée : `03425a1`, fusion de la PR nº 9. Aucune PR ouverte au
démarrage. Priorité : interactions utiles et retours exacts. Drive désactivé,
aucun déploiement, un seul lot par cycle.

| Objectif | Problème observé / hypothèse | Bénéfice | Priorité, coût / risque | Dépendances | Critère mesurable | État |
|---|---|---|---|---|---|---|
| I3 — Activation contextuelle d'une version | Observé : version sélectionnable mais aucune action disponible | Revenir explicitement à une version antérieure sans perdre l'historique | 1, moyen / modéré | I2/PR9, SQLite | Confirmation obligatoire ; une seule active ; sélection stable ; séances et commentaires intacts | Vérifié : 62 tests + 15 sous-tests, revue indépendante acceptée |
| I4 — Export contextuel d'une version | Hypothèse : exporter la version consultée réduit les erreurs de sélection | Obtenir le fichier de la version voulue | 2, faible / faible | I3 | Export identifié Vn sans changement d'état | Proposé après I3 |
| D5 — Petit écran et clavier | Limite observée : pas de navigateur disponible | Actions accessibles à 360 px et au clavier | 3, moyen / faible | Navigateur utilisable | Focus logique, actions visibles, contraste texte 4,5:1 | Bloqué pour validation visuelle |
| L3 — Restauration conservatrice | Hypothèse : restauration ancienne menace corrections | Conserver mémoire locale | 4, moyen / élevé | Diagnostic SQLite temporaire, Drive simulé | Ancienneté/corruption/interruption sans perte | Différé |

D1/PR5, D2a/PR6, D3a/PR7, D3b/PR8 et I2/PR9 sont intégrés : ne pas les refaire.

## Lot I3 et attribution

Branche `lab/version-actions`. Développeur : `edt_memory.py` et tests transactionnels.
Responsable : `edt_history_ui.py`, AppTest et documents. Pilote/Éclaireur et
vérificateur : lecture seule.

Une version archivée n'est activée qu'après sélection et confirmation. Une
transaction sérialisée valide son emploi, archive l'ancienne active puis active la
cible. Aucun contenu de version n'est réécrit et aucune dépendance n'est ajoutée.
