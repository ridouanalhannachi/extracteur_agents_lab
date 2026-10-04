# v7.5 — Recherche globale EDT

Ajoute le module :

`🔎 Recherche globale`

Exemples :

- `DAOUDI`
- `Salle A12`
- `RT S3`
- `Réseaux`
- `V3`
- `Automne`

La recherche couvre :

1. toutes les séances archivées ;
2. toutes les versions ;
3. tous les changements archivés.

Elle permet aussi d'ouvrir directement une version trouvée et d'afficher son emploi complet.

## Installation

```bash
cd ~/extrateur-edt-rh/edtv7
unzip -o "/mnt/c/Users/HP/Downloads/EDT_Recherche_Globale_patch_v7_5.zip" -d ~/extrateur-edt-rh/edtv7
python apply_edt_global_search_v7_5.py
python -m py_compile app.py edt_global_search_ui.py
streamlit run app.py
```

## Après validation

```bash
git add app.py edt_global_search_ui.py VERSION
git commit -m "v7.5 add global timetable search"
git push
```
