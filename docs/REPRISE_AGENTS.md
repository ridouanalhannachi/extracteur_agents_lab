# Relais EDT/RH — I4

- Lot : téléchargement Excel de la version sélectionnée.
- Branche : `lab/version-export` ; base `b41b0441aeae7f917cfc2078045f52cc68aa7bf5`.
- État : vérifié ; 65 tests et 15 sous-tests réussis ; revue indépendante acceptée.
- Diagnostic confirmé : sélection précise existante, aucun export depuis l'Historique.
- Changements : export Vn avec deux feuilles, nom versionné, état vide ; lecture seule.
- Fichiers : edt_history_ui.py, tests/test_version_export.py et cinq documents.
- Preuve : `/tmp/edt-i4-final/bin/python -m pytest -q` — 65 tests et 15 sous-tests.
- Limites : AppTest, pas de navigateur/mobile/clavier réel ni capture avant/après.
- Inachevé : commit/push/PR,
  contrôles SHA/protections puis fusion conditionnelle autorisée. Aucun déploiement.
- Suite : D5 si un navigateur utilisable permet la validation ; sinon diagnostic L3 séparé.
