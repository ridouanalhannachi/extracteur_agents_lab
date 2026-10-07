# Objectifs EDT/RH — 7 octobre 2026

Base distante vérifiée : `c0c10d2`, fusion de la PR nº 8. Aucune PR ouverte au
démarrage. Priorité : interactions utiles et retours exacts. Drive désactivé,
aucun déploiement, un seul lot par cycle.

| Objectif | Problème observé / hypothèse | Bénéfice | Priorité, coût / risque | Dépendances | Critère mesurable | État |
|---|---|---|---|---|---|---|
| I2 — Brouillon de correction contrôlé | Observé : éditeur sans appliquer/annuler ; persistance implicite du widget | Corriger, naviguer et revenir en arrière sans perte | 1, moyen / modéré | D3b/PR8, session Streamlit | Saisie conservée ; appliquer alimente export/mémoire ; annuler restaure dernier appliqué ; nouvel import isolé ; aucune écriture DB | Vérifié : 56 tests, revue indépendante acceptée |
| I3 — Actions contextuelles versions | Hypothèse : actions dispersées dans historique | Agir sur la version sélectionnée | 2, moyen / modéré | I2 | Sélection stable et confirmation exacte ; aucune activation implicite | Proposé |
| D5 — Petit écran et clavier | Limite observée : pas de navigateur disponible | Actions accessibles à 360 px et au clavier | 3, moyen / faible | Navigateur utilisable | Focus logique, actions visibles, contraste texte 4,5:1 | Bloqué pour validation visuelle |
| L3 — Restauration conservatrice | Hypothèse : restauration ancienne menace corrections | Conserver mémoire locale | 4, moyen / élevé | Diagnostic SQLite temporaire, Drive simulé | Ancienneté/corruption/interruption sans perte | Différé |

D1/PR5, D2a/PR6, D3a/PR7 et D3b/PR8 sont intégrés : ne pas les refaire.

## Lot I2 et attribution

Branche `lab/interactive-correction`. Responsable : `app.py`, helper de brouillon,
adaptation du test D3b et documents. Développeur délégué : nouveau test AppTest
uniquement. Pilote/Éclaireur et vérificateur : lecture seule.

Le brouillon de travail est lié à l'empreinte nom/contenu/ordre des fichiers. Une
correction déclenche un état « non appliqué » conservé pendant la navigation.
« Appliquer » remplace le checkpoint local consommé par export, assistant et
enregistrement ; « Annuler » revient à ce checkpoint. Ces deux actions ne créent
aucune version et ne touchent ni SQLite ni Drive. Un nouvel import réinitialise
explicitement les deux brouillons. Aucun composant ni dépendance n'est ajouté.
