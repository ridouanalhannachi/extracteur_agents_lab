# Relais EDT/RH — D1

- Lot : accueil et navigation, branche `lab/design-home-navigation`.
- Base distante : `38bc8f839c8af5fbd59c401348aac7ea87bab676` ; PR 1–4 intégrées.
- État : code vérifié localement, publication/fusion à vérifier sur GitHub.
- Diagnostic confirmé : pas d'accueil, widgets import retirés entre modules.
- Changements : accueil à six accès réels, navigation, panneau import persistant,
  thème natif clair. Extraction/persistance/export inchangés, Drive désactivé.
- Attribution : UI au développeur/responsable ; objectifs/backlog au Pilote ;
  veille à l'Éclaireur ; journal/relais au responsable ; revue en lecture seule.
- Fichiers : app.py, ui_navigation.py, .streamlit/config.toml,
  tests/test_navigation.py et docs/{OBJECTIFS_PILOTE,BACKLOG_LAB,VEILLE_TECHNIQUE,
  JOURNAL_LAB,REPRISE_AGENTS}.md.
- Commande : `/tmp/edt-ui-venv/bin/python -m unittest discover -s tests -q` :
  39 tests réussis ; `git diff --check` réussi. Environnement de test temporaire.
- AppTest : six routes, aller/retour, état OCR et Drive désactivé contrôlés.
- Limite : serveur local lancé, mais Chromium absent et téléchargement invalide ;
  aucune comparaison visuelle ni validation mobile/clavier annoncée.
- Reprise : lire PR et branches distantes avant écriture ; ne pas refaire D1 si
  intégré. Terminer contrôle visuel si possible, puis diagnostic D2 tableaux/filtres.
- Autorisation actuelle : fusion via PR après contrôles et revue, sans push direct
  main ni déploiement. Aucun nouveau consentement requis pour ce seul périmètre.
