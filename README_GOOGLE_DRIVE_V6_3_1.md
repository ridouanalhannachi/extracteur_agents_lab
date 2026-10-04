# Correctif Google Drive v6.3.1 — OAuth sous WSL

Ce correctif cible le cas où Streamlit tourne dans Ubuntu/WSL et où le navigateur Google tourne sous Windows.

## Changements

- ouverture du navigateur Windows via `explorer.exe` ;
- callback OAuth sur `127.0.0.1` plutôt que `localhost` ;
- écoute WSL sur `0.0.0.0` pour recevoir le callback ;
- timeout de 180 secondes au lieu d'un chargement infini ;
- URL OAuth également affichée dans le terminal Ubuntu si l'ouverture automatique échoue.

## Installation

```bash
cd ~/extrateur-edt-rh/edtv3
unzip -o "/mnt/c/Users/HP/Downloads/GoogleDrive_patch_v6_3_1.zip" -d ~/extrateur-edt-rh/edtv3
rm -rf __pycache__
source .venv/bin/activate
streamlit run app.py --server.address=0.0.0.0
```

Puis `Ctrl+F5` dans le navigateur et relancer **Connecter mon compte Google Drive**.
