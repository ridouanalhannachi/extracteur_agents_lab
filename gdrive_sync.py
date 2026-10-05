from __future__ import annotations

import hashlib
import base64
import io
import json
import os
import shutil
import sqlite3
import subprocess
import tempfile
import webbrowser
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional, Tuple

from app_config import APP_MODE, BASE_DIR, DATA_DIR, DB_PATH, GDRIVE_DIR, LOCAL_BACKUP_DIR, IS_CLOUD, DRIVE_ENABLED

if DRIVE_ENABLED:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload

CREDENTIALS_PATH = GDRIVE_DIR / "credentials.json"
TOKEN_PATH = GDRIVE_DIR / "token.json"
STATE_PATH = GDRIVE_DIR / "sync_state.json"

DRIVE_FOLDER_NAME = "Extracteur_EDT_RH_Lab"
DRIVE_BACKUP_FOLDER_NAME = "backups"
DRIVE_DB_NAME = "estn-lab.db"
SCOPES = ["https://www.googleapis.com/auth/drive.file"]


def _require_drive_enabled() -> None:
    if not DRIVE_ENABLED:
        raise RuntimeError("Google Drive est désactivé dans ce laboratoire isolé.")


def _ensure_dirs() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    GDRIVE_DIR.mkdir(parents=True, exist_ok=True)
    LOCAL_BACKUP_DIR.mkdir(parents=True, exist_ok=True)


def save_credentials_json(raw: bytes) -> Path:
    _require_drive_enabled()
    _ensure_dirs()
    parsed = json.loads(raw.decode("utf-8-sig"))
    if not isinstance(parsed, dict) or not ("installed" in parsed or "web" in parsed):
        raise ValueError("Le fichier ne ressemble pas à un credentials.json OAuth Google valide.")
    CREDENTIALS_PATH.write_bytes(raw)
    return CREDENTIALS_PATH


def credentials_configured() -> bool:
    if not DRIVE_ENABLED:
        return False
    return CREDENTIALS_PATH.exists() or bool(os.environ.get("GDRIVE_TOKEN_JSON", "").strip()) or bool(os.environ.get("GDRIVE_TOKEN_B64", "").strip())


def _load_state() -> Dict:
    if not STATE_PATH.exists():
        return {}
    try:
        return json.loads(STATE_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save_state(state: Dict) -> None:
    _ensure_dirs()
    STATE_PATH.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def disconnect() -> None:
    if TOKEN_PATH.exists():
        TOKEN_PATH.unlink()
    # Un secret Cloud Run ne peut pas être supprimé depuis l'application.


def _open_windows_browser(url: str) -> bool:
    """Ouvre l'URL OAuth dans le navigateur Windows depuis WSL.

    On évite PowerShell/Start-Process car les caractères ``&`` présents dans
    les URL OAuth peuvent être mal interprétés. ``explorer.exe`` reçoit l'URL
    comme un argument unique et la transmet au navigateur Windows par défaut.
    """
    if os.environ.get("WSL_DISTRO_NAME"):
        candidates = [
            Path("/mnt/c/Windows/explorer.exe"),
            Path("/mnt/c/Windows/System32/cmd.exe"),
        ]
        try:
            if candidates[0].exists():
                subprocess.Popen(
                    [str(candidates[0]), url],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                return True
            if candidates[1].exists():
                subprocess.Popen(
                    [str(candidates[1]), "/c", "start", "", url],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                return True
        except Exception:
            pass
    try:
        return bool(webbrowser.open(url))
    except Exception:
        return False


def get_credentials(interactive: bool = False) -> Optional[Credentials]:
    if not DRIVE_ENABLED:
        if interactive:
            _require_drive_enabled()
        return None
    _ensure_dirs()
    creds = None

    env_token = os.environ.get("GDRIVE_TOKEN_JSON", "").strip()
    env_token_b64 = os.environ.get("GDRIVE_TOKEN_B64", "").strip()

    if not env_token and env_token_b64:
        try:
            env_token = base64.b64decode(env_token_b64).decode("utf-8")
        except Exception:
            env_token = ""

    if env_token:
        try:
            creds = Credentials.from_authorized_user_info(json.loads(env_token), SCOPES)
        except Exception:
            creds = None

    if creds is None and TOKEN_PATH.exists():
        try:
            creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)
        except Exception:
            creds = None

    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            TOKEN_PATH.write_text(creds.to_json(), encoding="utf-8")
        except Exception:
            creds = None

    if creds and creds.valid:
        return creds

    if not interactive:
        return None
    if IS_CLOUD:
        raise RuntimeError("En mode cloud, configurez GDRIVE_TOKEN_JSON dans les secrets de la plateforme.")
    if not CREDENTIALS_PATH.exists():
        raise FileNotFoundError("credentials.json n'est pas encore configuré.")

    flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_PATH), SCOPES)

    # Le flux OAuth tourne dans WSL mais le navigateur est sous Windows.
    # 127.0.0.1 évite les ambiguïtés IPv4/IPv6 de "localhost".
    # bind_addr=0.0.0.0 permet à la redirection Windows -> WSL d'atteindre
    # le petit serveur OAuth local. Un timeout évite un chargement infini.
    original_open = webbrowser.open
    webbrowser.open = lambda url, *args, **kwargs: _open_windows_browser(url)
    try:
        creds = flow.run_local_server(
            host="127.0.0.1",
            bind_addr="0.0.0.0",
            port=0,
            open_browser=True,
            authorization_prompt_message=(
                "Si le navigateur ne s'ouvre pas automatiquement, copiez cette URL "
                "dans le navigateur Windows : {url}"
            ),
            success_message=(
                "Connexion Google Drive réussie. Vous pouvez fermer cette fenêtre "
                "et revenir dans l'application."
            ),
            access_type="offline",
            prompt="consent",
            timeout=180,
        )
    finally:
        webbrowser.open = original_open

    TOKEN_PATH.write_text(creds.to_json(), encoding="utf-8")
    return creds


def is_connected() -> bool:
    creds = get_credentials(interactive=False)
    return bool(creds and creds.valid)


def _service(interactive: bool = False):
    _require_drive_enabled()
    creds = get_credentials(interactive=interactive)
    if not creds:
        raise RuntimeError("Google Drive n'est pas connecté.")
    return build("drive", "v3", credentials=creds, cache_discovery=False)


def _escape_q(value: str) -> str:
    return value.replace("'", "\\'")


def _find_named(service, name: str, parent_id: Optional[str] = None, mime_type: Optional[str] = None):
    clauses = [f"name='{_escape_q(name)}'", "trashed=false"]
    if parent_id:
        clauses.append(f"'{parent_id}' in parents")
    if mime_type:
        clauses.append(f"mimeType='{mime_type}'")
    result = service.files().list(
        q=" and ".join(clauses),
        spaces="drive",
        fields="files(id,name,mimeType,modifiedTime,md5Checksum,parents,size)",
        pageSize=20,
    ).execute()
    files = result.get("files", [])
    return files[0] if files else None


def _ensure_folder(service, name: str, parent_id: Optional[str] = None) -> str:
    mime = "application/vnd.google-apps.folder"
    found = _find_named(service, name, parent_id=parent_id, mime_type=mime)
    if found:
        return found["id"]
    body = {"name": name, "mimeType": mime}
    if parent_id:
        body["parents"] = [parent_id]
    created = service.files().create(body=body, fields="id").execute()
    return created["id"]


def ensure_drive_structure(service=None) -> Tuple[str, str]:
    _require_drive_enabled()
    service = service or _service()
    root_id = _ensure_folder(service, DRIVE_FOLDER_NAME)
    backups_id = _ensure_folder(service, DRIVE_BACKUP_FOLDER_NAME, root_id)
    state = _load_state()
    state.update({"drive_folder_id": root_id, "drive_backup_folder_id": backups_id})
    _save_state(state)
    return root_id, backups_id


def _drive_db(service, folder_id: str):
    return _find_named(service, DRIVE_DB_NAME, parent_id=folder_id)


def _md5_file(path: Path) -> Optional[str]:
    if not path.exists():
        return None
    h = hashlib.md5()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _sqlite_snapshot(source: Path, target: Path) -> None:
    if not source.exists():
        source.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(source):
            pass
    with sqlite3.connect(source) as src, sqlite3.connect(target) as dst:
        src.backup(dst)


def _validate_sqlite(path: Path) -> None:
    with sqlite3.connect(path) as conn:
        result = conn.execute("PRAGMA integrity_check").fetchone()
    if not result or str(result[0]).lower() != "ok":
        raise RuntimeError("La base téléchargée depuis Drive n'a pas passé le contrôle d'intégrité SQLite.")


def _local_backup(label: str = "before_drive_replace") -> Optional[Path]:
    if not DB_PATH.exists():
        return None
    _ensure_dirs()
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    target = LOCAL_BACKUP_DIR / f"estn_{label}_{stamp}.db"
    _sqlite_snapshot(DB_PATH, target)
    return target


def get_remote_info() -> Optional[Dict]:
    service = _service()
    folder_id, _ = ensure_drive_structure(service)
    return _drive_db(service, folder_id)


def connection_info() -> Dict:
    state = _load_state()
    connected = is_connected()
    info = {
        "connected": connected,
        "credentials_configured": credentials_configured(),
        "local_db": str(DB_PATH),
        "local_exists": DB_PATH.exists(),
        "local_md5": _md5_file(DB_PATH),
        "last_sync": state.get("last_sync"),
        "last_synced_md5": state.get("last_synced_md5"),
        "drive_file_id": state.get("drive_file_id"),
    }
    if connected:
        try:
            remote = get_remote_info()
            info["remote"] = remote
        except Exception as exc:
            info["remote_error"] = str(exc)
    return info


class RemoteOverwriteBlocked(RuntimeError):
    """An existing remote database cannot safely be replaced by this client."""

    def __init__(self, remote: Dict):
        self.remote = remote
        super().__init__(
            "Conflit de sauvegarde : mémoire locale conservée. "
            "Remplacement de la base Google Drive bloqué en l'absence de "
            "protection atomique contre les écritures concurrentes."
        )


def upload_database(create_remote_backup: bool = True) -> Dict:
    """Create the first remote database; never overwrite an existing database.

    ``create_remote_backup`` remains accepted for existing callers but cannot
    bypass the guard. A preceding read/copy does not protect a later update
    against another client. Concurrent first creations can still produce
    duplicate files; this is not an atomic create-if-absent implementation.
    """
    service = _service()
    folder_id, _ = ensure_drive_structure(service)
    _ensure_dirs()

    with tempfile.TemporaryDirectory() as tmp:
        snapshot = Path(tmp) / DRIVE_DB_NAME
        _sqlite_snapshot(DB_PATH, snapshot)
        _validate_sqlite(snapshot)
        local_md5 = _md5_file(snapshot)

        remote = _drive_db(service, folder_id)
        if remote:
            # Refuse before copy/update and before recording any sync success.
            raise RemoteOverwriteBlocked(remote)

        media = MediaFileUpload(str(snapshot), mimetype="application/x-sqlite3", resumable=False)
        result = service.files().create(
            body={"name": DRIVE_DB_NAME, "parents": [folder_id]},
            media_body=media,
            fields="id,name,modifiedTime,md5Checksum,size",
        ).execute()

    state = _load_state()
    state.update({
        "drive_file_id": result["id"],
        "last_sync": datetime.now(timezone.utc).isoformat(),
        "last_synced_md5": result.get("md5Checksum") or local_md5,
        "last_action": "upload",
    })
    _save_state(state)
    return result


def _sync_upload(create_remote_backup: bool = True) -> Dict:
    """Adapt a blocked upload to the conflict result understood by the UI."""
    try:
        result = upload_database(create_remote_backup=create_remote_backup)
    except RemoteOverwriteBlocked as exc:
        return {"status": "conflict", "message": str(exc), "remote": exc.remote}
    return {"status": "uploaded", "message": "Première base envoyée vers Google Drive.", "remote": result}


def download_database(create_local_backup: bool = True) -> Dict:
    service = _service()
    folder_id, _ = ensure_drive_structure(service)
    remote = _drive_db(service, folder_id)
    if not remote:
        raise FileNotFoundError("Aucune base estn.db n'existe encore dans Google Drive.")

    if create_local_backup:
        _local_backup("before_drive_download")
    _ensure_dirs()
    fd, tmp_name = tempfile.mkstemp(prefix="estn_drive_", suffix=".db", dir=str(DATA_DIR))
    os.close(fd)
    tmp_path = Path(tmp_name)
    try:
        request = service.files().get_media(fileId=remote["id"])
        with tmp_path.open("wb") as fh:
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while not done:
                _, done = downloader.next_chunk()
        _validate_sqlite(tmp_path)
        os.replace(tmp_path, DB_PATH)
    finally:
        if tmp_path.exists():
            tmp_path.unlink(missing_ok=True)

    local_md5 = _md5_file(DB_PATH)
    state = _load_state()
    state.update({
        "drive_file_id": remote["id"],
        "last_sync": datetime.now(timezone.utc).isoformat(),
        "last_synced_md5": remote.get("md5Checksum") or local_md5,
        "last_action": "download",
    })
    _save_state(state)
    return remote


def sync_database() -> Dict:
    """Synchronisation prudente basée sur le dernier hash synchronisé.

    - Drive absent : upload de la base locale.
    - Local identique au dernier sync et Drive modifié : download.
    - Drive identique au dernier sync et local modifié : remplacement bloqué.
    - Les deux ont changé : renvoie 'conflict' sans écriture distante.
    """
    service = _service()
    folder_id, _ = ensure_drive_structure(service)
    remote = _drive_db(service, folder_id)
    local_md5 = _md5_file(DB_PATH)
    state = _load_state()
    last = state.get("last_synced_md5")

    if not remote:
        if not DB_PATH.exists():
            DB_PATH.parent.mkdir(parents=True, exist_ok=True)
            with sqlite3.connect(DB_PATH):
                pass
        return _sync_upload(create_remote_backup=False)

    remote_md5 = remote.get("md5Checksum")
    if local_md5 == remote_md5 and local_md5 is not None:
        state.update({
            "drive_file_id": remote["id"],
            "last_sync": datetime.now(timezone.utc).isoformat(),
            "last_synced_md5": remote_md5,
            "last_action": "noop",
        })
        _save_state(state)
        return {"status": "up_to_date", "message": "La base locale et Google Drive sont déjà identiques.", "remote": remote}

    if last:
        local_changed = local_md5 != last
        remote_changed = remote_md5 != last
        if local_changed and remote_changed:
            return {
                "status": "conflict",
                "message": "La base locale et la base Google Drive ont toutes les deux changé depuis la dernière synchronisation.",
                "local_md5": local_md5,
                "remote_md5": remote_md5,
                "remote": remote,
            }
        if remote_changed and not local_changed:
            result = download_database()
            return {"status": "downloaded", "message": "Version Google Drive téléchargée.", "remote": result}
        if local_changed and not remote_changed:
            return _sync_upload()

    # Première synchronisation sur cet appareil : ne jamais écraser silencieusement.
    return {
        "status": "first_choice",
        "message": "Une base existe déjà dans Google Drive et une base locale existe aussi. Choisissez laquelle doit devenir la référence.",
        "local_md5": local_md5,
        "remote_md5": remote_md5,
        "remote": remote,
    }


def enable_auto_sync(enabled: bool) -> None:
    if enabled:
        _require_drive_enabled()
    state = _load_state()
    state["auto_sync"] = bool(enabled)
    _save_state(state)


def auto_sync_enabled() -> bool:
    if not DRIVE_ENABLED:
        return False
    # Le stockage local des plateformes cloud est éphémère. En cloud, chaque
    # modification RH doit donc être renvoyée vers Drive automatiquement.
    if IS_CLOUD:
        return True
    return bool(_load_state().get("auto_sync", False))


def auto_upload_after_change() -> Tuple[bool, str]:
    if not auto_sync_enabled() or not is_connected():
        return False, "Synchronisation automatique désactivée."
    try:
        upload_database(create_remote_backup=False)
        return True, "Base synchronisée automatiquement avec Google Drive."
    except Exception as exc:
        return False, f"Synchronisation automatique impossible : {exc}"
