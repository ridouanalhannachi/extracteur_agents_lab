# Backlog du laboratoire EDT/RH

Référence de copie : `e44dd858c5e3f0405d0f401bdf7e1d9c48f5ed56`, correctif
v7.9.1 proposé dans la PR nº 1 du dépôt d'origine. Le statut ci-dessous décrit
les travaux à vérifier dans le laboratoire, pas la version déployée.

## Correctifs hérités à conserver

La copie hérite des correctifs de migration SQLite, de sauvegarde manuelle,
d'affichage des échecs de synchronisation, de reconnaissance des durées équivalentes
et de reprise du démarrage après une erreur Drive. Leur présence doit être confirmée
sur le commit examiné ; ne pas les réimplémenter sans défaut reproduit.

## Lots prioritaires

| Lot | État initial | Résultat attendu | Validation nécessaire |
|---|---|---|---|
| L0 — Isolation | Vérifié localement le 2026-10-04 | Le lancement du laboratoire ne lit ni ne remplace les données de production | Configuration séparée, aucune base réelle ni secret livré, tests des chemins locaux et du blocage des appels distants en mode local |
| L1 — Mémoire après redémarrage | À examiner | Une correction et sa vérification restent consultables après réouverture de la base | Base fictive : créer emploi et versions, corriger, fermer et rouvrir ; comparer séances, historique et vérifications ; migration relancée sans perte |
| L2 — Sauvegarde distante concurrente | À examiner | Détecter qu'une sauvegarde distante a changé avant tout remplacement et rendre le conflit visible | Reproduction sur service simulé avec deux clients ; aucune donnée distante remplacée en cas de conflit ; reprise explicitement contrôlée |
| L3 — Restauration conservatrice | À examiner | Un échec de téléchargement ou une base invalide laisse la mémoire locale intacte | Simuler interruption et base corrompue, vérifier intégrité locale et possibilité de nouvelle tentative ; examiner le comportement face à une base distante plus ancienne |
| L4 — Parcours de correction | À examiner | La personne distingue modification non enregistrée, sauvegarde locale et état distant | Parcours sur données fictives : correction, enregistrement, échec simulé, nouvelle tentative, réouverture ; aucun message trompeur de réussite |

L2 correspond à un risque identifié lors de la revue précédente : l'envoi automatique
peut remplacer le fichier distant sans contrôle de concurrence. Confirmer le mécanisme
dans le code actuel avant de choisir une correction. Une simple vérification suivie
d'un envoi n'est pas une garantie atomique : documenter les limites restantes.

Chaque lot doit être redécoupé s'il ne tient pas dans un cycle raisonnable. Un lot
déjà traité ou une proposition ouverte prend priorité sur un nouveau développement.
Les états changent seulement avec une preuve consignée dans le journal.

## Hors du premier périmètre

Les imports enseignants, analyses des descriptifs, comparaisons de volumes horaires
et nouveaux assistants sont des évolutions futures. Aucun statut « réalisé » ne leur
est attribué. Une validation réelle de Drive nécessitera ultérieurement un espace de
test distinct explicitement autorisé ; les simulations ne la remplacent pas.
