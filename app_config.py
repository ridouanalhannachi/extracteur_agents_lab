from __future__ import annotations

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
# This independent laboratory must never inherit production paths or secrets.
# Cloud hosting also starts locally: no automatic Drive restoration is allowed.
APP_MODE = "lab"
IS_STREAMLIT_CLOUD = False
IS_CLOUD = False
DRIVE_ENABLED = False

DATA_DIR = BASE_DIR / "data-lab"
DB_PATH = DATA_DIR / "estn-lab.db"
GDRIVE_DIR = DATA_DIR / "gdrive"
LOCAL_BACKUP_DIR = DATA_DIR / "backups"

DATA_DIR.mkdir(parents=True, exist_ok=True)
GDRIVE_DIR.mkdir(parents=True, exist_ok=True)
LOCAL_BACKUP_DIR.mkdir(parents=True, exist_ok=True)
