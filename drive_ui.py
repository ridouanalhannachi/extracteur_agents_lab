from __future__ import annotations

from pathlib import Path

import streamlit as st

from app_config import APP_MODE, IS_CLOUD, DRIVE_ENABLED

from gdrive_sync import (
    CREDENTIALS_PATH,
    DRIVE_DB_NAME,
    DRIVE_FOLDER_NAME,
    auto_sync_enabled,
    connection_info,
    credentials_configured,
    disconnect,
    download_database,
    enable_auto_sync,
    get_credentials,
    save_credentials_json,
    sync_database,
    upload_database,
)


def _fmt_time(value):
    if not value:
        return "—"
    return str(value).replace("T", " ").replace("Z", " UTC")


def render_drive_module():
    st.title("☁️ Google Drive — Base de données")
    if not DRIVE_ENABLED:
        st.info("Laboratoire isolé : Google Drive est désactivé. Les données sont enregistrées uniquement dans la base locale du laboratoire.")
        return
    st.caption(
        "Google Drive conserve une copie synchronisée de data/estn.db. "
        "L'application travaille toujours sur une copie SQLite locale, puis synchronise de façon contrôlée pour éviter la corruption."
    )

    st.info(
        f"Dossier Drive utilisé : **{DRIVE_FOLDER_NAME}** / **{DRIVE_DB_NAME}**\n\n"
        "Accès demandé : uniquement aux fichiers créés ou utilisés par cette application (scope drive.file)."
    )

    st.subheader("1. Configuration Google")
    if IS_CLOUD:
        st.info("Mode Cloud : l'accès Google Drive est fourni par le secret GDRIVE_TOKEN_JSON.")
    else:
        if credentials_configured():
            st.success(f"credentials.json configuré : {CREDENTIALS_PATH}")
        else:
            st.warning("Ajoutez d'abord le fichier credentials.json créé dans Google Cloud.")

        uploaded = st.file_uploader(
            "credentials.json OAuth Google",
            type=["json"],
            key="gdrive_credentials_upload",
            help="Google Cloud → Google Drive API → OAuth Client ID → Application de bureau → Télécharger JSON.",
        )
        if uploaded is not None and st.button("💾 Enregistrer credentials.json", key="save_gdrive_credentials"):
            try:
                save_credentials_json(uploaded.getvalue())
                st.success("credentials.json enregistré.")
                st.rerun()
            except Exception as exc:
                st.error(f"Fichier refusé : {exc}")

    info = connection_info()
    st.subheader("2. Connexion au compte Google")
    if info["connected"]:
        st.success("Compte Google Drive connecté.")
        if not IS_CLOUD and st.button("Se déconnecter de Google Drive", key="gdrive_disconnect"):
            disconnect()
            st.rerun()
    else:
        st.warning("Google Drive n'est pas encore connecté.")
        if IS_CLOUD:
            st.error("Le secret GDRIVE_TOKEN_JSON est absent ou invalide dans l'environnement cloud.")
        elif st.button("🔐 Connecter mon compte Google Drive", type="primary", disabled=not credentials_configured()):
            try:
                with st.spinner("Une page Google va s'ouvrir. Autorisez l'accès puis revenez ici..."):
                    get_credentials(interactive=True)
                st.success("Connexion réussie.")
                st.rerun()
            except Exception as exc:
                st.error(f"Connexion impossible : {exc}")

    if not info["connected"]:
        st.stop()

    info = connection_info()
    remote = info.get("remote") or {}
    st.subheader("3. État de la synchronisation")
    c1, c2, c3 = st.columns(3)
    c1.metric("Base locale", "Présente" if info.get("local_exists") else "Absente")
    c2.metric("Base Drive", "Présente" if remote else "Absente")
    c3.metric("Dernière synchro", _fmt_time(info.get("last_sync")))

    if remote:
        st.caption(
            f"Drive : `{remote.get('name', DRIVE_DB_NAME)}` — dernière modification : "
            f"{_fmt_time(remote.get('modifiedTime'))} — ID : `{remote.get('id', '')}`"
        )

    if IS_CLOUD:
        st.success("Synchronisation automatique RH → Google Drive : activée obligatoirement en mode Cloud.")
    else:
        enabled = st.toggle(
            "Synchronisation automatique après les modifications RH",
            value=auto_sync_enabled(),
            help="Après un enregistrement RH, une résolution de conflit ou une règle apprise, la base est envoyée vers Drive.",
        )
        if enabled != auto_sync_enabled():
            enable_auto_sync(enabled)
            st.toast("Préférence de synchronisation enregistrée.")

    st.markdown("#### Synchroniser maintenant")
    if st.button("🔄 Synchroniser automatiquement", type="primary", width="stretch"):
        try:
            result = sync_database()
            st.session_state["gdrive_last_sync_result"] = result
        except Exception as exc:
            st.error(f"Synchronisation impossible : {exc}")

    result = st.session_state.get("gdrive_last_sync_result")
    if result:
        status = result.get("status")
        if status in {"uploaded", "downloaded", "up_to_date"}:
            st.success(result.get("message"))
        elif status in {"conflict", "first_choice"}:
            st.warning(result.get("message"))
            st.caption("Par sécurité, aucune base n'a été écrasée automatiquement.")
            left, right = st.columns(2)
            if left.button("⬇️ Utiliser la base Google Drive", width="stretch", key="gdrive_force_download"):
                try:
                    download_database()
                    st.session_state.pop("gdrive_last_sync_result", None)
                    st.success("Base Google Drive téléchargée. Recharge de l'application...")
                    st.rerun()
                except Exception as exc:
                    st.error(str(exc))
            if right.button("⬆️ Utiliser la base locale", width="stretch", key="gdrive_force_upload"):
                try:
                    upload_database()
                    st.session_state.pop("gdrive_last_sync_result", None)
                    st.success("Base locale envoyée vers Google Drive.")
                    st.rerun()
                except Exception as exc:
                    st.error(str(exc))

    with st.expander("Actions manuelles / dépannage", expanded=False):
        st.warning("Ces actions forcent un sens de synchronisation. Utilisez-les seulement si vous savez quelle copie est la bonne.")
        c1, c2 = st.columns(2)
        if c1.button("⬇️ Forcer Drive → PC", width="stretch"):
            try:
                download_database()
                st.success("Base Drive téléchargée.")
                st.rerun()
            except Exception as exc:
                st.error(str(exc))
        if c2.button("⬆️ Forcer PC → Drive", width="stretch"):
            try:
                upload_database()
                st.success("Base locale envoyée sur Drive.")
                st.rerun()
            except Exception as exc:
                st.error(str(exc))

    st.divider()
    st.caption(
        "La base n'est jamais ouverte directement depuis Google Drive. Elle reste locale pendant l'utilisation, "
        "et Drive sert de copie centrale synchronisée."
    )
