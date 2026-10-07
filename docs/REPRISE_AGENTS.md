# Relais EDT/RH — I2

- Lot : brouillon interactif appliquer/annuler.
- Branche : `lab/interactive-correction` ; base `c0c10d258d97223bd17b867c9aa5121a0d1e3c3d`.
- État : vérifié ; 56 tests responsable et vérificateur réussis ; revue indépendante acceptée.
- Diagnostic confirmé : éditeur sans validation/annulation ni checkpoint durable.
- Changements : brouillon lié aux imports et conservé en navigation ; appliquer
  alimente export/assistant/mémoire ; annuler restaure dernier appliqué ; changement
  d'import réinitialise. Aucun appel d'écriture dans ces actions.
- Fichiers : app.py, edt_correction_state.py, tests/test_correction_interactions.py,
  adaptation test_save_state.py et cinq documents. Pilote/développeur/vérificateur
  ont des missions distinctes ; seul le responsable modifie code/docs hors nouveau test.
- Preuve : suite complète 56 tests en 10,272 s avec `/tmp/edt-i2-venv/bin/python`.
- Limites : édition AppTest injectée, pas de navigateur/mobile/clavier réel.
- Inachevé : tests finaux arbre exact, commit/push/PR,
  contrôles SHA/protections puis fusion conditionnelle autorisée. Aucun déploiement.
- Suite : I3 actions contextuelles des versions, après intégration de I2.
