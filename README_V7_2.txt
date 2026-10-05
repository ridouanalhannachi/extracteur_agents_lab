V7.2 - PREMIERE ETAPE MEMOIRE EDT

Ajoute :
- tables SQLite edt_timetables, edt_versions, edt_sessions dans estn.db
- onglet Memoire / Versions
- V1, V2, V3... par annee + periode + filiere + semestre
- version active automatique
- anti-duplication d'un emploi strictement identique
- synchronisation automatique vers Google Drive apres enregistrement

INSTALLATION WSL :
cd ~/extrateur-edt-rh/edtv7
unzip -o "/mnt/c/Users/HP/Downloads/EDT_Memoire_patch_v7_2.zip" -d ~/extrateur-edt-rh/edtv7
python apply_edt_memory_v7_2.py
python -m py_compile app.py edt_memory.py
streamlit run app.py

APRES TEST :
git add app.py edt_memory.py VERSION
git commit -m "v7.2 add timetable version memory"
git push
