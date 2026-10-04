# RH v6.1 — Recherche enseignant + conflits sans rechargement

## Nouveautés

- Après résolution d'un conflit RH, l'interface se réactualise automatiquement (`st.rerun()`).
- Après apprentissage d'une colonne ou suppression d'une fiche, la liste est aussi actualisée automatiquement.
- Nouveau moteur de recherche enseignant :
  - recherche dès la première lettre (voyelle ou consonne),
  - préfixe du nom ou prénom,
  - initiales (ex. `DS`),
  - email / téléphone,
  - tolérance à de petites variations d'écriture,
  - rapprochement par consonnes pour les recherches courtes.
- Lorsqu'un enseignant est sélectionné :
  - les informations principales sont affichées en premier : Statut, Nom, Prénom, Email, Téléphone, Diplôme, Spécialité, Département ;
  - les informations secondaires sont affichées juste en dessous à partir de `Autres informations`, Source document, Section, dates ;
  - l'historique permanent de la fiche est accessible directement.

## Installation du patch

Dans Ubuntu/WSL :

```bash
cd ~/extrateur-edt-rh/edtv3
```

Arrêter Streamlit avec `Ctrl+C`, puis :

```bash
unzip -o "/mnt/c/Users/HP/Downloads/RH_patch_v6_1.zip" -d ~/extrateur-edt-rh/edtv3
rm -rf __pycache__
source .venv/bin/activate
streamlit run app.py --server.address=0.0.0.0
```

Actualiser ensuite le navigateur avec `Ctrl+F5`.
