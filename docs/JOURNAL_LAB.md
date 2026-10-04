# Journal du laboratoire

## 2026-10-04 — Initialisation

Source : e44dd858c5e3f0405d0f401bdf7e1d9c48f5ed56, PR nº 1 v7.9.1.
Copie indépendante sans historique Git source. Deux agents ont préparé isolation
et consignes de développement. Base data-lab/estn-lab.db ; variables production
ignorées ; Drive bloqué ; formulaire Drive remplacé par un message explicite.

Validation : `python -m unittest discover -s tests -q` : 24 tests réussis.
Données fictives et services simulés. Aucun test réel de Drive ni déploiement.
Prochaine étape : L1, vérifier mémoire et corrections après redémarrage.

## 2026-10-04 — L1, persistance entre processus

Base distante examinée : 17171299d75365d9bbcc35935add8a75d383ff08.
Branche : lab/restart-persistence, dérivée de lab/bootstrap-isolation.
Un agent développe les tests ; le responsable relit les assertions et exécute la suite.

Ajout : tests/test_edt_restart.py. Deux scénarios exécutent des interpréteurs Python
séparés : création V1, correction V2 avec validation, puis réouverture sans état UI ;
migration des six colonnes historiques manquantes puis relance dans un autre processus.
Les assertions couvrent versions actives, séances historiques, source/page, notes,
historique exact de la salle modifiée, absence de doublon et intégrité SQLite.

Commande : `python -m unittest discover -s tests -q` — 26 tests réussis.
Aucun défaut reproduit sur ces scénarios : aucun correctif applicatif nécessaire.
Limites : données fictives, Streamlit et Drive simulés ; pas de test navigateur ni
de redémarrage réel Streamlit Cloud. Une base conservée sur disque ne démontre pas
la persistance d'un hébergement dont le disque est éphémère.
Prochaine étape : L2, diagnostic des remplacements distants concurrents, uniquement
sur service simulé et en maintenant Drive désactivé dans le laboratoire.
