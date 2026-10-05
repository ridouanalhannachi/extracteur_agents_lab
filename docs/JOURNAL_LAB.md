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

## 2026-10-05 — L2a, garde conservatrice des remplacements distants

Base examinée : `75534fc639aeaf5725d52b26e38d3b5a711114ce` (PR nº 3).
Branche : `lab/concurrent-backup-guard`. Diagnostic confirmé : un envoi pouvait
appeler `files.update` sans précondition atomique et effacer une correction distante.

Le correctif refuse tout remplacement d'une base distante existante, convertit le
refus en état `conflict` pour la synchronisation et empêche l'envoi automatique
d'annoncer un succès. La première création reste autorisée. Drive demeure désactivé
dans `app_config.py`; les données sont fictives et le service Drive est simulé.

Validation du responsable : `python -m unittest tests.test_drive_concurrency -v`
— 11 tests réussis ; `python -m unittest discover -s tests -q` — 37 tests réussis.
Vérification indépendante : mêmes 11 et 37 tests réussis, `git diff --check` réussi,
aucun secret ni donnée personnelle détecté et aucun workflow de déploiement présent.

Limites : aucune validation OAuth/API Drive réelle ; deux premières créations
simultanées peuvent encore produire des fichiers homonymes. L'interface d'envoi
forcé devra être adaptée avant toute activation réelle, car la garde bloque désormais
tout remplacement. Prochaine étape : publier L2a, puis diagnostiquer L3 séparément.
