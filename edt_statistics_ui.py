from __future__ import annotations

import sqlite3
from datetime import datetime

import pandas as pd
import streamlit as st

from app_config import DB_PATH
from edt_advanced_statistics_ui import render_advanced_statistics

try:
    import altair as alt
except Exception:
    alt = None


DAY_ORDER = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]

PALETTE = {
    "blue": "#2563EB",
    "green": "#16A34A",
    "orange": "#EA580C",
    "purple": "#7C3AED",
    "red": "#DC2626",
    "teal": "#0F766E",
    "slate": "#475569",
    "amber": "#D97706",
}


def _table_exists(conn, name):
    return conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
        (name,),
    ).fetchone() is not None


def _columns(conn, table):
    if not _table_exists(conn, table):
        return set()
    return {row[1] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()}


def _clean(value):
    if value is None:
        return ""
    try:
        if pd.isna(value):
            return ""
    except Exception:
        pass
    return " ".join(str(value).split()).strip()


def _number(value, default=0):
    try:
        if pd.isna(value):
            return default
        return float(value)
    except Exception:
        return default


def _load_sessions():
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

        sql = f"""
            SELECT
                s.id AS session_id,
                s.version_id,
                v.version_number,
                {active_expr} AS is_active,
                {status_expr} AS version_status,
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
                s.source_document
            FROM edt_sessions s
            JOIN edt_versions v ON v.id = s.version_id
            JOIN edt_timetables t ON t.id = v.timetable_id
        """
        frame = pd.read_sql_query(sql, conn)

    if not frame.empty:
        frame["duree"] = pd.to_numeric(frame["duree"], errors="coerce").fillna(0.0)
        for col in [
            "academic_year", "period", "filiere", "niveau", "jour", "horaire",
            "matiere", "type_seance", "enseignant", "groupe", "salle",
            "source_document", "version_status"
        ]:
            if col in frame.columns:
                frame[col] = frame[col].fillna("").astype(str).str.strip()

    return frame


def _load_versions():
    with sqlite3.connect(DB_PATH) as conn:
        if not (
            _table_exists(conn, "edt_versions")
            and _table_exists(conn, "edt_timetables")
        ):
            return pd.DataFrame()

        cols = _columns(conn, "edt_versions")
        active_expr = "v.is_active" if "is_active" in cols else "0"
        status_expr = "v.status" if "status" in cols else "''"
        count_expr = "v.sessions_count" if "sessions_count" in cols else "0"

        sql = f"""
            SELECT
                v.id AS version_id,
                v.timetable_id,
                v.version_number,
                v.imported_at,
                {active_expr} AS is_active,
                {status_expr} AS status,
                {count_expr} AS sessions_count,
                t.academic_year,
                t.period,
                t.filiere,
                t.niveau
            FROM edt_versions v
            JOIN edt_timetables t ON t.id = v.timetable_id
        """
        return pd.read_sql_query(sql, conn)


def _load_changes():
    with sqlite3.connect(DB_PATH) as conn:
        if not _table_exists(conn, "edt_version_change_summary"):
            return pd.DataFrame()

        return pd.read_sql_query(
            """
            SELECT
                s.to_version_id,
                s.from_version_id,
                s.unchanged_count,
                s.modified_count,
                s.added_count,
                s.removed_count,
                s.created_at,
                v.version_number,
                v.timetable_id,
                t.academic_year,
                t.period,
                t.filiere,
                t.niveau
            FROM edt_version_change_summary s
            JOIN edt_versions v ON v.id=s.to_version_id
            JOIN edt_timetables t ON t.id=v.timetable_id
            ORDER BY s.created_at
            """,
            conn,
        )


def _load_global_counts():
    result = {
        "timetables": 0,
        "versions": 0,
        "sessions": 0,
        "changes": 0,
    }
    with sqlite3.connect(DB_PATH) as conn:
        for key, table in [
            ("timetables", "edt_timetables"),
            ("versions", "edt_versions"),
            ("sessions", "edt_sessions"),
            ("changes", "edt_version_changes"),
        ]:
            if _table_exists(conn, table):
                result[key] = int(conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])
    return result


def _filter_options(frame, column):
    if frame.empty or column not in frame.columns:
        return ["Tous"]
    values = sorted({
        _clean(x)
        for x in frame[column].tolist()
        if _clean(x)
    })
    return ["Tous"] + values


def _apply_filters(frame, filters):
    out = frame.copy()
    for column, value in filters.items():
        if value != "Tous" and column in out.columns:
            out = out[out[column].astype(str) == str(value)]
    return out


def _metric_card(title, value, subtitle, color):
    st.markdown(
        f"""
        <div style="
            border-radius:16px;
            padding:18px 18px 16px 18px;
            background:linear-gradient(135deg,{color} 0%,{color}DD 100%);
            color:white;
            min-height:118px;
            box-shadow:0 4px 16px rgba(15,23,42,.12);
            margin-bottom:8px;">
            <div style="font-size:13px;font-weight:700;opacity:.90;text-transform:uppercase;letter-spacing:.04em;">
                {title}
            </div>
            <div style="font-size:31px;font-weight:800;line-height:1.15;margin-top:8px;">
                {value}
            </div>
            <div style="font-size:12px;opacity:.88;margin-top:7px;">
                {subtitle}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _bar_chart(frame, category, value, title, color, horizontal=False, value_format=".0f"):
    if frame.empty:
        st.info("Pas assez de données pour ce graphique.")
        return

    if alt is None:
        st.bar_chart(frame.set_index(category)[value], width="stretch")
        return

    enc_x = alt.X(f"{value}:Q", title=None, axis=alt.Axis(format=value_format))
    enc_y = alt.Y(
        f"{category}:N",
        title=None,
        sort="-x",
        axis=alt.Axis(labelLimit=220),
    )

    if not horizontal:
        enc_x, enc_y = (
            alt.X(f"{category}:N", title=None, sort="-y", axis=alt.Axis(labelAngle=-25, labelLimit=130)),
            alt.Y(f"{value}:Q", title=None, axis=alt.Axis(format=value_format)),
        )

    chart = (
        alt.Chart(frame)
        .mark_bar(cornerRadiusTopLeft=5, cornerRadiusTopRight=5)
        .encode(
            x=enc_x,
            y=enc_y,
            color=alt.value(color),
            tooltip=[
                alt.Tooltip(f"{category}:N", title=category),
                alt.Tooltip(f"{value}:Q", title=value, format=value_format),
            ],
        )
        .properties(title=title, height=max(280, min(520, 34 * len(frame))))
    )

    st.altair_chart(chart, width="stretch")


def _donut_chart(frame, category, value, title):
    if frame.empty:
        st.info("Pas assez de données pour ce graphique.")
        return

    if alt is None:
        st.dataframe(frame, width="stretch", hide_index=True)
        return

    chart = (
        alt.Chart(frame)
        .mark_arc(innerRadius=65, outerRadius=120)
        .encode(
            theta=alt.Theta(f"{value}:Q"),
            color=alt.Color(
                f"{category}:N",
                legend=alt.Legend(title=None, orient="bottom"),
                scale=alt.Scale(
                    range=[
                        "#2563EB", "#7C3AED", "#16A34A", "#EA580C",
                        "#DC2626", "#0F766E", "#D97706", "#475569"
                    ]
                ),
            ),
            tooltip=[
                alt.Tooltip(f"{category}:N", title=category),
                alt.Tooltip(f"{value}:Q", title=value, format=".0f"),
            ],
        )
        .properties(title=title, height=360)
    )
    st.altair_chart(chart, width="stretch")


def _stacked_change_chart(frame):
    if frame.empty:
        st.info("Aucun historique de changements disponible pour ces filtres.")
        return

    data = frame.copy()
    data["Version"] = data.apply(
        lambda row: f'{row["filiere"]} {row["niveau"]} · V{int(row["version_number"])}',
        axis=1,
    )

    long = data.melt(
        id_vars=["Version"],
        value_vars=["modified_count", "added_count", "removed_count"],
        var_name="Type",
        value_name="Nombre",
    )

    labels = {
        "modified_count": "Modifiées",
        "added_count": "Ajoutées",
        "removed_count": "Supprimées",
    }
    long["Type"] = long["Type"].map(labels)

    if alt is None:
        pivot = long.pivot_table(index="Version", columns="Type", values="Nombre", aggfunc="sum")
        st.bar_chart(pivot, width="stretch")
        return

    chart = (
        alt.Chart(long)
        .mark_bar()
        .encode(
            x=alt.X("Version:N", title=None, sort=None, axis=alt.Axis(labelAngle=-35, labelLimit=130)),
            y=alt.Y("Nombre:Q", title="Nombre de changements"),
            color=alt.Color(
                "Type:N",
                title=None,
                scale=alt.Scale(
                    domain=["Modifiées", "Ajoutées", "Supprimées"],
                    range=["#EA580C", "#16A34A", "#DC2626"],
                ),
            ),
            tooltip=["Version:N", "Type:N", alt.Tooltip("Nombre:Q", format=".0f")],
        )
        .properties(title="Évolution des changements par nouvelle version", height=360)
    )

    st.altair_chart(chart, width="stretch")


def render_edt_statistics():
    st.title("📊 Statistiques des emplois du temps")
    st.caption(
        "Tableau de bord visuel pour comprendre l'activité pédagogique, "
        "les charges, l'occupation des salles et l'évolution des versions."
    )

    sessions_all = _load_sessions()
    versions_all = _load_versions()
    changes_all = _load_changes()
    global_counts = _load_global_counts()

    if sessions_all.empty:
        st.info("Aucune séance mémorisée dans estn.db.")
        return

    st.markdown("### 🎛️ Filtres")

    f1, f2, f3, f4 = st.columns(4)
    selected_year = f1.selectbox(
        "Année universitaire",
        _filter_options(sessions_all, "academic_year"),
        key="stats_year",
    )
    selected_period = f2.selectbox(
        "Période",
        _filter_options(sessions_all, "period"),
        key="stats_period",
    )
    selected_filiere = f3.selectbox(
        "Filière",
        _filter_options(sessions_all, "filiere"),
        key="stats_filiere",
    )
    selected_semester = f4.selectbox(
        "Semestre",
        _filter_options(sessions_all, "niveau"),
        key="stats_semester",
    )

    mode = st.radio(
        "Données analysées",
        ["Versions actives uniquement", "Toutes les versions archivées"],
        horizontal=True,
        key="stats_scope",
    )

    filters = {
        "academic_year": selected_year,
        "period": selected_period,
        "filiere": selected_filiere,
        "niveau": selected_semester,
    }

    sessions = _apply_filters(sessions_all, filters)
    versions = _apply_filters(versions_all, filters)
    changes = _apply_filters(changes_all, filters)

    if mode == "Versions actives uniquement":
        if "is_active" in sessions.columns:
            sessions = sessions[sessions["is_active"].fillna(0).astype(int) == 1]
        if "is_active" in versions.columns:
            versions = versions[versions["is_active"].fillna(0).astype(int) == 1]

    if sessions.empty:
        st.warning("Aucune séance ne correspond aux filtres choisis.")
        return

    total_sessions = len(sessions)
    total_hours = float(sessions["duree"].sum())
    teachers = int(sessions["enseignant"].replace("", pd.NA).dropna().nunique())
    rooms = int(sessions["salle"].replace("", pd.NA).dropna().nunique())
    subjects = int(sessions["matiere"].replace("", pd.NA).dropna().nunique())
    programs = int(
        sessions[["filiere", "niveau"]]
        .drop_duplicates()
        .shape[0]
    )

    st.markdown("### 🧭 Vue générale")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        _metric_card("Séances", f"{total_sessions:,}".replace(",", " "), "dans le périmètre sélectionné", PALETTE["blue"])
    with c2:
        _metric_card("Volume horaire", f"{total_hours:.1f} h", "somme des durées archivées", PALETTE["green"])
    with c3:
        _metric_card("Enseignants", teachers, "enseignants distincts", PALETTE["purple"])
    with c4:
        _metric_card("Salles", rooms, "salles distinctes utilisées", PALETTE["orange"])

    c5, c6, c7, c8 = st.columns(4)
    with c5:
        _metric_card("Matières", subjects, "matières distinctes", PALETTE["teal"])
    with c6:
        _metric_card("Filière / Semestre", programs, "combinaisons actives", PALETTE["slate"])
    with c7:
        _metric_card("Versions", len(versions), "versions dans les filtres", PALETTE["amber"])
    with c8:
        change_total = 0
        if not changes.empty:
            change_total = int(
                changes[["modified_count", "added_count", "removed_count"]]
                .fillna(0)
                .sum()
                .sum()
            )
        _metric_card("Changements", change_total, "modifiées + ajoutées + supprimées", PALETTE["red"])

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📅 Activité",
        "👨‍🏫 Enseignants",
        "🏫 Salles",
        "📚 Matières & types",
        "🔄 Versions & changements",
    ])

    with tab1:
        st.markdown("### Répartition de l'activité")

        left, right = st.columns(2)

        day_stats = (
            sessions.groupby("jour", dropna=False)
            .agg(Séances=("session_id", "count"), Heures=("duree", "sum"))
            .reset_index()
            .rename(columns={"jour": "Jour"})
        )
        day_stats["Jour"] = pd.Categorical(
            day_stats["Jour"],
            categories=DAY_ORDER,
            ordered=True,
        )
        day_stats = day_stats.sort_values("Jour")
        day_stats["Jour"] = day_stats["Jour"].astype(str)

        with left:
            _bar_chart(
                day_stats[day_stats["Jour"] != "nan"],
                "Jour",
                "Séances",
                "Nombre de séances par jour",
                PALETTE["blue"],
            )

        period_stats = (
            sessions.groupby(["filiere", "niveau"], dropna=False)
            .size()
            .reset_index(name="Séances")
        )
        period_stats["Filière / Semestre"] = (
            period_stats["filiere"].astype(str)
            + " "
            + period_stats["niveau"].astype(str)
        )
        period_stats = period_stats.sort_values("Séances", ascending=False).head(15)

        with right:
            _bar_chart(
                period_stats,
                "Filière / Semestre",
                "Séances",
                "Activité par filière / semestre",
                PALETTE["purple"],
                horizontal=True,
            )

        st.markdown("#### Tableau journalier")
        display_day = day_stats.rename(columns={"Séances": "Nb séances"})
        display_day["Heures"] = display_day["Heures"].round(2)
        st.dataframe(display_day, width="stretch", hide_index=True)

    with tab2:
        st.markdown("### Charge des enseignants")

        teacher_stats = (
            sessions[sessions["enseignant"].str.strip() != ""]
            .groupby("enseignant")
            .agg(
                Séances=("session_id", "count"),
                Heures=("duree", "sum"),
                Matières=("matiere", "nunique"),
                Filières=("filiere", "nunique"),
            )
            .reset_index()
            .rename(columns={"enseignant": "Enseignant"})
        )
        teacher_stats["Heures"] = teacher_stats["Heures"].round(2)

        left, right = st.columns(2)
        with left:
            _bar_chart(
                teacher_stats.sort_values("Heures", ascending=False).head(15),
                "Enseignant",
                "Heures",
                "Top 15 — charge horaire",
                PALETTE["green"],
                horizontal=True,
                value_format=".1f",
            )
        with right:
            _bar_chart(
                teacher_stats.sort_values("Séances", ascending=False).head(15),
                "Enseignant",
                "Séances",
                "Top 15 — nombre de séances",
                PALETTE["blue"],
                horizontal=True,
            )

        st.markdown("#### Détail des charges")
        st.dataframe(
            teacher_stats.sort_values(["Heures", "Séances"], ascending=False),
            width="stretch",
            hide_index=True,
        )

    with tab3:
        st.markdown("### Utilisation des salles")

        room_stats = (
            sessions[sessions["salle"].str.strip() != ""]
            .groupby("salle")
            .agg(
                Séances=("session_id", "count"),
                Heures=("duree", "sum"),
                Enseignants=("enseignant", "nunique"),
                Matières=("matiere", "nunique"),
            )
            .reset_index()
            .rename(columns={"salle": "Salle"})
        )
        room_stats["Heures"] = room_stats["Heures"].round(2)

        left, right = st.columns(2)
        with left:
            _bar_chart(
                room_stats.sort_values("Séances", ascending=False).head(15),
                "Salle",
                "Séances",
                "Salles les plus utilisées",
                PALETTE["orange"],
                horizontal=True,
            )
        with right:
            _bar_chart(
                room_stats.sort_values("Heures", ascending=False).head(15),
                "Salle",
                "Heures",
                "Volume horaire par salle",
                PALETTE["teal"],
                horizontal=True,
                value_format=".1f",
            )

        st.markdown("#### Détail des salles")
        st.dataframe(
            room_stats.sort_values(["Séances", "Heures"], ascending=False),
            width="stretch",
            hide_index=True,
        )

    with tab4:
        st.markdown("### Matières et types de séances")

        type_stats = (
            sessions.assign(
                Type=sessions["type_seance"].replace("", "Non précisé")
            )
            .groupby("Type")
            .size()
            .reset_index(name="Séances")
            .sort_values("Séances", ascending=False)
        )

        subject_stats = (
            sessions[sessions["matiere"].str.strip() != ""]
            .groupby("matiere")
            .agg(
                Séances=("session_id", "count"),
                Heures=("duree", "sum"),
                Enseignants=("enseignant", "nunique"),
            )
            .reset_index()
            .rename(columns={"matiere": "Matière"})
        )
        subject_stats["Heures"] = subject_stats["Heures"].round(2)

        left, right = st.columns(2)
        with left:
            _donut_chart(
                type_stats,
                "Type",
                "Séances",
                "Répartition CM / TD / TP",
            )
        with right:
            _bar_chart(
                subject_stats.sort_values("Heures", ascending=False).head(15),
                "Matière",
                "Heures",
                "Top matières par volume horaire",
                PALETTE["purple"],
                horizontal=True,
                value_format=".1f",
            )

        st.markdown("#### Détail des matières")
        st.dataframe(
            subject_stats.sort_values(["Heures", "Séances"], ascending=False),
            width="stretch",
            hide_index=True,
        )

    with tab5:
        st.markdown("### Versions et changements")

        if versions.empty:
            st.info("Aucune version ne correspond aux filtres.")
        else:
            version_by_program = (
                versions.groupby(["filiere", "niveau"])
                .size()
                .reset_index(name="Versions")
            )
            version_by_program["Filière / Semestre"] = (
                version_by_program["filiere"].astype(str)
                + " "
                + version_by_program["niveau"].astype(str)
            )
            version_by_program = version_by_program.sort_values(
                "Versions",
                ascending=False,
            ).head(20)

            left, right = st.columns(2)

            with left:
                _bar_chart(
                    version_by_program,
                    "Filière / Semestre",
                    "Versions",
                    "Nombre de versions par emploi",
                    PALETTE["amber"],
                    horizontal=True,
                )

            with right:
                if changes.empty:
                    st.info("Aucun changement archivé pour ces filtres.")
                else:
                    totals = pd.DataFrame({
                        "Type": ["Modifiées", "Ajoutées", "Supprimées"],
                        "Nombre": [
                            int(changes["modified_count"].fillna(0).sum()),
                            int(changes["added_count"].fillna(0).sum()),
                            int(changes["removed_count"].fillna(0).sum()),
                        ],
                    })
                    _donut_chart(
                        totals,
                        "Type",
                        "Nombre",
                        "Nature des changements archivés",
                    )

            if not changes.empty:
                _stacked_change_chart(changes)

                change_rank = (
                    changes.assign(
                        Changements=(
                            changes["modified_count"].fillna(0)
                            + changes["added_count"].fillna(0)
                            + changes["removed_count"].fillna(0)
                        )
                    )
                    .groupby(["filiere", "niveau"], as_index=False)["Changements"]
                    .sum()
                )
                change_rank["Filière / Semestre"] = (
                    change_rank["filiere"].astype(str)
                    + " "
                    + change_rank["niveau"].astype(str)
                )

                st.markdown("#### Emplois ayant le plus changé")
                st.dataframe(
                    change_rank[
                        ["Filière / Semestre", "Changements"]
                    ].sort_values("Changements", ascending=False),
                    width="stretch",
                    hide_index=True,
                )

    # === v7.7 ADVANCED STATISTICS ===
    st.divider()
    render_advanced_statistics()

    st.divider()
    st.caption(
        "Conseil : utilisez « Versions actives uniquement » pour analyser l'état actuel. "
        "« Toutes les versions archivées » sert à étudier l'historique et l'évolution."
    )

    with st.expander("ℹ️ Totaux complets de la mémoire EDT"):
        st.write(
            {
                "Emplois mémorisés": global_counts["timetables"],
                "Versions archivées": global_counts["versions"],
                "Séances archivées": global_counts["sessions"],
                "Changements détaillés archivés": global_counts["changes"],
            }
        )
