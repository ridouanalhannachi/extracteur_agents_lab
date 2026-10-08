# Objectifs EDT/RH — 8 octobre 2026

Base distante vérifiée : `0bdf629`, fusion de la PR nº 13. Aucune PR ouverte au
démarrage. Priorité : fermer les parcours interactifs utiles sans modifier en place
les versions enregistrées. Drive désactivé, aucun déploiement, un lot par cycle.

| Objectif | Problème observé / bénéfice | Priorité, coût / risque | Dépendances | Critère mesurable | État |
|---|---|---|---|---|---|
| I7 — Ouvrir une séance trouvée dans son contexte | La recherche imposait de retrouver manuellement version et séance | 1, faible à moyen / faible | I5, navigation persistante | Une action ouvre la bonne version, marque la séance, conserve le focus au rerun et reste en lecture seule | Vérifié : 81 tests + 21 sous-tests ; revue indépendante acceptée |
| I8 — Étendre l'action aux versions/changements | Hypothèse : les autres onglets de recherche imposent encore une navigation manuelle | 2, faible à moyen / faible | I7 | Diagnostic puis action vers le contexte exact, sans dupliquer I7 | Proposé |
| D5 — Petit écran et clavier | Validation navigateur réelle indisponible | 3, moyen / faible | Navigateur utilisable | Actions visibles à 360 px, focus logique, contraste 4,5:1 | Bloqué pour validation visuelle |
| L3 — Restauration conservatrice | Hypothèse : restauration ancienne menace une correction | 4, moyen / élevé | Diagnostic SQLite temporaire, Drive simulé | Ancienneté/corruption/interruption sans perte | Différé |

I6/PR13 est intégré et sort des objectifs actifs. I7 reste borné à la transition
Recherche globale → Historique pour une séance. Aucune dépendance ajoutée.
