# Backlog EDT/RH — 8 octobre 2026

Base vérifiée : `5f981ea`, PR 1 à 12 fusionnées et aucune PR ouverte au début du
cycle. Les lots interactifs I2 à I5 sont intégrés : ne pas les refaire.

## Lot I6 — Correction ciblée depuis la Vérification globale

Diagnostic confirmé : la console sélectionnait et marquait une séance « À revoir »,
mais toutes ses cartes étaient en lecture seule. Une erreur exigeait de retrouver le
document et de recommencer le parcours d'import.

Livrable développé : bouton « Corriger cette séance », formulaire prérempli,
préparation locale avec diff explicite, annulation sans écriture et confirmation avant
« Enregistrer comme nouvelle version ». La correction remplace uniquement la séance
ciblée dans la nouvelle version ; l'ancienne version et les autres séances restent
inchangées. Une soumission identique est dédupliquée. Une durée invalide est refusée.
Un contrôle transactionnel refuse une correction fondée sur une version devenue
inactive afin de ne pas écraser silencieusement un changement concurrent.

Critères : préparation en lecture seule, annulation, V1 intacte, V2 active, autre
séance intacte, doublon sans V3, base obsolète refusée sans mutation, durée invalide
sans version, échec de synchronisation distingué et parcours AppTest complet.

État : 7 tests ciblés et 6 sous-tests, puis 76 tests et 21 sous-tests réussis.
Revue indépendante acceptée après correction des durées non finies et du risque de
version concurrente. Compilation Python et `git diff --check` réussis.

## Suite

1. I7 : ouvrir un résultat de recherche dans sa version/séance.
2. D5 : validation petit écran, clavier et contraste dans un navigateur réel.
3. L3 : restauration conservatrice après les besoins interactifs.

Aucune dépendance, donnée réelle ou secret. Drive reste désactivé. Aucun déploiement.
