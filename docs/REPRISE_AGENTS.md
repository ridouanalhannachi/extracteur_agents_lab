# Relais EDT/RH — D2a

- Lot : catalogue et filtres de l'Historique.
- Branche : `lab/design-table-filters` ; base `58ac343581be8638bf8ab454937819bb3d4b11c9`.
- État : vérifié localement ; publication/fusion à effectuer via PR.
- Diagnostic confirmé : filtres sur une rangée, titre non contextuel, aucun compteur
  ni réinitialisation, tableau vide avant le message.
- Changements : deux rangées, résultat/total, titre adapté, reset et état vide utile ;
  compatibilité Streamlit 1.45.1 sur les largeurs de cet écran.
- Fichiers : `edt_history_ui.py`, `tests/test_history_catalog_ui.py` et documents
  OBJECTIFS_PILOTE, BACKLOG_LAB, VEILLE_TECHNIQUE, JOURNAL_LAB, REPRISE_AGENTS.
- Preuves : 4 tests ciblés ; suite complète 43 tests réussis ; `git diff --check`.
  AppTest utilise deux emplois fictifs et SQLite temporaire.
- Attribution : Pilote et Éclaireur distincts ; développeur délégué bloqué par quota ;
  développement et revue ensuite réalisés successivement par le responsable.
- Limites : revue non indépendante, aucune capture navigateur, validation mobile ou
  clavier. Drive désactivé, aucune donnée réelle, dépendance ou déploiement.
- Reprise : vérifier distant et PR avant écriture ; publier le contenu exact testé,
  puis fusionner seulement si SHA, protections et absence de déploiement sont confirmés.
  Le lot suivant doit rester distinct.
