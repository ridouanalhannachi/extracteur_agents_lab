# Objectifs EDT/RH — 8 octobre 2026

Base distante vérifiée : `5f981ea`, fusion de la PR nº 12. Aucune PR ouverte au
démarrage. Priorité : fermer les parcours interactifs utiles sans modifier en place
les versions enregistrées. Drive désactivé, aucun déploiement, un lot par cycle.

| Objectif | Problème observé / bénéfice | Priorité, coût / risque | Dépendances | Critère mesurable | État |
|---|---|---|---|---|---|
| I6 — Corriger la séance vérifiée | La console signale « À revoir » mais restait en lecture seule ; évite de retrouver et réimporter le document | 1, moyen / moyen | Versionnage SQLite existant | Préparer/annuler sans écriture ; confirmer crée une seule V2 active, V1 et autres séances intactes | Vérifié : 76 tests + 21 sous-tests, revue indépendante acceptée |
| I7 — Ouvrir un résultat de recherche dans son contexte | La recherche impose de retrouver manuellement version/séance | 2, faible à moyen / faible | I5, navigation persistante | Une action ouvre la bonne version et conserve la sélection | Proposé |
| D5 — Petit écran et clavier | Validation navigateur réelle indisponible | 3, moyen / faible | Navigateur utilisable | Actions visibles à 360 px, focus logique, contraste 4,5:1 | Bloqué pour validation visuelle |
| L3 — Restauration conservatrice | Hypothèse : restauration ancienne menace une correction | 4, moyen / élevé | Diagnostic SQLite temporaire, Drive simulé | Ancienneté/corruption/interruption sans perte | Différé |

I5/PR12 est intégré et sort des objectifs actifs. I6 reste borné au formulaire de
correction, au garde-fou de version active et aux tests. Aucune dépendance ajoutée.
