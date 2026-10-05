from __future__ import annotations

import html
import sqlite3

import pandas as pd
import streamlit as st

from app_config import DB_PATH

try:
    import altair as alt
except Exception:
    alt = None


COLORS = {
    "blue": "#2563EB",
    "green": "#16A34A",
    "orange": "#EA580C",
    "red": "#DC2626",
    "purple": "#7C3AED",
    "teal": "#0F766E",
    "slate": "#475569",
    "amber": "#D97706",
}

DAY_ORDER = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]


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

        frame = pd.read_sql_query(
            f"""
            SELECT
                s.id AS session_id,
                s.version_id,
                v.version_number,
                {active_expr} AS is_active,
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
            JOIN edt_versions v ON v.id=s.version_id
            JOIN edt_timetables t ON t.id=v.timetable_id
            """,
            conn,
        )

    if frame.empty:
        return frame

    frame["duree"] = pd.to_numeric(frame["duree"], errors="coerce").fillna(0.0)

    for col in [
        "academic_year", "period", "filiere", "niveau", "jour", "horaire",
        "matiere", "type_seance", "enseignant", "groupe", "salle",
        "source_document"
    ]:
        frame[col] = frame[col].fillna("").astype(str).str.strip()

    return frame


def _load_changes():
    with sqlite3.connect(DB_PATH) as conn:
        if not (
            _table_exists(conn, "edt_version_change_summary")
            and _table_exists(conn, "edt_versions")
            and _table_exists(conn, "edt_timetables")
        ):
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
            ORDER BY s.created_at, v.version_number
            """,
            conn,
        )


def _apply_shared_filters(frame):
    if frame.empty:
        return frame

    mapping = {
        "academic_year": st.session_state.get("stats_year", "Tous"),
        "period": st.session_state.get("stats_period", "Tous"),
        "filiere": st.session_state.get("stats_filiere", "Tous"),
        "niveau": st.session_state.get("stats_semester", "Tous"),
    }

    out = frame.copy()
    for col, selected in mapping.items():
        if selected and selected != "Tous" and col in out.columns:
            out = out[out[col].astype(str) == str(selected)]

    return out


def _shared_scope_active_only():
    return (
        st.session_state.get("stats_scope", "Versions actives uniquement")
        == "Versions actives uniquement"
    )


def _insight_card(icon, title, value, note, color):
    st.markdown(
        f"""
        <div style="
            border-left:6px solid {color};
            background:rgba(148,163,184,.08);
            border-radius:14px;
            padding:15px 16px;
            min-height:108px;
            margin-bottom:8px;">
          <div style="font-size:13px;font-weight:750;color:{color};">{icon} {html.escape(str(title))}</div>
          <div style="font-size:24px;font-weight:800;margin-top:5px;">{html.escape(str(value))}</div>
          <div style="font-size:12px;opacity:.75;margin-top:5px;">{html.escape(str(note))}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_automatic_insights(sessions, changes):
    st.markdown("#### 💡 Lecture rapide des données")

    cards = []

    if not sessions.empty:
        days = sessions[sessions["jour"].str.strip() != ""].groupby("jour").size()
        if not days.empty:
            day = str(days.idxmax())
            cards.append(("📅", "Jour le plus chargé", day, f"{int(days.max())} séances", COLORS["blue"]))

        teachers = (
            sessions[sessions["enseignant"].str.strip() != ""]
            .groupby("enseignant")["duree"]
            .sum()
        )
        if not teachers.empty:
            teacher = str(teachers.idxmax())
            cards.append(("👨‍🏫", "Charge la plus élevée", teacher, f"{teachers.max():.1f} h", COLORS["purple"]))

        rooms = sessions[sessions["salle"].str.strip() != ""].groupby("salle").size()
        if not rooms.empty:
            room = str(rooms.idxmax())
            cards.append(("🏫", "Salle la plus sollicitée", room, f"{int(rooms.max())} séances", COLORS["orange"]))

    if not changes.empty:
        c = changes.copy()
        c["total_changes"] = (
            c["modified_count"].fillna(0)
            + c["added_count"].fillna(0)
            + c["removed_count"].fillna(0)
        )
        if not c.empty and c["total_changes"].max() > 0:
            row = c.sort_values("total_changes", ascending=False).iloc[0]
            label = f'{row["filiere"]} {row["niveau"]} V{int(row["version_number"])}'
            cards.append(("🔄", "Transition la plus mouvementée", label, f'{int(row["total_changes"])} changements', COLORS["red"]))

    if not cards:
        st.info("Pas encore assez de données pour produire une lecture automatique.")
        return

    cols = st.columns(min(4, len(cards)))
    for idx, card in enumerate(cards[:4]):
        with cols[idx]:
            _insight_card(*card)


def _render_heatmap(sessions):
    data = sessions[
        (sessions["jour"].str.strip() != "")
        & (sessions["horaire"].str.strip() != "")
    ].copy()

    if data.empty:
        st.info("Aucune donnée Jour/Horaire exploitable.")
        return

    heat = (
        data.groupby(["jour", "horaire"])
        .size()
        .reset_index(name="Séances")
    )

    heat["jour"] = pd.Categorical(heat["jour"], categories=DAY_ORDER, ordered=True)
    heat = heat.sort_values(["jour", "horaire"])
    heat["jour"] = heat["jour"].astype(str)

    if alt is None:
        pivot = heat.pivot(index="jour", columns="horaire", values="Séances").fillna(0)
        st.dataframe(pivot, width="stretch")
        return

    chart = (
        alt.Chart(heat)
        .mark_rect(cornerRadius=3)
        .encode(
            x=alt.X("horaire:N", title="Horaire", sort=sorted(heat["horaire"].unique())),
            y=alt.Y("jour:N", title=None, sort=DAY_ORDER),
            color=alt.Color(
                "Séances:Q",
                title="Séances",
                scale=alt.Scale(scheme="blues"),
            ),
            tooltip=[
                alt.Tooltip("jour:N", title="Jour"),
                alt.Tooltip("horaire:N", title="Horaire"),
                alt.Tooltip("Séances:Q", format=".0f"),
            ],
        )
        .properties(
            title="Carte thermique d'occupation — jour × horaire",
            height=300,
        )
    )
    st.altair_chart(chart, width="stretch")

    st.caption(
        "Plus la cellule est intense, plus le créneau contient de séances. "
        "Cette vue aide à repérer rapidement les créneaux très sollicités et les périodes creuses."
    )


def _teacher_load_frame(sessions):
    return (
        sessions[sessions["enseignant"].str.strip() != ""]
        .groupby("enseignant")
        .agg(
            Heures=("duree", "sum"),
            Séances=("session_id", "count"),
            Matières=("matiere", "nunique"),
            Filières=("filiere", "nunique"),
        )
        .reset_index()
        .rename(columns={"enseignant": "Enseignant"})
    )


def _render_distribution_and_outliers(sessions):
    loads = _teacher_load_frame(sessions)

    if len(loads) < 4:
        st.info("Il faut au moins 4 enseignants pour une analyse de distribution utile.")
        return

    q1 = float(loads["Heures"].quantile(0.25))
    median = float(loads["Heures"].median())
    q3 = float(loads["Heures"].quantile(0.75))
    iqr = q3 - q1
    lower = max(0.0, q1 - 1.5 * iqr)
    upper = q3 + 1.5 * iqr

    loads["Atypique"] = (loads["Heures"] < lower) | (loads["Heures"] > upper)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Q1", f"{q1:.1f} h")
    c2.metric("Médiane", f"{median:.1f} h")
    c3.metric("Q3", f"{q3:.1f} h")
    c4.metric("Seuil IQR supérieur", f"{upper:.1f} h")

    if alt is not None:
        box = (
            alt.Chart(loads)
            .mark_boxplot(size=60, extent=1.5)
            .encode(
                y=alt.Y("Heures:Q", title="Charge horaire"),
                color=alt.value(COLORS["purple"]),
                tooltip=[alt.Tooltip("Heures:Q", format=".1f")],
            )
            .properties(title="Distribution de la charge horaire des enseignants", height=330)
        )
        st.altair_chart(box, width="stretch")
    else:
        st.dataframe(loads.sort_values("Heures", ascending=False), width="stretch", hide_index=True)

    atypical = loads[loads["Atypique"]].sort_values("Heures", ascending=False)

    st.markdown("##### Charges statistiquement atypiques selon la règle IQR")
    if atypical.empty:
        st.success("Aucune charge atypique détectée par la règle 1,5 × IQR.")
    else:
        st.dataframe(
            atypical[["Enseignant", "Heures", "Séances", "Matières", "Filières"]],
            width="stretch",
            hide_index=True,
        )
        st.warning(
            "« Atypique » signifie statistiquement éloigné de la distribution observée. "
            "Cela ne signifie pas automatiquement surcharge ou erreur administrative."
        )


def _pareto_data(sessions, dimension):
    label_map = {
        "salle": "Salle",
        "enseignant": "Enseignant",
        "matiere": "Matière",
    }
    clean = sessions[sessions[dimension].str.strip() != ""]
    if clean.empty:
        return pd.DataFrame(), label_map[dimension]

    out = (
        clean.groupby(dimension)
        .size()
        .reset_index(name="Séances")
        .sort_values("Séances", ascending=False)
    )
    out["Part cumulative (%)"] = out["Séances"].cumsum() / out["Séances"].sum() * 100.0
    out = out.rename(columns={dimension: label_map[dimension]})
    return out, label_map[dimension]


def _render_pareto(sessions):
    dimension_label = st.selectbox(
        "Analyser la concentration par",
        ["Salles", "Enseignants", "Matières"],
        key="advanced_pareto_dimension",
    )
    dimension = {
        "Salles": "salle",
        "Enseignants": "enseignant",
        "Matières": "matiere",
    }[dimension_label]

    frame, category = _pareto_data(sessions, dimension)
    if frame.empty:
        st.info("Pas assez de données pour cette analyse.")
        return

    shown = frame.head(20).copy()

    if alt is not None:
        base = alt.Chart(shown).encode(
            x=alt.X(f"{category}:N", sort="-y", title=None, axis=alt.Axis(labelAngle=-35, labelLimit=130))
        )

        bars = base.mark_bar(color=COLORS["blue"]).encode(
            y=alt.Y("Séances:Q", title="Nombre de séances"),
            tooltip=[
                alt.Tooltip(f"{category}:N"),
                alt.Tooltip("Séances:Q", format=".0f"),
                alt.Tooltip("Part cumulative (%):Q", format=".1f"),
            ],
        )

        line = base.mark_line(point=True, color=COLORS["orange"]).encode(
            y=alt.Y(
                "Part cumulative (%):Q",
                title="Part cumulative (%)",
                scale=alt.Scale(domain=[0, 100]),
            ),
            tooltip=[
                alt.Tooltip(f"{category}:N"),
                alt.Tooltip("Part cumulative (%):Q", format=".1f"),
            ],
        )

        chart = alt.layer(bars, line).resolve_scale(y="independent").properties(
            title=f"Analyse de Pareto — {dimension_label.lower()}",
            height=380,
        )
        st.altair_chart(chart, width="stretch")
    else:
        st.dataframe(shown, width="stretch", hide_index=True)

    first_80 = frame[frame["Part cumulative (%)"] <= 80]
    n80 = len(first_80)
    if n80 < len(frame):
        n80 += 1

    st.info(
        f"Environ {n80} {dimension_label.lower()} suffisent pour atteindre ~80 % "
        f"des séances dans le périmètre courant."
    )


def _render_control_chart(changes):
    if len(changes) < 3:
        st.info("Il faut au moins 3 transitions de versions pour une carte de contrôle utile.")
        return

    data = changes.copy()
    data["Total changements"] = (
        data["modified_count"].fillna(0)
        + data["added_count"].fillna(0)
        + data["removed_count"].fillna(0)
    ).astype(float)

    data = data.sort_values(["created_at", "filiere", "niveau", "version_number"]).reset_index(drop=True)
    data["Index"] = range(1, len(data) + 1)
    data["Transition"] = data.apply(
        lambda row: f'{row["filiere"]} {row["niveau"]} · V{int(row["version_number"])}',
        axis=1,
    )

    mean = float(data["Total changements"].mean())
    std = float(data["Total changements"].std(ddof=1)) if len(data) > 1 else 0.0
    ucl = mean + 3 * std
    lcl = max(0.0, mean - 3 * std)

    data["Moyenne"] = mean
    data["UCL"] = ucl
    data["LCL"] = lcl
    data["Signal"] = data["Total changements"] > ucl

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Moyenne", f"{mean:.1f}")
    c2.metric("Écart-type", f"{std:.1f}")
    c3.metric("Limite UCL (3σ)", f"{ucl:.1f}")
    c4.metric("Signaux", int(data["Signal"].sum()))

    if alt is not None:
        line = (
            alt.Chart(data)
            .mark_line(point=True, color=COLORS["blue"])
            .encode(
                x=alt.X("Index:Q", title="Ordre chronologique des versions"),
                y=alt.Y("Total changements:Q", title="Nombre de changements"),
                tooltip=[
                    alt.Tooltip("Transition:N"),
                    alt.Tooltip("Total changements:Q", format=".0f"),
                ],
            )
        )

        mean_rule = alt.Chart(data).mark_rule(
            color=COLORS["green"],
            strokeDash=[6, 4],
        ).encode(y="Moyenne:Q")

        ucl_rule = alt.Chart(data).mark_rule(
            color=COLORS["red"],
            strokeDash=[4, 4],
        ).encode(y="UCL:Q")

        signal_points = (
            alt.Chart(data[data["Signal"]])
            .mark_point(size=130, filled=True, color=COLORS["red"])
            .encode(
                x="Index:Q",
                y="Total changements:Q",
                tooltip=["Transition:N", "Total changements:Q"],
            )
        )

        chart = alt.layer(line, mean_rule, ucl_rule, signal_points).properties(
            title="Carte de contrôle des changements entre versions",
            height=380,
        )
        st.altair_chart(chart, width="stretch")

    signals = data[data["Signal"]]
    if signals.empty:
        st.success("Aucune transition ne dépasse la limite supérieure 3σ.")
    else:
        st.warning(
            "Une transition au-dessus de la limite 3σ est un signal statistique inhabituel "
            "par rapport à l'historique ; elle mérite une vérification."
        )
        st.dataframe(
            signals[["Transition", "Total changements", "created_at"]],
            width="stretch",
            hide_index=True,
        )


def _render_stability(changes):
    if changes.empty:
        st.info("Aucun historique de changements disponible.")
        return

    data = changes.copy()
    data["Changements"] = (
        data["modified_count"].fillna(0)
        + data["added_count"].fillna(0)
        + data["removed_count"].fillna(0)
    )
    data["Base"] = (
        data["unchanged_count"].fillna(0)
        + data["modified_count"].fillna(0)
        + data["added_count"].fillna(0)
        + data["removed_count"].fillna(0)
    )
    data["Taux de changement (%)"] = data.apply(
        lambda row: (100.0 * row["Changements"] / row["Base"]) if row["Base"] else 0.0,
        axis=1,
    )
    data["Stabilité (%)"] = 100.0 - data["Taux de changement (%)"]
    data["Emploi / version"] = data.apply(
        lambda row: f'{row["filiere"]} {row["niveau"]} · V{int(row["version_number"])}',
        axis=1,
    )

    ranked = data.sort_values("Taux de changement (%)", ascending=False).head(20)

    if alt is not None:
        chart = (
            alt.Chart(ranked)
            .mark_bar(color=COLORS["red"])
            .encode(
                y=alt.Y("Emploi / version:N", sort="-x", title=None),
                x=alt.X("Taux de changement (%):Q", title="Taux de changement (%)"),
                tooltip=[
                    "Emploi / version:N",
                    alt.Tooltip("Taux de changement (%):Q", format=".1f"),
                    alt.Tooltip("Stabilité (%):Q", format=".1f"),
                    alt.Tooltip("Changements:Q", format=".0f"),
                ],
            )
            .properties(title="Versions les moins stables", height=max(280, min(520, 30 * len(ranked))))
        )
        st.altair_chart(chart, width="stretch")

    st.dataframe(
        ranked[
            [
                "academic_year", "period", "filiere", "niveau",
                "version_number", "Changements",
                "Taux de changement (%)", "Stabilité (%)"
            ]
        ].rename(
            columns={
                "academic_year": "Année",
                "period": "Période",
                "filiere": "Filière",
                "niveau": "Semestre",
                "version_number": "Version",
            }
        ),
        width="stretch",
        hide_index=True,
    )
    st.caption(
        "Le score de stabilité est un indicateur interne à l'application : "
        "100 − taux de changement entre deux versions."
    )


def _render_data_quality(sessions):
    fields = {
        "jour": "Jour",
        "horaire": "Horaire",
        "matiere": "Matière",
        "enseignant": "Enseignant",
        "salle": "Salle",
        "filiere": "Filière",
        "niveau": "Semestre",
    }

    rows = []
    total = len(sessions)

    for col, label in fields.items():
        missing = int((sessions[col].fillna("").astype(str).str.strip() == "").sum())
        rate = 100.0 * missing / total if total else 0.0
        rows.append({
            "Champ": label,
            "Manquants": missing,
            "Taux manquant (%)": rate,
            "Complétude (%)": 100.0 - rate,
        })

    quality = pd.DataFrame(rows)
    total_missing = int(quality["Manquants"].sum())
    possible = total * len(fields)
    score = 100.0 * (1.0 - total_missing / possible) if possible else 0.0

    c1, c2, c3 = st.columns(3)
    c1.metric("Score de complétude", f"{score:.1f} %")
    c2.metric("Cellules manquantes", total_missing)
    c3.metric("Séances analysées", total)

    if alt is not None:
        chart = (
            alt.Chart(quality)
            .mark_bar(color=COLORS["amber"])
            .encode(
                y=alt.Y("Champ:N", sort="-x", title=None),
                x=alt.X(
                    "Taux manquant (%):Q",
                    title="Taux de valeurs manquantes (%)",
                    scale=alt.Scale(domain=[0, 100]),
                ),
                tooltip=[
                    "Champ:N",
                    alt.Tooltip("Manquants:Q", format=".0f"),
                    alt.Tooltip("Taux manquant (%):Q", format=".1f"),
                ],
            )
            .properties(title="Complétude des champs essentiels", height=300)
        )
        st.altair_chart(chart, width="stretch")

    st.dataframe(
        quality.sort_values("Taux manquant (%)", ascending=False),
        width="stretch",
        hide_index=True,
    )
    st.caption(
        "Cet indicateur mesure uniquement la complétude technique des champs essentiels. "
        "Il ne mesure pas à lui seul la qualité pédagogique d'un emploi du temps."
    )


def render_advanced_statistics():
    sessions = _apply_shared_filters(_load_sessions())
    changes = _apply_shared_filters(_load_changes())

    if sessions.empty:
        return

    if _shared_scope_active_only() and "is_active" in sessions.columns:
        sessions = sessions[sessions["is_active"].fillna(0).astype(int) == 1]

    st.markdown("## 🧠 Analyse statistique avancée")
    st.caption(
        "Techniques inspirées de l'analyse exploratoire, du contrôle statistique, "
        "des tableaux de bord interactifs et de la visualisation d'indicateurs."
    )

    _render_automatic_insights(sessions, changes)

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🔥 Heatmap",
        "📦 Distribution & anomalies",
        "📊 Pareto 80/20",
        "📈 Stabilité & contrôle",
        "✅ Qualité des données",
    ])

    with tab1:
        st.markdown("### Occupation temporelle")
        _render_heatmap(sessions)

    with tab2:
        st.markdown("### Distribution des charges")
        _render_distribution_and_outliers(sessions)

    with tab3:
        st.markdown("### Concentration des ressources")
        _render_pareto(sessions)

    with tab4:
        st.markdown("### Stabilité des versions")
        sub1, sub2 = st.tabs(["Carte de contrôle 3σ", "Indice de stabilité"])
        with sub1:
            _render_control_chart(changes)
        with sub2:
            _render_stability(changes)

    with tab5:
        st.markdown("### Complétude de la base EDT")
        _render_data_quality(sessions)
