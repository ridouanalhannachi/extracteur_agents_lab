# Relais EDT/RH — D3a

- Lot : guidage import, correction, export et enregistrement.
- Branche : `lab/design-import-guidance` ; base
  `d31e253cae993b05cea31a12c0b9478c1bc7e5f2`.
- État : vérifié et accepté indépendamment ; publication/fusion via PR à effectuer.
- Diagnostic confirmé : faux repère « 3. Export », correction après l'export dans
  les onglets, état de complétude et contrôle hors contexte.
- Changements : guide avant import, quatre onglets ordonnés, état prêt/incomplet/vide,
  export et contrôles regroupés, distinction version / Vérification globale.
- Fichiers : `app.py`, `tests/test_import_workflow_ui.py` et documents
  OBJECTIFS_PILOTE, BACKLOG_LAB, VEILLE_TECHNIQUE, JOURNAL_LAB, REPRISE_AGENTS.
- Preuves : 6 tests ciblés ; 49 tests complets ; compilation et `git diff --check`.
  Revue indépendante reprise après correction d'une incohérence de numérotation.
- Préservation : 19 widgets et clés identiques ; moteurs, données, persistance,
  export et dépendances inchangés ; Drive désactivé ; aucun workflow.
- Limites : AppTest réel sans fichier importé ; aucune capture navigateur, validation
  petit écran ou focus clavier. Aucun déploiement.
- Reprise : vérifier distant et PR avant écriture ; publier l'arbre exact testé,
  puis fusionner seulement si SHA, protections et absence de déploiement sont confirmés.
