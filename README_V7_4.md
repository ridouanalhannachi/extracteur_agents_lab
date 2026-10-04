# v7.4 — Historique visuel complet des emplois du temps

Ajoute un nouveau module dans la barre latérale :

`🗂️ Historique EDT`

Il fonctionne même sans uploader un nouveau fichier.

Fonctions :

- vue de tous les emplois mémorisés ;
- filtres année / période / filière / semestre ;
- nombre total d'emplois, versions, séances et changements ;
- boutons V1 / V2 / V3... ;
- affichage complet de l'emploi de chaque version ;
- indication de la version active ;
- modifications Vn-1 → Vn ;
- séances modifiées / ajoutées / supprimées ;
- option `Afficher toutes les versions`.

Installation :

```bash
cd ~/extrateur-edt-rh/edtv7
unzip -o "/mnt/c/Users/HP/Downloads/EDT_Historique_patch_v7_4.zip" -d ~/extrateur-edt-rh/edtv7
python apply_edt_history_v7_4.py
python -m py_compile app.py edt_history_ui.py
streamlit run app.py
```

Après validation locale :

```bash
git add app.py edt_history_ui.py VERSION
git commit -m "v7.4 add complete timetable history UI"
git push
```
