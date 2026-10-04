from __future__ import annotations

from typing import Dict

from app_config import DB_PATH, IS_CLOUD

_BOOTSTRAPPED = False
_LAST_RESULT: Dict = {}


def bootstrap_cloud_database() -> Dict:
    """Restore the active SQLite database from Google Drive once per process.

    In cloud mode the local filesystem is disposable. For safety, the app refuses
    to start with an empty temporary database when Drive is unavailable.
    """
    global _BOOTSTRAPPED, _LAST_RESULT
    if _BOOTSTRAPPED:
        return _LAST_RESULT

    if not IS_CLOUD:
        _BOOTSTRAPPED = True
        _LAST_RESULT = {"status": "local", "message": "Mode local."}
        return _LAST_RESULT

    try:
        from gdrive_sync import download_database, get_remote_info, is_connected

        if not is_connected():
            _LAST_RESULT = {
                "status": "error",
                "message": "Google Drive n'est pas connecté. Vérifiez le secret GDRIVE_TOKEN_JSON.",
            }
            return _LAST_RESULT

        remote = get_remote_info()
        if not remote:
            _LAST_RESULT = {
                "status": "error",
                "message": "Aucune base estn.db n'a été trouvée dans Google Drive. Synchronisez d'abord la base locale vers Drive.",
            }
            return _LAST_RESULT

        download_database(create_local_backup=False)
        _LAST_RESULT = {"status": "downloaded", "message": "Base restaurée depuis Google Drive."}
    except Exception as exc:
        _LAST_RESULT = {"status": "error", "message": f"Initialisation Drive impossible : {exc}"}

    # A temporary Drive failure must not block every subsequent rerun.
    # Once restoration succeeds, never download again over local changes.
    _BOOTSTRAPPED = _LAST_RESULT.get("status") == "downloaded"
    return _LAST_RESULT
