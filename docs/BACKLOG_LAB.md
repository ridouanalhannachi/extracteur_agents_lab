# Backlog du laboratoire EDT/RH

## État et priorité — 2026-10-07

Base distante examinée par le responsable : `58ac343`, fusion de la PR nº 5.
PR nº 1 à 5 fusionnées, aucune PR ouverte au début du cycle. Le laboratoire est
séparé de l'application d'origine ; aucun déploiement n'est demandé.

La priorité utilisateur du 6 octobre est une amélioration visible du design.
Les travaux locaux antérieurs sont préservés. D1 est intégré ; le lot D2a commence
sur une branche propre et ne reprend aucun ancien lot.

## Lots actifs

| Lot | État | Résultat attendu | Validation nécessaire |
|---|---|---|---|
| D1 — Accueil et navigation | Intégré via PR nº 5 à `58ac343` ; 39 tests historiques, dont 2 AppTest ; rendu navigateur à vérifier | Accueil clair, accès aux fonctions existantes, hiérarchie et styles cohérents ; Drive identifié comme désactivé | Contrôler ultérieurement comparaison visuelle, focus et petit écran avec un vrai navigateur |
| D2a — Catalogue et filtres de l'historique | Vérifié localement : 43 tests ; publication à effectuer | Filtres en deux rangées, décompte résultat/total, titre contextuel, réinitialisation et état vide explicite | AppTest : `2/2`, filtre `1/2`, réinitialisation `2/2`, cas vide ; mêmes identifiants métier ; revue successive non indépendante |
| D3 — Import/correction/validation | Proposé | Étapes et actions compréhensibles, corrections conservées | Import fictif → correction → validation → export → réouverture, sans perte |
| D4 — États vides et sauvegardes | Proposé | Absence de données, erreur et succès local clairement distingués | Parcours vide et erreurs simulées ; aucune réussite distante inventée |
| L3 — Restauration conservatrice | Proposé, différé après priorités design | Une restauration invalide, interrompue ou ancienne préserve la mémoire locale | Diagnostic sur SQLite temporaire et Drive simulé ; séances, versions, validations et intégrité comparées |

Les cinq objectifs détaillés et les critères transversaux d'accessibilité sont dans
`docs/OBJECTIFS_PILOTE.md`. Un seul lot développé par cycle. Les états évoluent
uniquement sur preuves consignées ; « en cours » ne signifie ni testé ni publié.

### Périmètre D2a de ce cycle

Uniquement le catalogue initial de `render_edt_history()` et ses quatre filtres.
Les autres tableaux de l'historique, les statistiques, la base RH, les éditeurs de
séances et les exports sont hors lot. Aucun changement de requête SQL, de règle de
filtrage, de donnée persistée ou de dépendance. AppTest peut prouver les parcours et
les sous-ensembles ; il ne prouve pas à lui seul le rendu clavier/mobile.

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
