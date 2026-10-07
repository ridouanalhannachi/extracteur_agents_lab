# Relais EDT/RH — D3b

- État : vérifié, accepté indépendamment ; publication/fusion par PR à effectuer.
- Branche : `lab/design-save-state` ; base distante `67df619df64d52314ab13413402b4da1e50979bd`.
- Diagnostic confirmé : corrections détaillées après auto-save, pas d'état durable.
- Livrable : comparaison locale lecture seule et messages réactifs pour cible
  sélectionnée ; enregistré actif, archivé, non enregistré, vide/incomplet/inconnu.
- Fichiers : app.py, edt_save_state.py, tests/test_save_state.py ; OBJECTIFS_PILOTE,
  BACKLOG_LAB, VEILLE_TECHNIQUE, JOURNAL_LAB et ce relais. Responsable seul en écriture,
  Pilote/vérificateur en lecture. Aucun autre agent actif au début de la reprise.
- Commande : `/tmp/edt-ui-venv/bin/python -m unittest discover -s tests -q`.
  Responsable : 55 réussis (8,410 s) ; indépendant : 55 (8,845 s) ; 6 ciblés
  réussis par chacun. Diff-check réussi. Données fictives et bases temporaires.
- Limites : rendu navigateur, mobile, clavier et navigation avec saisies non
  vérifiés ; AppTest utilise une injection de corrections. Statut limité à la
  cible sélectionnée et aux séances métier, pas Intervenants ni provenance.
- Inachevé : publication et fusion conditionnelle. Vérifier distant/PR avant
  toute reprise ; ne pas dupliquer D3b s'il est fusionné. Aucun blocage technique.
- Prochaine action : publier l'arbre testé, contrôler PR/SHA/protections puis fusion
  autorisée via PR ; jamais de push direct main ni déploiement. Drive désactivé.
