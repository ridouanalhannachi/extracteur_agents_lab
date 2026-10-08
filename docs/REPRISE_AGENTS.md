# Relais EDT/RH — I6

- Lot : correction ciblée depuis la Vérification globale.
- Branche : `lab/verification-correction` ; base `5f981eaff9222d9853f9853845bbb57aed45143d`.
- État : vérifié ; 76 tests et 21 sous-tests ; revue indépendante acceptée.
- Diagnostic : séance sélectionnée et marquée « À revoir », mais non modifiable.
- Changements : formulaire prérempli, préparation locale, diff, annulation, confirmation,
  nouvelle version dédupliquée ; durée invalide et base obsolète refusées.
- Fichiers : `edt_memory.py`, `edt_verification_ui.py`, test I6 et cinq documents.
- Preuve : `/tmp/edt-i6-venv/bin/python -m pytest -q` — 76 tests, 21 sous-tests.
- Invariants : V1 et autres séances intactes ; Drive désactivé ; aucun déploiement.
- Limite : AppTest, pas de navigateur Windows/mobile/clavier réel ni capture.
- Inachevé : commit/push/PR et fusion contrôlée.
- Suite : terminer I6 ; ne pas ouvrir I7 avant publication/fusion.
