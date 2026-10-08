# Relais EDT/RH — I7

- Lot : ouvrir une séance trouvée dans sa version exacte dans l'Historique.
- Branche : `lab/search-result-context` ; base `0bdf6294b3eb9b27e4c79ad30372029d20a4a8a7`.
- État : vérifié ; revue indépendante acceptée après correction des libellés ambigus.
- Diagnostic : résultats de séances sans action vers leur contexte enregistré.
- Changements : sélection native, ouverture par trois IDs validés, version archivée
  exacte, focus persistant et effaçable, erreur explicite pour cible invalide.
- Fichiers : `edt_global_search_ui.py`, `edt_history_ui.py`, `ui_navigation.py`,
  test I7 et cinq documents.
- Preuve : `.venv/bin/python -m pytest -q` — 81 tests, 21 sous-tests.
- Invariants : snapshot SQLite identique ; filtres tiers conservés ; Drive désactivé.
- Limite : AppTest, pas de navigateur Windows/mobile/clavier réel ni capture.
- Inachevé : commit/push/PR et fusion contrôlée.
- Suite : terminer I7 ; ne pas ouvrir I8 avant publication/fusion.
