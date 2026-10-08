# Backlog EDT/RH — 7 octobre 2026

Base vérifiée : `b41b044`, PR 1 à 10 fusionnées, aucune PR ouverte au début du
cycle. Le socle de fiabilité et les lots interactifs jusqu'à I3 sont intégrés.

## Lot en cours : I4 — Export contextuel de la version sélectionnée

Diagnostic confirmé : l'Historique cible déjà une version précise, mais ne permettait
pas de télécharger cette version. L'export existant n'était accessible que dans le
parcours d'import/correction.

Livrable développé : bouton « Télécharger Vn en Excel » dans les actions contextuelles,
nom `EDT_<emploi>_Vn.xlsx`, deux feuilles existantes et état vide explicite. L'export
d'une version archivée ne l'active pas et ne crée aucun enregistrement.

Critères : V1 et V2 donnent leurs propres séances et noms ; deux feuilles présentes ;
bouton désactivé sans séance ; sélection, versions et drapeaux actifs inchangés.

État : 13 tests ciblés puis 65 tests et 15 sous-tests réussis. Revue indépendante
acceptée sans blocage. AppTest couvre sélection/état vide ; lecture du classeur et snapshots
SQLite couvrent contenu exact et absence de mutation.

## Suite

1. D5 : vérifier petit écran, clavier et contraste dans un navigateur réel.
2. L3 : restauration conservatrice, différée après les besoins interactifs.

Aucune nouvelle dépendance, donnée réelle ou secret. Drive reste désactivé. Pas de
push direct sur `main`, aucun déploiement, dépôt d'origine exclu.
