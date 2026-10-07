# Backlog EDT/RH — 7 octobre 2026

Base vérifiée : `03425a1`, PR 1 à 9 fusionnées, aucune PR ouverte au début du
cycle. Le socle de fiabilité, D1/D2a/D3a/D3b et I2 sont intégrés.

## Lot en cours : I3 — Activation contextuelle d'une version

Diagnostic confirmé : l'Historique conservait la version sélectionnée mais ne
proposait aucune action sur elle. `edt_memory.py` savait créer une nouvelle version,
pas réactiver explicitement une version archivée.

Livrable développé : action sur la version sélectionnée, confirmation en deux temps,
bouton désactivé avant confirmation, transaction SQLite atomique et retour exact
sur la nouvelle et l'ancienne version active. La sélection reste sur la version
activée après relance. Aucune suppression ni réécriture de séance/commentaire.

Critères : exactement une active après confirmation ; aucune écriture avant celle-ci ;
appel répété idempotent ; mauvais emploi/version refusé sans mutation ; statuts métier,
versions, séances et commentaires préservés.

État : 62 tests et 15 sous-tests réussis par le responsable ; revue indépendante
acceptée avec 10 tests ciblés et 62 tests complets. AppTest couvre sélection, verrou de confirmation, activation, retour et
persistance ; SQLite temporaire couvre transaction et intégrité.

## Suite

1. I4 : évaluer l'export contextuel de la version consultée.
2. D5 : vérifier petit écran, clavier et contraste dans un navigateur réel.
3. L3 : restauration conservatrice, différée après les besoins interactifs.

Aucune nouvelle dépendance, donnée réelle ou secret. Drive reste désactivé. Pas de
push direct sur `main`, aucun déploiement, dépôt d'origine exclu.
