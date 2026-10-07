# Relais EDT/RH — I3

- Lot : activation explicite de la version sélectionnée.
- Branche : `lab/version-actions` ; base `03425a173115a74ae24c240004a6f66615fc0728`.
- État : vérifié ; 62 tests et 15 sous-tests responsable réussis ; revue indépendante acceptée.
- Diagnostic confirmé : versions consultables/sélection stable, aucune action contextuelle.
- Changements : confirmation obligatoire, activation atomique et idempotente,
  ancienne active archivée, retour exact ; aucun contenu de version supprimé ou réécrit.
- Fichiers : edt_memory.py, edt_history_ui.py, deux tests et cinq documents.
- Preuve : `/tmp/edt-i3-venv/bin/python -m pytest -q` — 62 tests et 15 sous-tests.
- Limites : AppTest, pas de navigateur/mobile/clavier réel ni capture avant/après.
- Inachevé : commit/push/PR,
  contrôles SHA/protections puis fusion conditionnelle autorisée. Aucun déploiement.
- Suite : I4 export contextuel, uniquement après intégration de I3.
