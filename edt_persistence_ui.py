"""Keep EDT synchronization failures visible across Streamlit reruns."""
import streamlit as st

from gdrive_sync import auto_upload_after_change

_SYNC_ERROR = "edt_pending_sync_error"


def sync_edt_changes():
    """Save locally first; never turn a Drive failure into a failed local save."""
    try:
        ok, message = auto_upload_after_change()
    except Exception as exc:
        ok, message = False, f"Synchronisation impossible : {exc}"
    if ok:
        st.session_state.pop(_SYNC_ERROR, None)
    else:
        st.session_state[_SYNC_ERROR] = message
    return ok, message


def render_edt_sync_status():
    if _SYNC_ERROR not in st.session_state:
        return
    st.warning(
        "Les modifications EDT sont enregistrées dans la base locale, "
        "mais leur sauvegarde Google Drive n'est pas confirmée. "
        "Sur le Cloud, elles peuvent être perdues au redémarrage. "
        + st.session_state[_SYNC_ERROR]
    )
    if st.button("🔄 Réessayer la sauvegarde Google Drive", key="edt_retry_sync"):
        ok, message = sync_edt_changes()
        if ok:
            st.rerun()
        else:
            st.warning(message)
