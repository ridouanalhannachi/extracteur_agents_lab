from pathlib import Path
import json

required = ["app.py", "requirements.txt", "Dockerfile", "gdrive_sync.py", "rh_manager.py"]
missing = [x for x in required if not Path(x).exists()]
if missing:
    raise SystemExit("Fichiers manquants : " + ", ".join(missing))

token = Path("data/gdrive/token.json")
if not token.exists():
    print("ATTENTION : data/gdrive/token.json absent. Connectez d'abord Google Drive en mode local.")
else:
    payload = json.loads(token.read_text(encoding="utf-8"))
    print("Token Google Drive présent :", bool(payload.get("refresh_token")), "(refresh_token)")
print("Préparation Cloud v7 : OK")
