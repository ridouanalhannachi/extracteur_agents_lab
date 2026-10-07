# Backlog du laboratoire EDT/RH

## État et priorité — 2026-10-06

Base distante examinée par le responsable :
`38bc8f839c8af5fbd59c401348aac7ea87bab676`.
PR nº 1 à 4 fusionnées, aucune PR ouverte au début du cycle. Le laboratoire est
séparé de l'application d'origine ; aucun déploiement n'est demandé.

La priorité utilisateur du 6 octobre est une amélioration visible du design.
Les travaux locaux antérieurs sont préservés. Le lot D1 commence sur une branche
propre ; les anciens lots intégrés ne sont pas redéveloppés.

## Lots actifs

| Lot | État | Résultat attendu | Validation nécessaire |
|---|---|---|---|
| D1 — Accueil et navigation | Vérifié : 39 tests, dont 2 AppTest ; rendu navigateur à vérifier | Accueil clair, accès aux fonctions existantes, hiérarchie et styles cohérents ; Drive identifié comme désactivé | Contrôler accès aux modules, absence de fonctions ou statistiques fictives, état des parcours préservé et suite applicative réussie ; comparaison visuelle si lancement réellement possible |
| D2 — Tableaux et filtres | Proposé, diagnostic à conduire | Lecture et sélection facilitées sans changement des données ni exports | Données fictives ; filtres, colonnes, clavier et petit écran ; mêmes résultats métier |
| D3 — Import/correction/validation | Proposé | Étapes et actions compréhensibles, corrections conservées | Import fictif → correction → validation → export → réouverture, sans perte |
| D4 — États vides et sauvegardes | Proposé | Absence de données, erreur et succès local clairement distingués | Parcours vide et erreurs simulées ; aucune réussite distante inventée |
| L3 — Restauration conservatrice | Proposé, différé après priorités design | Une restauration invalide, interrompue ou ancienne préserve la mémoire locale | Diagnostic sur SQLite temporaire et Drive simulé ; séances, versions, validations et intégrité comparées |

Les cinq objectifs détaillés et les critères transversaux d'accessibilité sont dans
`docs/OBJECTIFS_PILOTE.md`. Un seul lot développé par cycle. Les états évoluent
uniquement sur preuves consignées ; « en cours » ne signifie ni testé ni publié.

## Socle intégré à préserver

| Lot | Preuves historiques | Limites |
|---|---|---|
| L0 — Isolation | Intégré via PR nº 1 ; configuration et base laboratoire séparées, appels Drive bloqués | Ne prouve pas la persistance sur disque éphémère |
| L1 — Mémoire après redémarrage | Intégré via PR nº 2 ; tests sur processus Python distincts, migration et conservation des corrections/validations | Données fictives, pas de redémarrage réel Streamlit Cloud |
| L2a — Garde des remplacements distants | Intégré via PR nº 4 ; 11 tests ciblés et 37 tests totaux historiques réussis, service simulé | Drive réel non testé et désactivé ; créations initiales simultanées et interface d'envoi forcé restent à diagnostiquer avant activation |

La PR nº 3 fait également partie de la base intégrée. Ne pas confondre les
comptages historiques avec les tests exécutés pendant le présent cycle.
La copie conserve les correctifs hérités v7.9.1 : migration SQLite, sauvegarde
manuelle, erreurs de synchronisation, durées équivalentes et reprise de démarrage.
Ne pas les réimplémenter sans défaut reproduit.

## Hors de ce lot

Pas de migration de framework, nouvelle dépendance, appel IA externe, coût,
donnée réelle ou secret. Pas d'activation Drive. Les imports enseignants étendus,
analyses de descriptifs et nouveaux assistants restent des propositions distinctes.
Les commits/push en branche dédiée et fusions par PR sont autorisés aux conditions
actuelles données par l'utilisateur ; pas de push direct sur main ni déploiement.
