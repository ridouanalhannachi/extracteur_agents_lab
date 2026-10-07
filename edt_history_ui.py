from __future__ import annotations

import json
import sqlite3

import pandas as pd
import streamlit as st

from app_config import DB_PATH
from edt_memory import activate_timetable_version


HISTORY_FILTERS = (
    ("Année universitaire", "history_year"),
    ("Période", "history_period"),
    ("Filière", "history_filiere"),
    ("Semestre", "history_semester"),
)


def _filter_history_catalog(memory, selections):
    """Return the catalog rows matching the four visible history filters."""
    filtered = memory.copy()
    for column, _key in HISTORY_FILTERS:
        selected = selections.get(column, "Tous")
        if selected != "Tous":
            filtered = filtered[filtered[column].astype(str) == str(selected)]
    return filtered


def _reset_history_filters(state=None):
    target = st.session_state if state is None else state
    for _column, key in HISTORY_FILTERS:
        target[key] = "Tous"


def _table_exists(conn, name):
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
        (name,),
    ).fetchone()
    return row is not None


def _columns(conn, table):
    if not _table_exists(conn, table):
        return set()
    return {row[1] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()}


def _load_timetables():
    with sqlite3.connect(DB_PATH) as conn:
        if not _table_exists(conn, "edt_timetables"):
            return pd.DataFrame()

        version_cols = _columns(conn, "edt_versions")
        active_expr = (
            "MAX(CASE WHEN v.is_active=1 THEN v.version_number END)"
            if "is_active" in version_cols
            else "MAX(v.version_number)"
        )

        sql = f'''
            SELECT
                t.id,
                t.academic_year AS "Année universitaire",
                t.period AS "Période",
                t.filiere AS "Filière",
                t.niveau AS "Semestre",
                COUNT(v.id) AS "Nombre de versions",
                {active_expr} AS "Version active"
            FROM edt_timetables t
            LEFT JOIN edt_versions v ON v.timetable_id=t.id
            GROUP BY
                t.id, t.academic_year, t.period, t.filiere, t.niveau
            ORDER BY
                t.academic_year DESC,
                t.period,
                t.filiere,
                t.niveau
        '''
        return pd.read_sql_query(sql, conn)


def _load_versions(timetable_id):
    with sqlite3.connect(DB_PATH) as conn:
        if not _table_exists(conn, "edt_versions"):
            return pd.DataFrame()

        cols = _columns(conn, "edt_versions")
        status_expr = "status" if "status" in cols else "'-'"
        active_expr = "is_active" if "is_active" in cols else "0"
        count_expr = "sessions_count" if "sessions_count" in cols else "0"
        source_expr = "source_documents" if "source_documents" in cols else "''"
        comment_expr = "comment" if "comment" in cols else "''"

        sql = f'''
            SELECT
                id,
                version_number,
                imported_at,
                {status_expr} AS status,
                {active_expr} AS is_active,
                {count_expr} AS sessions_count,
                {source_expr} AS source_documents,
                {comment_expr} AS comment
            FROM edt_versions
            WHERE timetable_id=?
            ORDER BY version_number DESC
        '''
        return pd.read_sql_query(sql, conn, params=(int(timetable_id),))


def _load_sessions(version_id):
    with sqlite3.connect(DB_PATH) as conn:
        if not _table_exists(conn, "edt_sessions"):
            return pd.DataFrame()

        return pd.read_sql_query(
            '''
            SELECT
                jour AS "Jour",
                horaire AS "Horaire",
                matiere AS "Matière",
                type_seance AS "Type",
                enseignant AS "Enseignant",
                groupe AS "Groupe",
                salle AS "Salle",
                duree AS "Durée",
                source_document AS "Document source",
                page AS "Page"
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
                    WHEN 'Dimanche' THEN 7
                    ELSE 8
                END,
                horaire,
                matiere,
                enseignant
            ''',
            conn,
            params=(int(version_id),),
        )


def _load_change_summary(version_id):
    with sqlite3.connect(DB_PATH) as conn:
        if not _table_exists(conn, "edt_version_change_summary"):
            return None

        row = conn.execute(
            '''
            SELECT
                from_version_id,
                unchanged_count,
                modified_count,
                added_count,
                removed_count,
                created_at
            FROM edt_version_change_summary
            WHERE to_version_id=?
            ''',
            (int(version_id),),
        ).fetchone()

        if not row:
            return None

        previous_number = None
        if row[0] is not None:
            prev = conn.execute(
                "SELECT version_number FROM edt_versions WHERE id=?",
                (int(row[0]),),
            ).fetchone()
            if prev:
                previous_number = int(prev[0])

        return {
            "previous_version_number": previous_number,
            "unchanged": int(row[1] or 0),
            "modified": int(row[2] or 0),
            "added": int(row[3] or 0),
            "removed": int(row[4] or 0),
            "created_at": row[5],
        }


def _load_changes(version_id):
    with sqlite3.connect(DB_PATH) as conn:
        if not _table_exists(conn, "edt_version_changes"):
            return pd.DataFrame()

        rows = conn.execute(
            '''
            SELECT
                change_type,
                matiere,
                enseignant,
                groupe,
                type_seance,
                changed_fields,
                old_data_json,
                new_data_json
            FROM edt_version_changes
            WHERE to_version_id=?
            ORDER BY
                CASE change_type
                    WHEN 'modified' THEN 1
                    WHEN 'added' THEN 2
                    WHEN 'removed' THEN 3
                    ELSE 4
                END,
                matiere,
                enseignant
            ''',
            (int(version_id),),
        ).fetchall()

    labels = {
        "modified": "🟠 Modifiée",
        "added": "🟢 Ajoutée",
        "removed": "🔴 Supprimée",
    }

    output = []

    for change_type, matiere, enseignant, groupe, type_seance, fields_json, old_json, new_json in rows:
        try:
            fields = json.loads(fields_json or "[]")
        except Exception:
            fields = []

        try:
            old = json.loads(old_json or "{}")
        except Exception:
            old = {}

        try:
            new = json.loads(new_json or "{}")
        except Exception:
            new = {}

        def summary(data):
            if not data:
                return ""
            parts = []
            for key in ["Jour", "Horaire", "Salle", "Nom et prénom"]:
                value = str(data.get(key, "") or "").strip()
                if value:
                    parts.append(value)
            return " | ".join(parts)

        output.append(
            {
                "Changement": labels.get(change_type, change_type),
                "Matière": matiere or "",
                "Enseignant": enseignant or "",
                "Type": type_seance or "",
                "Groupe": groupe or "",
                "Champs modifiés": ", ".join(fields),
                "Avant": summary(old),
                "Après": summary(new),
            }
        )

    return pd.DataFrame(output)


def _format_sources(raw):
    if not raw:
        return ""
    try:
        values = json.loads(raw)
        if isinstance(values, list):
            return ", ".join(str(x) for x in values)
    except Exception:
        pass
    return str(raw)


def _render_change_block(version_id, version_number):
    summary = _load_change_summary(version_id)

    if version_number == 1 and summary is None:
        st.info("V1 est la version initiale : aucune version précédente à comparer.")
        return

    if summary is None:
        st.info("Aucun rapport de changement archivé pour cette version.")
        return

    previous = summary["previous_version_number"]

    if previous is None:
        st.info(f"V{version_number} est enregistrée comme version initiale.")
        return

    st.markdown(f"#### 🔄 Modifications apportées — V{previous} → V{version_number}")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Identiques", summary["unchanged"])
    c2.metric("Modifiées", summary["modified"])
    c3.metric("Ajoutées", summary["added"])
    c4.metric("Supprimées", summary["removed"])

    changes = _load_changes(version_id)

    if changes.empty:
        st.success("Aucun changement détaillé.")
        return

    for label, title in [
        ("🟠 Modifiée", "🟠 Séances modifiées"),
        ("🟢 Ajoutée", "🟢 Séances ajoutées"),
        ("🔴 Supprimée", "🔴 Séances supprimées"),
    ]:
        part = changes[changes["Changement"] == label]
        if not part.empty:
            st.markdown(f"**{title}**")
            st.dataframe(part, use_container_width=True, hide_index=True)


def _render_version(version):
    version_id = int(version["id"])
    version_number = int(version["version_number"])
    is_active = bool(int(version.get("is_active", 0) or 0))

    title = f"📅 Version V{version_number}"
    if is_active:
        title += " — ✅ Active"

    st.markdown(f"### {title}")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Version", f"V{version_number}")
    c2.metric("Statut", str(version.get("status", "-") or "-"))
    c3.metric("Séances", int(version.get("sessions_count", 0) or 0))
    c4.metric("Active", "Oui" if is_active else "Non")

    date_import = str(version.get("imported_at", "") or "")
    source = _format_sources(version.get("source_documents", ""))
    comment = str(version.get("comment", "") or "").strip()

    if date_import:
        st.caption(f"Import : {date_import}")
    if source:
        st.caption(f"Document(s) source : {source}")
    if comment:
        st.info(f"Commentaire : {comment}")

    sessions = _load_sessions(version_id)

    st.markdown("#### Emploi du temps de cette version")
    if sessions.empty:
        st.warning("Aucune séance enregistrée pour cette version.")
    else:
        st.dataframe(sessions, use_container_width=True, hide_index=True)

    _render_change_block(version_id, version_number)


def _render_version_action(timetable_id, version, active_version_number):
    """Render the explicit, contextual activation control for one version."""
    version_id = int(version["id"])
    version_number = int(version["version_number"])
    is_active = bool(int(version.get("is_active", 0) or 0))

    st.markdown("#### Action sur la version sélectionnée")
    state_label = "Active" if is_active else "Archivée"
    st.info(f"V{version_number} sélectionnée — {state_label}")

    flash_key = f"history_version_action_flash_{timetable_id}"
    flash = st.session_state.pop(flash_key, None)
    if flash:
        st.success(flash)

    confirm_key = f"history_confirm_activate_{timetable_id}_{version_id}"
    reset_key = f"history_reset_confirm_activate_{timetable_id}_{version_id}"
    if st.session_state.pop(reset_key, False):
        st.session_state.pop(confirm_key, None)

    if is_active:
        st.caption("Cette version est déjà utilisée comme version active.")
        return

    if active_version_number is not None:
        st.caption(
            f"L’activation de V{version_number} archivera V{active_version_number}. "
            "Les séances des deux versions resteront enregistrées."
        )

    confirmed = st.checkbox(
        f"Je confirme l’activation de V{version_number}.",
        key=confirm_key,
        help="L’ancienne version active sera archivée. Aucune séance ne sera supprimée.",
    )
    if st.button(
        f"Activer V{version_number}",
        key=f"history_activate_version_{timetable_id}_{version_id}",
        disabled=not confirmed,
        type="primary",
    ):
        try:
            result = activate_timetable_version(
                timetable_id,
                version_id,
                db_path=DB_PATH,
            )
        except (ValueError, sqlite3.Error) as exc:
            st.error(f"Activation impossible : {exc}")
            return

        previous = result.get("previous_version_number")
        if result.get("status") == "already_active":
            message = f"V{version_number} était déjà active. Aucune donnée n’a été modifiée."
        elif previous is None or int(previous) == version_number:
            message = f"V{version_number} est maintenant active."
        else:
            message = f"V{version_number} est maintenant active ; V{int(previous)} a été archivée."
        st.session_state[flash_key] = message
        st.session_state[reset_key] = True
        st.rerun()


def render_edt_history():
    st.title("🗂️ Historique des emplois du temps")
    st.caption(
        "Consultez tous les emplois mémorisés, chaque version et les changements "
        "archivés entre deux versions."
    )

    memory = _load_timetables()

    if memory.empty:
        st.info("Aucun emploi du temps mémorisé dans estn.db.")
        return

    total_versions = int(memory["Nombre de versions"].fillna(0).sum())

    with sqlite3.connect(DB_PATH) as conn:
        total_sessions = 0
        total_changes = 0

        if _table_exists(conn, "edt_sessions"):
            total_sessions = int(
                conn.execute("SELECT COUNT(*) FROM edt_sessions").fetchone()[0]
            )

        if _table_exists(conn, "edt_version_changes"):
            total_changes = int(
                conn.execute("SELECT COUNT(*) FROM edt_version_changes").fetchone()[0]
            )

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Emplois", len(memory))
    c2.metric("Versions", total_versions)
    c3.metric("Séances archivées", total_sessions)
    c4.metric("Changements archivés", total_changes)

    st.markdown("### 🔎 Filtres")

    def options(column):
        values = sorted(
            {
                str(x).strip()
                for x in memory[column].fillna("").tolist()
                if str(x).strip()
            }
        )
        return ["Tous"] + values

    first_row = st.columns(2)
    second_row = st.columns(2)
    filter_columns = (*first_row, *second_row)
    selections = {}
    for container, (column, key) in zip(filter_columns, HISTORY_FILTERS):
        selections[column] = container.selectbox(column, options(column), key=key)

    filters_active = any(value != "Tous" for value in selections.values())
    actions, result_status = st.columns([1, 2])
    actions.button(
        "Réinitialiser les filtres",
        key="history_reset_filters",
        disabled=not filters_active,
        on_click=_reset_history_filters,
        use_container_width=True,
    )

    filtered = _filter_history_catalog(memory, selections)
    result_status.caption(f"**{len(filtered)} résultat(s) sur {len(memory)} emploi(s)**")

    title = "### 📚 Emplois correspondant aux filtres" if filters_active else "### 📚 Tous les emplois mémorisés"
    st.markdown(title)

    if filtered.empty:
        st.warning("Aucun emploi ne correspond aux filtres. Élargissez la sélection ou réinitialisez les filtres.")
        return

    st.dataframe(
        filtered.drop(columns=["id"]),
        use_container_width=True,
        hide_index=True,
    )

    labels = {}
    for _, row in filtered.iterrows():
        active = row["Version active"]
        active_text = f"V{int(active)}" if pd.notna(active) else "-"
        label = (
            f'{row["Année universitaire"]} | {row["Période"]} | '
            f'{row["Filière"]} | {row["Semestre"]} | active {active_text}'
        )
        labels[label] = int(row["id"])

    selected_timetable_label = st.selectbox(
        "Choisir un emploi",
        list(labels.keys()),
        key="history_timetable",
    )

    timetable_id = labels[selected_timetable_label]
    versions = _load_versions(timetable_id)

    if versions.empty:
        st.warning("Aucune version enregistrée pour cet emploi.")
        return

    st.markdown("### 🧭 Versions disponibles")
    st.caption("Cliquez sur une version pour afficher son emploi complet et les modifications apportées.")

    version_records = versions.to_dict("records")
    button_columns = st.columns(min(5, max(1, len(version_records))))

    session_key = f"edt_history_selected_version_{timetable_id}"
    if session_key not in st.session_state:
        active_rows = [
            row for row in version_records
            if int(row.get("is_active", 0) or 0) == 1
        ]
        default_row = active_rows[0] if active_rows else version_records[0]
        st.session_state[session_key] = int(default_row["id"])

    for index, version in enumerate(version_records):
        version_number = int(version["version_number"])
        active = int(version.get("is_active", 0) or 0) == 1
        label = f"V{version_number}" + (" ✅" if active else "")

        with button_columns[index % len(button_columns)]:
            if st.button(
                label,
                key=f"history_version_button_{timetable_id}_{version_number}",
                use_container_width=True,
            ):
                st.session_state[session_key] = int(version["id"])

    selected_version_id = int(st.session_state[session_key])

    selected_rows = [
        row for row in version_records
        if int(row["id"]) == selected_version_id
    ]

    if not selected_rows:
        selected_rows = [version_records[0]]
        st.session_state[session_key] = int(selected_rows[0]["id"])

    selected_version = selected_rows[0]
    active_rows = [
        row for row in version_records
        if int(row.get("is_active", 0) or 0) == 1
    ]
    active_version_number = (
        int(active_rows[0]["version_number"]) if active_rows else None
    )

    st.divider()
    _render_version_action(timetable_id, selected_version, active_version_number)
    _render_version(selected_version)

    st.divider()
    show_all = st.checkbox(
        "📚 Afficher toutes les versions de cet emploi",
        value=False,
        key=f"history_show_all_{timetable_id}",
    )

    if show_all:
        st.markdown("## Toutes les versions")
        for version in sorted(
            version_records,
            key=lambda row: int(row["version_number"]),
            reverse=True,
        ):
            number = int(version["version_number"])
            active = int(version.get("is_active", 0) or 0) == 1
            title = f"V{number}" + (" — Active" if active else "")

            with st.expander(title, expanded=False):
                _render_version(version)
