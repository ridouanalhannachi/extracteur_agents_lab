from pathlib import Path

root = Path(__file__).resolve().parent
required = [
    root / "app.py",
    root / "requirements.txt",
    root / "packages.txt",
    root / ".gitignore",
    root / ".streamlit" / "config.toml",
]
missing = [str(x.relative_to(root)) for x in required if not x.exists()]
if missing:
    print("MANQUANT :", ", ".join(missing))
    raise SystemExit(1)

for secret in [root / "data/gdrive/token.json", root / "data/gdrive/credentials.json", root / "data/estn.db"]:
    print(f"Local seulement : {secret.relative_to(root)} -> {'présent' if secret.exists() else 'absent'}")

print("Préparation Streamlit Community Cloud : OK")
