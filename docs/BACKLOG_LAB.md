# Backlog EDT/RH — 7 octobre 2026

Base vérifiée : `a59d3cf`, PR 1 à 11 fusionnées, aucune PR ouverte au début du
cycle. Le socle de fiabilité et les lots interactifs jusqu'à I4 sont intégrés.

## Lot en cours : I5 — Filtres des séances de la version sélectionnée

Diagnostic confirmé : après sélection de Vn, l'Historique affichait toutes ses séances
sans recherche, filtres, compteur, réinitialisation ni état zéro filtré.

Livrable développé : recherche texte sans distinction d'accents sur matière/enseignant/groupe/salle/horaire,
filtres Jour/Enseignant/Groupe, compteur résultat/total, réinitialisation et état zéro.
Les filtres restent propres à chaque Vn lors des allers-retours.

Critères : défaut, filtres individuels/combinés, zéro et reset exacts ; état V1/V2
isolé ; Excel complet, SQLite et drapeau actif inchangés.

État : 17 tests ciblés puis 69 tests et 15 sous-tests réussis. Revue indépendante
acceptée sans blocage après vérification Unicode. AppTest couvre les transitions ; les feuilles Excel et snapshots SQLite
couvrent l'absence de mutation fonctionnelle.

## Suite

1. D5 : vérifier petit écran, clavier et contraste dans un navigateur réel.
2. L3 : restauration conservatrice, différée après les besoins interactifs.

Aucune nouvelle dépendance, donnée réelle ou secret. Drive reste désactivé. Pas de
push direct sur `main`, aucun déploiement, dépôt d'origine exclu.
