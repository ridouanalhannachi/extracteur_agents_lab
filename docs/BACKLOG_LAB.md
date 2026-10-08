# Backlog EDT/RH — 8 octobre 2026

Base vérifiée : `0bdf629`, PR 1 à 13 fusionnées et aucune PR ouverte au début du
cycle. Les lots interactifs I2 à I6 sont intégrés : ne pas les refaire.

## Lot I7 — Ouvrir une séance trouvée dans son contexte

Diagnostic confirmé : la Recherche globale trouvait les séances et connaissait déjà
leurs identifiants d'emploi, version et séance, mais n'offrait aucune action vers
l'Historique. L'utilisateur devait retrouver manuellement la bonne version.

Livrable développé : sélection native d'une séance trouvée et bouton « Ouvrir dans
l'historique ». La transition transmet uniquement les trois identifiants, les valide
par jointure SQLite, ouvre l'emploi et la version exacts — y compris archivés — puis
marque la séance avec une ligne dédiée. L'intention est consommée une fois ; le focus
reste présent aux réexécutions jusqu'à « Afficher toutes les séances ». Une cible
supprimée ou incohérente est refusée sans afficher un contexte trompeur.

Critères : V1 archivée exacte ouverte malgré V2 active, libellés identiques séparés
par IDs, focus conservé après rerun puis effaçable, filtres des autres versions
préservés, erreur explicite et snapshot SQLite identique.

État final : 16 tests ciblés puis 81 tests et 21 sous-tests réussis ;
`git diff --check` et compilation réussis. La revue indépendante a d'abord relevé
des libellés ambigus pour deux séances du même créneau. Enseignant, groupe et salle
ont été ajoutés ; un AppTest sélectionne désormais la bonne séance parmi deux cas
semblables. Revue finale acceptée sur l'arbre corrigé.

## Suite

1. I8 : diagnostiquer l'ouverture contextuelle des résultats Version/Changement.
2. D5 : validation petit écran, clavier et contraste dans un navigateur réel.
3. L3 : restauration conservatrice après les besoins interactifs.

Aucune dépendance, donnée réelle ou secret. Drive reste désactivé. Aucun déploiement.
