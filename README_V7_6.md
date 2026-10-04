# v7.6 — Tableau de bord Statistiques EDT

Ajoute le module :

`📊 Statistiques EDT`

Contenu :

- cartes KPI colorées ;
- filtres année / période / filière / semestre ;
- choix entre versions actives et tout l'historique ;
- séances et heures par jour ;
- charge horaire par enseignant ;
- top enseignants par nombre de séances ;
- utilisation des salles ;
- volume horaire des salles ;
- répartition CM / TD / TP ;
- top matières ;
- nombre de versions par emploi ;
- modifications / ajouts / suppressions ;
- classement des emplois ayant le plus changé.

## Installation

```bash
cd ~/extrateur-edt-rh/edtv7
unzip -o "/mnt/c/Users/HP/Downloads/EDT_Statistiques_patch_v7_6.zip" -d ~/extrateur-edt-rh/edtv7
python apply_edt_statistics_v7_6.py
python -m py_compile app.py edt_statistics_ui.py
streamlit run app.py
```

## Après validation

```bash
git add app.py edt_statistics_ui.py VERSION
git commit -m "v7.6 add timetable statistics dashboard"
git push
```
