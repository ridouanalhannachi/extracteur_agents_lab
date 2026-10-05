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
| L1 — Mémoire après redémarrage | Validé sur données fictives le 2026-10-04 | Une correction et sa vérification restent consultables après réouverture de la base | Base fictive : créer emploi et versions, corriger, fermer et rouvrir ; comparer séances, historique et vérifications ; migration relancée sans perte |
| L2a — Garde conservatrice des remplacements distants | Vérifié sur service simulé le 2026-10-05 | Refuser le remplacement d’un fichier existant sans garantie atomique et rendre le refus explicite | 11 tests ciblés et 37 tests au total réussis : zéro remplacement, état local conservé et aucun faux succès ; Drive réel non testé et désactivé |
| L3 — Restauration conservatrice | À examiner | Un échec de téléchargement ou une base invalide laisse la mémoire locale intacte | Simuler interruption et base corrompue, vérifier intégrité locale et possibilité de nouvelle tentative ; examiner le comportement face à une base distante plus ancienne |
| L4 — Parcours de correction | À examiner | La personne distingue modification non enregistrée, sauvegarde locale et état distant | Parcours sur données fictives : correction, enregistrement, échec simulé, nouvelle tentative, réouverture ; aucun message trompeur de réussite |

Le diagnostic L2 sur `75534fc` confirme que `upload_database` remplace le fichier
existant sans précondition ; `auto_upload_after_change` l'appelle directement.
L2a borne ce cycle au refus conservateur de ce remplacement : un contrôle puis un
envoi ne prouve pas l'atomicité. Branche : `lab/concurrent-backup-guard`.
Drive reste désactivé. L2 n'est pas déclaré entièrement résolu : autoriser à nouveau
un remplacement sûr et traiter des créations initiales simultanées demanderaient
un protocole supplémentaire, à diagnostiquer séparément. Voir OBJECTIFS_PILOTE.md.

Chaque lot doit être redécoupé s'il ne tient pas dans un cycle raisonnable. Un lot
déjà traité ou une proposition ouverte prend priorité sur un nouveau développement.
Les états changent seulement avec une preuve consignée dans le journal.

## Hors du premier périmètre

Les imports enseignants, analyses des descriptifs, comparaisons de volumes horaires
et nouveaux assistants sont des évolutions futures. Aucun statut « réalisé » ne leur
est attribué. Une validation réelle de Drive nécessitera ultérieurement un espace de
test distinct explicitement autorisé ; les simulations ne la remplacent pas.
