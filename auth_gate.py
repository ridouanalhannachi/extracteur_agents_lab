from __future__ import annotations

import hmac
import os
import streamlit as st


def require_login() -> None:
    """Protection simple pour le déploiement personnel Cloud Run.

    En local, si APP_PASSWORD n'est pas défini, aucune connexion n'est demandée.
    En cloud, APP_PASSWORD doit être fourni via Secret Manager.
    """
    expected = os.environ.get("APP_PASSWORD", "")
    if not expected:
        return

    if st.session_state.get("app_authenticated"):
        return

    st.title("🔐 Extracteur EDT + RH")
    st.caption("Accès personnel")
    value = st.text_input("Mot de passe", type="password", key="app_login_password")
    if st.button("Se connecter", type="primary"):
        if hmac.compare_digest(value or "", expected):
            st.session_state["app_authenticated"] = True
            st.rerun()
        else:
            st.error("Mot de passe incorrect.")
    st.stop()
