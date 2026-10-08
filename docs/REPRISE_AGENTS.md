# Relais EDT/RH — I5

- Lot : filtres réactifs des séances de la version sélectionnée.
- Branche : `lab/session-filters` ; base `a59d3cf32e0d994213b65369b59ce33cf40ce929`.
- État : vérifié ; 69 tests et 15 sous-tests réussis ; revue indépendante acceptée.
- Diagnostic confirmé : tableau complet sans recherche, compteur ni reset.
- Changements : recherche, Jour/Enseignant/Groupe, compteur, reset, zéro ; état isolé Vn.
- Fichiers : edt_history_ui.py, tests/test_version_session_filters.py et cinq documents.
- Preuve : `/tmp/edt-i5-final/bin/python -m pytest -q` — 69 tests et 15 sous-tests.
- Limites : AppTest, pas de navigateur/mobile/clavier réel ni capture avant/après.
- Inachevé : commit/push/PR,
  contrôles SHA/protections puis fusion conditionnelle autorisée. Aucun déploiement.
- Suite : D5 si un navigateur utilisable permet la validation ; sinon diagnostic L3 séparé.
