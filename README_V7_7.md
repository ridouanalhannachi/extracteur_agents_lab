# v7.7 — Analyse statistique avancée EDT

Cette version enrichit le module `📊 Statistiques EDT`.

Nouveautés :

- insights automatiques ;
- heatmap Jour × Horaire ;
- boxplot de la charge horaire ;
- détection des charges atypiques par règle IQR ;
- Pareto 80/20 pour salles / enseignants / matières ;
- carte de contrôle 3σ des changements entre versions ;
- taux de changement et score de stabilité ;
- score de complétude technique des données.

Installation :

```bash
cd ~/extrateur-edt-rh/edtv7
unzip -o "/mnt/c/Users/HP/Downloads/EDT_Analyse_Statistique_Avancee_patch_v7_7.zip" -d ~/extrateur-edt-rh/edtv7
python apply_advanced_statistics_v7_7.py
python -m py_compile edt_statistics_ui.py edt_advanced_statistics_ui.py
streamlit run app.py
```

Après validation :

```bash
git add edt_statistics_ui.py edt_advanced_statistics_ui.py VERSION
git commit -m "v7.7 add advanced statistical analytics"
git push
```
