# Backlog du laboratoire EDT/RH

## État et priorité — 2026-10-07

Base distante examinée par le responsable : `d31e253`, fusion de la PR nº 6.
PR nº 1 à 6 fusionnées, aucune PR ouverte au début du cycle. Le laboratoire est
séparé de l'application d'origine ; aucun déploiement n'est demandé.

La priorité utilisateur du 6 octobre reste une amélioration visible du design.
D1 (accueil/navigation) et D2a (catalogue/filtres) sont intégrés. Le lot suivant
est D3a, limité au guidage de l'écran d'import/correction/enregistrement/export.

## Lots actifs

| Lot | État | Résultat attendu | Validation nécessaire |
|---|---|---|---|
| D3a — Repères du parcours EDT | **Vérifié localement ; publication à effectuer** | Étapes import → correction/vérification → enregistrement/export visibles, ordonnées et fidèles aux actions existantes | AppTest du guide vide + contrôles structurels ; 6 tests ciblés et 49 tests complets ; inventaire des 19 widgets inchangé ; revue indépendante acceptée |
| D3b — Validation et conservation des corrections | Proposé, hors lot | État non enregistré/enregistré non ambigu ; correction conservée après réouverture | Diagnostic puis import fictif → correction → enregistrement → réouverture → export, sans perte ni faux succès distant |
| D4 — États vides, erreurs et sauvegardes | Proposé | Absence de données, erreur et succès local clairement distingués | Parcours vide et erreurs simulées ; aucune réussite distante inventée |
| D5 — Petits écrans et accessibilité | Proposé | Actions principales utilisables à 360 px et au clavier ; contrastes et libellés lisibles | Navigateur réel, ordre de focus, absence d'action masquée, contraste texte normal ≥ 4,5:1 |
| L3 — Restauration conservatrice | Proposé, différé après priorités design | Une restauration invalide, interrompue ou ancienne préserve la mémoire locale | Diagnostic sur SQLite temporaire et Drive simulé ; séances, versions, validations et intégrité comparées |

Les problèmes observés et hypothèses sont séparés dans
`docs/OBJECTIFS_PILOTE.md`. Un seul lot est développé par cycle. Les états
évoluent uniquement sur preuves consignées ; « prêt » ne signifie ni développé,
ni testé, ni publié.

### Périmètre D3a de ce cycle

Le diagnostic de lecture porte sur `app.py` :

- la barre latérale numérote « 1. Fichiers », « 2. PDF scannés » et
  « 3. Export », mais sa troisième section ne contient aucune action d'export ;
- les séances à corriger sont dans le deuxième onglet, tandis que
  l'enregistrement de version se trouve dans le quatrième ;
- l'utilisateur doit donc reconstruire l'ordre des actions à partir de plusieurs
  zones de l'écran.

D3a peut modifier les libellés de la barre latérale, le guide visible et
l'ordre/titre des onglets ou zones de l'écran EDT, uniquement pour rendre les
étapes existantes prévisibles. Il ne peut ajouter ni simuler une action.

Sont explicitement hors lot : extraction PDF/Word/OCR, référentiel enseignants,
règles de complétude, calculs, éditeurs et données produites, auto-enregistrement,
persistance SQLite, historique, synchronisation, assistant local et génération
Excel. Les conditions d'activation du téléchargement doivent rester identiques.

### Critères mesurables D3a

- avant import, trois étapes cohérentes sont visibles et distinguent
  enregistrement local et export Excel ;
- aucun intitulé ne laisse croire qu'une action d'export existe dans la barre
  latérale ; aucun bouton de fonction inexistante n'est ajouté ;
- les contrôles structurels confirment les zones de correction, d'enregistrement
  et de téléchargement ; leurs 19 widgets, clés et libellés techniques sont inchangés ;
- un test UI ciblé et la suite complète réussissent sur l'arbre exact ;
- `git diff --check` réussit et Drive demeure désactivé ;
- rendu avant/après, affichage étroit et clavier restent explicitement non
  validés en l'absence d'un navigateur réel.

## Socle intégré à préserver

| Lot | Preuves historiques | Limites |
|---|---|---|
| D1 — Accueil et navigation | PR nº 5, `58ac343` ; 39 tests historiques, dont 2 AppTest | Pas de comparaison visuelle navigateur, mobile ou focus |
| D2a — Catalogue et filtres | PR nº 6, `d31e253` ; 43 tests historiques, dont AppTest sur SQLite temporaire | Pas de comparaison visuelle navigateur, mobile ou clavier |
| L0 — Isolation | PR nº 1 ; configuration et base laboratoire séparées, appels Drive bloqués | Ne prouve pas la persistance sur disque éphémère |
| L1 — Mémoire après redémarrage | PR nº 2 ; processus Python distincts, migration et conservation des corrections/validations | Données fictives, pas de redémarrage réel Streamlit Cloud |
| L2a — Garde des remplacements distants | PR nº 4 ; 11 tests ciblés et 37 tests totaux historiques, service simulé | Drive réel non testé et désactivé ; créations initiales simultanées à diagnostiquer |

La PR nº 3 fait également partie de la base intégrée. Ne pas confondre les
comptages historiques avec les tests exécutés pendant le présent cycle. Ne pas
réimplémenter le socle sans défaut reproduit.

## Hors de ce lot

Pas de migration de framework, nouvelle dépendance, appel IA externe, coût,
donnée réelle ou secret. Pas d'activation Drive. Les imports enseignants étendus,
analyses de descriptifs et nouveaux assistants restent des propositions séparées.
Les commits/push en branche dédiée et fusions par PR sont autorisés aux conditions
actuelles données par l'utilisateur ; pas de push direct sur `main` ni déploiement.
