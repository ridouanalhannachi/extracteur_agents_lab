from __future__ import annotations

import json
import re
import sqlite3
import unicodedata

import pandas as pd
import streamlit as st

from app_config import DB_PATH


STOP_WORDS = {
    "de", "du", "des", "le", "la", "les", "un", "une",
    "salle", "prof", "professeur", "enseignant", "enseignante",
    "module", "matiere", "matière", "filiere", "filière",
    "semestre", "niveau", "version", "emploi", "edt",
}


def _clean(value):
    if value is None:
        return ""
    try:
        if pd.isna(value):
            return ""
    except Exception:
        pass
    return re.sub(r"\s+", " ", str(value)).strip()


def _norm(value):
    text = unicodedata.normalize("NFKD", _clean(value))
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.lower()
    text = text.replace("_", " ").replace("-", " ")
    text = re.sub(r"[^a-z0-9@.+/ ]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _query_tokens(query):
    raw = _norm(query)
    tokens = [t for t in raw.split() if t and t not in STOP_WORDS]
    return tokens or ([raw] if raw else [])


def _table_exists(conn, name):
    return conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
        (name,),
    ).fetchone() is not None


def _columns(conn, table):
    if not _table_exists(conn, table):
        return set()
    return {row[1] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()}


def _matches(search_text, tokens):
    text = _norm(search_text)
    return all(token in text for token in tokens)


def _load_sessions_index():
    with sqlite3.connect(DB_PATH) as conn:
        if not (
            _table_exists(conn, "edt_sessions")
            and _table_exists(conn, "edt_versions")
            and _table_exists(conn, "edt_timetables")
        ):
            return pd.DataFrame()

        vcols = _columns(conn, "edt_versions")
        active_expr = "v.is_active" if "is_active" in vcols else "0"
        status_expr = "v.status" if "status" in vcols else "''"
        comment_expr = "v.comment" if "comment" in vcols else "''"

        sql = f"""
            SELECT
                s.id AS session_id,
                s.version_id,
                v.version_number,
                {active_expr} AS is_active,
                {status_expr} AS version_status,
                {comment_expr} AS version_comment,
                t.id AS timetable_id,
                t.academic_year,
                t.period,
                t.filiere,
                t.niveau,
                s.jour,
                s.horaire,
                s.matiere,
                s.type_seance,
                s.enseignant,
                s.groupe,
                s.salle,
                s.duree,
                s.source_document,
                s.page
            FROM edt_sessions s
            JOIN edt_versions v ON v.id = s.version_id
            JOIN edt_timetables t ON t.id = v.timetable_id
            ORDER BY
                t.academic_year DESC,
                t.filiere,
                t.niveau,
                v.version_number DESC,
                s.jour,
                s.horaire
        """
        return pd.read_sql_query(sql, conn)


def _load_versions_index():
    with sqlite3.connect(DB_PATH) as conn:
        if not (
            _table_exists(conn, "edt_versions")
            and _table_exists(conn, "edt_timetables")
        ):
            return pd.DataFrame()

        cols = _columns(conn, "edt_versions")
        active_expr = "v.is_active" if "is_active" in cols else "0"
        status_expr = "v.status" if "status" in cols else "''"
        source_expr = "v.source_documents" if "source_documents" in cols else "''"
        comment_expr = "v.comment" if "comment" in cols else "''"
        count_expr = "v.sessions_count" if "sessions_count" in cols else "0"

        sql = f"""
            SELECT
                v.id AS version_id,
                v.timetable_id,
                v.version_number,
                v.imported_at,
                {active_expr} AS is_active,
                {status_expr} AS status,
                {source_expr} AS source_documents,
                {comment_expr} AS comment,
                {count_expr} AS sessions_count,
                t.academic_year,
                t.period,
                t.filiere,
                t.niveau
            FROM edt_versions v
            JOIN edt_timetables t ON t.id = v.timetable_id
            ORDER BY
                t.academic_year DESC,
                t.filiere,
                t.niveau,
                v.version_number DESC
        """
        return pd.read_sql_query(sql, conn)


def _safe_change_select(conn):
    if not _table_exists(conn, "edt_version_changes"):
        return pd.DataFrame()

    cols = _columns(conn, "edt_version_changes")

    def expr(name, fallback="''"):
        return name if name in cols else fallback

    sql = f"""
        SELECT
            {expr("id", "NULL")} AS id,
            {expr("from_version_id", "NULL")} AS from_version_id,
            {expr("to_version_id", "NULL")} AS to_version_id,
            {expr("change_type")} AS change_type,
            {expr("matiere")} AS matiere,
            {expr("enseignant")} AS enseignant,
            {expr("groupe")} AS groupe,
            {expr("type_seance")} AS type_seance,
            {expr("changed_fields")} AS changed_fields,
            {expr("old_data_json")} AS old_data_json,
            {expr("new_data_json")} AS new_data_json,
            {expr("created_at")} AS created_at
        FROM edt_version_changes
        ORDER BY id DESC
    """
    try:
        return pd.read_sql_query(sql, conn)
    except Exception:
        return pd.DataFrame()


def _load_changes_index():
    with sqlite3.connect(DB_PATH) as conn:
        changes = _safe_change_select(conn)
        if changes.empty:
            return changes

        version_map = {}
        if _table_exists(conn, "edt_versions") and _table_exists(conn, "edt_timetables"):
            rows = conn.execute(
                """
                SELECT
                    v.id,
                    v.version_number,
                    v.timetable_id,
                    t.academic_year,
                    t.period,
                    t.filiere,
                    t.niveau
                FROM edt_versions v
                JOIN edt_timetables t ON t.id=v.timetable_id
                """
            ).fetchall()
            for row in rows:
                version_map[int(row[0])] = {
                    "version_number": int(row[1]),
                    "timetable_id": int(row[2]),
                    "academic_year": _clean(row[3]),
                    "period": _clean(row[4]),
                    "filiere": _clean(row[5]),
                    "niveau": _clean(row[6]),
                }

    enriched = []
    for _, row in changes.iterrows():
        item = row.to_dict()

        try:
            to_id = int(item.get("to_version_id")) if pd.notna(item.get("to_version_id")) else None
        except Exception:
            to_id = None

        try:
            from_id = int(item.get("from_version_id")) if pd.notna(item.get("from_version_id")) else None
        except Exception:
            from_id = None

        to_meta = version_map.get(to_id, {})
        from_meta = version_map.get(from_id, {})

        item.update({
            "version_number": to_meta.get("version_number"),
            "previous_version_number": from_meta.get("version_number"),
            "timetable_id": to_meta.get("timetable_id"),
            "academic_year": to_meta.get("academic_year", ""),
            "period": to_meta.get("period", ""),
            "filiere": to_meta.get("filiere", ""),
            "niveau": to_meta.get("niveau", ""),
        })

        try:
            old = json.loads(_clean(item.get("old_data_json")) or "{}")
        except Exception:
            old = {}
        try:
            new = json.loads(_clean(item.get("new_data_json")) or "{}")
        except Exception:
            new = {}

        item["old_summary"] = " | ".join(
            x for x in [
                _clean(old.get("Jour")),
                _clean(old.get("Horaire")),
                _clean(old.get("Salle")),
                _clean(old.get("Nom et prénom")),
            ] if x
        )
        item["new_summary"] = " | ".join(
            x for x in [
                _clean(new.get("Jour")),
                _clean(new.get("Horaire")),
                _clean(new.get("Salle")),
                _clean(new.get("Nom et prénom")),
            ] if x
        )

        enriched.append(item)

    return pd.DataFrame(enriched)


def _search_sessions(query):
    tokens = _query_tokens(query)
    if not tokens:
        return pd.DataFrame()

    frame = _load_sessions_index()
    if frame.empty:
        return frame

    def text(row):
        return " ".join([
            f"annee {row.get('academic_year', '')}",
            f"periode {row.get('period', '')}",
            f"filiere {row.get('filiere', '')}",
            f"semestre {row.get('niveau', '')}",
            f"jour {row.get('jour', '')}",
            f"horaire {row.get('horaire', '')}",
            f"matiere module {row.get('matiere', '')}",
            f"type {row.get('type_seance', '')}",
            f"enseignant professeur {row.get('enseignant', '')}",
            f"groupe {row.get('groupe', '')}",
            f"salle {row.get('salle', '')}",
            f"document {row.get('source_document', '')}",
            f"version v{row.get('version_number', '')}",
            f"commentaire {row.get('version_comment', '')}",
        ])

    mask = frame.apply(lambda row: _matches(text(row), tokens), axis=1)
    return frame[mask].copy()


def _search_versions(query):
    tokens = _query_tokens(query)
    if not tokens:
        return pd.DataFrame()

    frame = _load_versions_index()
    if frame.empty:
        return frame

    def text(row):
        return " ".join([
            f"annee {row.get('academic_year', '')}",
            f"periode {row.get('period', '')}",
            f"filiere {row.get('filiere', '')}",
            f"semestre {row.get('niveau', '')}",
            f"version v{row.get('version_number', '')}",
            f"statut {row.get('status', '')}",
            f"document {row.get('source_documents', '')}",
            f"commentaire {row.get('comment', '')}",
        ])

    mask = frame.apply(lambda row: _matches(text(row), tokens), axis=1)
    return frame[mask].copy()


def _search_changes(query):
    tokens = _query_tokens(query)
    if not tokens:
        return pd.DataFrame()

    frame = _load_changes_index()
    if frame.empty:
        return frame

    def text(row):
        return " ".join([
            f"annee {row.get('academic_year', '')}",
            f"periode {row.get('period', '')}",
            f"filiere {row.get('filiere', '')}",
            f"semestre {row.get('niveau', '')}",
            f"version v{row.get('version_number', '')}",
            f"matiere module {row.get('matiere', '')}",
            f"enseignant professeur {row.get('enseignant', '')}",
            f"groupe {row.get('groupe', '')}",
            f"type {row.get('type_seance', '')}",
            f"changement {row.get('change_type', '')}",
            f"champs {row.get('changed_fields', '')}",
            f"avant {row.get('old_summary', '')}",
            f"apres {row.get('new_summary', '')}",
            f"old {row.get('old_data_json', '')}",
            f"new {row.get('new_data_json', '')}",
        ])

    mask = frame.apply(lambda row: _matches(text(row), tokens), axis=1)
    return frame[mask].copy()


def _display_sessions(frame):
    if frame.empty:
        st.info("Aucune séance trouvée.")
        return

    out = pd.DataFrame({
        "Année": frame["academic_year"],
        "Période": frame["period"],
        "Filière": frame["filiere"],
        "Semestre": frame["niveau"],
        "Version": frame["version_number"].map(lambda x: f"V{int(x)}"),
        "Active": frame["is_active"].map(lambda x: "✅" if int(x or 0) else ""),
        "Jour": frame["jour"],
        "Horaire": frame["horaire"],
        "Matière": frame["matiere"],
        "Type": frame["type_seance"],
        "Enseignant": frame["enseignant"],
        "Groupe": frame["groupe"],
        "Salle": frame["salle"],
        "Document": frame["source_document"],
    })
    st.dataframe(out, width="stretch", hide_index=True)


def _display_versions(frame):
    if frame.empty:
        st.info("Aucune version trouvée.")
        return

    out = pd.DataFrame({
        "Année": frame["academic_year"],
        "Période": frame["period"],
        "Filière": frame["filiere"],
        "Semestre": frame["niveau"],
        "Version": frame["version_number"].map(lambda x: f"V{int(x)}"),
        "Active": frame["is_active"].map(lambda x: "✅" if int(x or 0) else ""),
        "Statut": frame["status"],
        "Séances": frame["sessions_count"],
        "Date import": frame["imported_at"],
        "Commentaire": frame["comment"],
    })
    st.dataframe(out, width="stretch", hide_index=True)


def _display_changes(frame):
    if frame.empty:
        st.info("Aucun changement trouvé.")
        return

    labels = {
        "modified": "🟠 Modifiée",
        "added": "🟢 Ajoutée",
        "removed": "🔴 Supprimée",
    }

    def version_label(row):
        current = row.get("version_number")
        previous = row.get("previous_version_number")
        if pd.isna(current):
            return ""
        if previous is None or pd.isna(previous):
            return f"V{int(current)}"
        return f"V{int(previous)} → V{int(current)}"

    out = pd.DataFrame({
        "Année": frame["academic_year"],
        "Période": frame["period"],
        "Filière": frame["filiere"],
        "Semestre": frame["niveau"],
        "Version": frame.apply(version_label, axis=1),
        "Changement": frame["change_type"].map(lambda x: labels.get(_clean(x), _clean(x))),
        "Matière": frame["matiere"],
        "Enseignant": frame["enseignant"],
        "Groupe": frame["groupe"],
        "Type": frame["type_seance"],
        "Champs": frame["changed_fields"],
        "Avant": frame["old_summary"],
        "Après": frame["new_summary"],
    })
    st.dataframe(out, width="stretch", hide_index=True)


def _render_version_detail(version_id):
    versions = _load_versions_index()
    if versions.empty:
        return

    selected = versions[versions["version_id"] == int(version_id)]
    if selected.empty:
        return

    row = selected.iloc[0]
    version_number = int(row["version_number"])

    st.markdown(
        f'### 📅 {row["filiere"]} {row["niveau"]} — '
        f'{row["period"]} {row["academic_year"]} — V{version_number}'
    )

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Version", f"V{version_number}")
    c2.metric("Active", "Oui" if int(row.get("is_active", 0) or 0) else "Non")
    c3.metric("Statut", _clean(row.get("status")) or "-")
    c4.metric("Séances", int(row.get("sessions_count", 0) or 0))

    with sqlite3.connect(DB_PATH) as conn:
        sessions = pd.read_sql_query(
            """
            SELECT
                jour AS "Jour",
                horaire AS "Horaire",
                matiere AS "Matière",
                type_seance AS "Type",
                enseignant AS "Enseignant",
                groupe AS "Groupe",
                salle AS "Salle",
                duree AS "Durée",
                source_document AS "Document"
            FROM edt_sessions
            WHERE version_id=?
            ORDER BY
                CASE jour
                    WHEN 'Lundi' THEN 1
                    WHEN 'Mardi' THEN 2
                    WHEN 'Mercredi' THEN 3
                    WHEN 'Jeudi' THEN 4
                    WHEN 'Vendredi' THEN 5
                    WHEN 'Samedi' THEN 6
                    ELSE 7
                END,
                horaire
            """,
            conn,
            params=(int(version_id),),
        )

    st.dataframe(sessions, width="stretch", hide_index=True)

    changes = _load_changes_index()
    if not changes.empty:
        current_changes = changes[changes["to_version_id"] == int(version_id)]
        if not current_changes.empty:
            st.markdown("#### 🔄 Changements associés à cette version")
            _display_changes(current_changes)


def render_global_edt_search():
    st.title("🔎 Recherche globale EDT")
    st.caption(
        "Recherchez dans toutes les séances, versions et modifications archivées. "
        "Exemples : DAOUDI, Salle A12, RT S3, Réseaux."
    )

    query = st.text_input(
        "Recherche",
        placeholder="Ex. DAOUDI, Salle A12, RT S3, Réseaux...",
        key="global_edt_search_query",
    )

    if not query.strip():
        st.info("Saisissez un nom, une salle, une filière, un semestre, une matière ou une version.")
        st.markdown(
            "**Exemples :** `DAOUDI` · `Salle A12` · `RT S3` · `Réseaux` · `V3` · `Automne`"
        )
        return

    sessions = _search_sessions(query)
    versions = _search_versions(query)
    changes = _search_changes(query)

    c1, c2, c3 = st.columns(3)
    c1.metric("Séances trouvées", len(sessions))
    c2.metric("Versions trouvées", len(versions))
    c3.metric("Changements trouvés", len(changes))

    tab1, tab2, tab3 = st.tabs([
        f"📅 Séances ({len(sessions)})",
        f"🗂️ Versions ({len(versions)})",
        f"🔄 Changements ({len(changes)})",
    ])

    with tab1:
        _display_sessions(sessions)

    with tab2:
        _display_versions(versions)

    with tab3:
        _display_changes(changes)

    candidate_versions = {}

    for _, row in sessions.iterrows():
        label = (
            f'{row["filiere"]} {row["niveau"]} | '
            f'{row["period"]} {row["academic_year"]} | '
            f'V{int(row["version_number"])}'
        )
        candidate_versions[label] = int(row["version_id"])

    for _, row in versions.iterrows():
        label = (
            f'{row["filiere"]} {row["niveau"]} | '
            f'{row["period"]} {row["academic_year"]} | '
            f'V{int(row["version_number"])}'
        )
        candidate_versions[label] = int(row["version_id"])

    if candidate_versions:
        st.divider()
        st.markdown("### 👁️ Ouvrir une version trouvée")
        selected_label = st.selectbox(
            "Version",
            list(candidate_versions.keys()),
            key="global_edt_search_version_detail",
        )
        _render_version_detail(candidate_versions[selected_label])
