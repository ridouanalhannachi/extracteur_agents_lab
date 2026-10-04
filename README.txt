Installation depuis WSL :

cd ~/extrateur-edt-rh/edtv7
unzip -o "/mnt/c/Users/HP/Downloads/EDT_Changements_v7_3.zip" -d ~/extrateur-edt-rh/edtv7
python apply_edt_changes_v73.py
python -m py_compile app.py edt_memory.py edt_changes.py
streamlit run app.py

Test :
- uploader EDT -> V1 initiale
- uploader une version modifiée -> V2
- le rapport V1 -> V2 doit apparaître automatiquement
- les changements sont archivés dans edt_version_changes et edt_version_change_summary
