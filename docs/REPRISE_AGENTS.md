# Relais des agents — laboratoire EDT/RH

## Lot courant

- Lot : L2a, refus conservateur des remplacements distants non atomiques.
- Branche : `lab/concurrent-backup-guard`.
- Base examinée : `75534fc639aeaf5725d52b26e38d3b5a711114ce` (PR nº 3).
- État : vérifié localement sur service simulé ; publication de la branche à terminer.
- Dépendances : PR nº 1, nº 2 et nº 3 non fusionnées au début du travail.

## Preuves et limites

Le chemin d'envoi peut appeler `files.update` sans précondition. Le correctif
retenu refuse le remplacement d'un fichier distant existant : il ne réalise pas
une synchronisation atomique ni une fusion de bases. Drive reste désactivé.
Les tests utilisent exclusivement SQLite temporaire et des services simulés.
Le responsable et un vérificateur indépendant ont exécuté 11 tests ciblés et la
suite complète de 37 tests, tous réussis. `git diff --check` réussit. Aucun secret,
donnée personnelle ou workflow de déploiement n'a été trouvé ; Drive est désactivé.

## Attribution

- Développeur : `gdrive_sync.py`, `tests/test_drive_concurrency.py`.
- Pilote : `docs/BACKLOG_LAB.md`, `docs/OBJECTIFS_PILOTE.md`.
- Vérificateur indépendant : relecture et tests, sans modifications de fichiers.
- Responsable : journal, relais et publication.

## Reprise

Publier la branche et ouvrir la PR L2a sans la confondre avec une validation Drive
réelle. Ne pas refaire L1. Après livraison de L2a, examiner la restauration
conservatrice L3 sur données fictives.
Les créations distantes simultanées et la réautorisation d'un remplacement sûr
restent hors de L2a. Aucun nouveau service ni technologie n'est requis pour ce lot.
