from __future__ import annotations

import html
import json
import math
import sqlite3
from datetime import datetime, timezone

import pandas as pd
import streamlit as st

from app_config import DB_PATH
from edt_memory import save_timetable_version
from edt_persistence_ui import sync_edt_changes


PROGRAM_ORDER = [
    ("IAID", "S1"),
    ("DAWM", "S1"),
    ("ILCS", "S1"),
    ("IDSD", "S1"),
    ("MGPDI", "S1"),
    ("FBTD", "S1"),
    ("WM", "S1"),
    ("MLT", "S1"),
    ("GCCD", "S1"),
    ("GITAM", "S1"),
    ("GEE", "S1"),
    ("RT", "S1"),
    ("IAID", "S3"),
    ("DAWM", "S3"),
    ("ILCS", "S3"),
    ("IDSD", "S3"),
    ("MGPDI", "S3"),
    ("FBTD", "S3"),
    ("WM", "S3"),
    ("MLT", "S3"),
    ("GCCD", "S3"),
    ("GITAM", "S3"),
    ("GEE", "S3"),
    ("RT", "S3"),
]

DAY_ORDER = {
    "Lundi": 1,
    "Mardi": 2,
    "Mercredi": 3,
    "Jeudi": 4,
    "Vendredi": 5,
    "Samedi": 6,
    "Dimanche": 7,
}

STATUS_LABELS = {
    "verified": "✅ Vérifiée",
    "review": "⚠️ À revoir",
    "pending": "⏳ Non vérifiée",
}

CORRECTION_FIELDS = (
    ("jour", "Jour"),
    ("horaire", "Horaire"),
    ("matiere", "Matière"),
    ("enseignant", "Enseignant"),
    ("type_seance", "Type"),
    ("groupe", "Groupe"),
    ("salle", "Salle"),
    ("duree", "Durée"),
)

CORRECTION_COLUMNS = {
    "jour": "Jour",
    "horaire": "Horaire",
    "matiere": "Matière",
    "enseignant": "Nom et prénom",
    "type_seance": "Type",
    "groupe": "Groupe",
    "salle": "Salle",
    "duree": "Durée",
}

CORRECTION_FLASH_KEY = "_verification_correction_flash"


def _now():
    return datetime.now(timezone.utc).isoformat()


def _clean(value):
    if value is None:
        return ""
    try:
        if pd.isna(value):
            return ""
    except Exception:
        pass
    return " ".join(str(value).split()).strip()


def _table_exists(conn, table):
    return conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
        (table,),
    ).fetchone() is not None


def _columns(conn, table):
    if not _table_exists(conn, table):
        return set()
    return {row[1] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()}


def ensure_verification_tables():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS edt_manual_verification (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                version_id INTEGER NOT NULL,
                session_id INTEGER NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                note TEXT,
                verified_at TEXT,
                updated_at TEXT NOT NULL,
                UNIQUE(version_id, session_id)
            )
        """)
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_edt_manual_verification_version "
            "ON edt_manual_verification(version_id)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_edt_manual_verification_status "
            "ON edt_manual_verification(status)"
        )
        conn.commit()


def _academic_years():
    with sqlite3.connect(DB_PATH) as conn:
        if not _table_exists(conn, "edt_timetables"):
            return []
        rows = conn.execute(
            """
            SELECT DISTINCT academic_year
            FROM edt_timetables
            WHERE TRIM(COALESCE(academic_year, '')) <> ''
            ORDER BY academic_year DESC
            """
        ).fetchall()
    return [_clean(row[0]) for row in rows if _clean(row[0])]


def _active_version_for(conn, academic_year, filiere, niveau):
    cols = _columns(conn, "edt_versions")
    active_filter = "AND v.is_active=1" if "is_active" in cols else ""
    row = conn.execute(
        f"""
        SELECT v.id, v.version_number
        FROM edt_versions v
        JOIN edt_timetables t ON t.id=v.timetable_id
        WHERE t.academic_year=?
          AND UPPER(TRIM(t.filiere))=UPPER(TRIM(?))
          AND UPPER(TRIM(t.niveau))=UPPER(TRIM(?))
          {active_filter}
        ORDER BY v.version_number DESC
        LIMIT 1
        """,
        (academic_year, filiere, niveau),
    ).fetchone()
    if row:
        return int(row[0]), int(row[1])

    row = conn.execute(
        """
        SELECT v.id, v.version_number
        FROM edt_versions v
        JOIN edt_timetables t ON t.id=v.timetable_id
        WHERE t.academic_year=?
          AND UPPER(TRIM(t.filiere))=UPPER(TRIM(?))
          AND UPPER(TRIM(t.niveau))=UPPER(TRIM(?))
        ORDER BY v.version_number DESC
        LIMIT 1
        """,
        (academic_year, filiere, niveau),
    ).fetchone()
    return (int(row[0]), int(row[1])) if row else (None, None)


def _load_console(academic_year):
    ensure_verification_tables()
    rows = []

    with sqlite3.connect(DB_PATH) as conn:
        for order_idx, (filiere, niveau) in enumerate(PROGRAM_ORDER):
            version_id, version_number = _active_version_for(
                conn,
                academic_year,
                filiere,
                niveau,
            )
            if version_id is None:
                rows.append({
                    "program_order": order_idx,
                    "filiere": filiere,
                    "niveau": niveau,
                    "missing_timetable": True,
                    "version_id": None,
                    "version_number": None,
                    "session_id": None,
                })
                continue

            sessions = conn.execute(
                """
                SELECT
                    s.id,
                    s.jour,
                    s.horaire,
                    s.matiere,
                    s.type_seance,
                    s.enseignant,
                    s.groupe,
                    s.salle,
                    s.duree,
                    s.source_document,
                    s.page,
                    mv.status,
                    mv.note,
                    mv.verified_at
                FROM edt_sessions s
                LEFT JOIN edt_manual_verification mv
                  ON mv.version_id=?
                 AND mv.session_id=s.id
                WHERE s.version_id=?
                """,
                (version_id, version_id),
            ).fetchall()

            session_rows = []
            for row in sessions:
                session_rows.append({
                    "program_order": order_idx,
                    "filiere": filiere,
                    "niveau": niveau,
                    "missing_timetable": False,
                    "version_id": version_id,
                    "version_number": version_number,
                    "session_id": int(row[0]),
                    "jour": _clean(row[1]),
                    "horaire": _clean(row[2]),
                    "matiere": _clean(row[3]),
                    "type_seance": _clean(row[4]),
                    "enseignant": _clean(row[5]),
                    "groupe": _clean(row[6]),
                    "salle": _clean(row[7]),
                    "duree": _clean(row[8]),
                    "source_document": _clean(row[9]),
                    "page": _clean(row[10]),
                    "verification_status": _clean(row[11]) or "pending",
                    "verification_note": _clean(row[12]),
                    "verified_at": _clean(row[13]),
                })

            session_rows.sort(
                key=lambda item: (
                    DAY_ORDER.get(item["jour"], 99),
                    item["horaire"],
                    item["matiere"],
                    item["enseignant"],
                )
            )
            for session_idx, item in enumerate(session_rows):
                item["session_order"] = session_idx
                rows.append(item)

    return rows


def _save_status(version_id, session_id, status, note=""):
    ensure_verification_tables()
    verified_at = _now() if status == "verified" else None
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            INSERT INTO edt_manual_verification (
                version_id,
                session_id,
                status,
                note,
                verified_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(version_id, session_id)
            DO UPDATE SET
                status=excluded.status,
                note=excluded.note,
                verified_at=excluded.verified_at,
                updated_at=excluded.updated_at
            """,
            (
                int(version_id),
                int(session_id),
                status,
                _clean(note),
                verified_at,
                _now(),
            ),
        )
        conn.commit()

    sync_edt_changes()


def _prepare_corrected_version(version_id, session_id, updates, db_path=None):
    """Build a new version payload while leaving the stored version untouched."""
    db_path = DB_PATH if db_path is None else db_path
    with sqlite3.connect(db_path) as conn:
        context = conn.execute(
            """
            SELECT t.academic_year, t.period, t.filiere, t.niveau
            FROM edt_versions v
            JOIN edt_timetables t ON t.id=v.timetable_id
            WHERE v.id=?
            """,
            (int(version_id),),
        ).fetchone()
        rows = conn.execute(
            """
            SELECT
                s.id,
                s.jour AS "Jour",
                s.matiere AS "Matière",
                s.type_seance AS "Type",
                s.enseignant AS "Nom et prénom",
                s.horaire AS "Horaire",
                s.duree AS "Durée",
                s.groupe AS "Groupe",
                s.salle AS "Salle",
                s.filiere AS "Filière",
                s.niveau AS "Niveau",
                s.academic_year AS "Année universitaire",
                s.source_document AS "Source PDF",
                s.page AS "Page"
            FROM edt_sessions s
            WHERE s.version_id=?
            ORDER BY s.id
            """,
            (int(version_id),),
        ).fetchall()

    if context is None:
        raise ValueError("La version sélectionnée n’existe plus.")
    if not rows:
        raise ValueError("La version sélectionnée ne contient aucune séance.")

    columns = [
        "_session_id", "Jour", "Matière", "Type", "Nom et prénom", "Horaire",
        "Durée", "Groupe", "Salle", "Filière", "Niveau", "Année universitaire",
        "Source PDF", "Page",
    ]
    frame = pd.DataFrame(rows, columns=columns)
    matches = frame.index[frame["_session_id"] == int(session_id)].tolist()
    if len(matches) != 1:
        raise ValueError("La séance ne correspond pas à la version sélectionnée.")

    row_index = matches[0]
    changed_fields = []
    for field, label in CORRECTION_FIELDS:
        column = CORRECTION_COLUMNS[field]
        before = _clean(frame.at[row_index, column])
        after = _clean(updates.get(field, before))
        if field == "duree" and after:
            try:
                duration_value = float(after.replace(",", "."))
            except ValueError as exc:
                raise ValueError("La durée doit être un nombre d’heures valide.") from exc
            if not math.isfinite(duration_value) or duration_value <= 0:
                raise ValueError("La durée doit être un nombre fini strictement positif.")
            after = str(duration_value)
        if after != before:
            frame.at[row_index, column] = after
            changed_fields.append({"field": field, "label": label, "before": before, "after": after})

    academic_year, period, filiere, niveau = map(_clean, context)
    return {
        "details": frame.drop(columns=["_session_id"]),
        "academic_year": academic_year,
        "period": period,
        "filiere": filiere,
        "niveau": niveau,
        "changed_fields": changed_fields,
    }


def _save_session_correction(
    version_id,
    session_id,
    updates,
    db_path=None,
    sync_func=None,
):
    """Persist an explicit correction as a new version, never in place."""
    db_path = DB_PATH if db_path is None else db_path
    sync_func = sync_edt_changes if sync_func is None else sync_func
    prepared = _prepare_corrected_version(version_id, session_id, updates, db_path)
    if not prepared["changed_fields"]:
        return {"status": "no_changes", "changed_fields": []}

    result = save_timetable_version(
        prepared["details"],
        prepared["academic_year"],
        prepared["period"],
        prepared["filiere"],
        prepared["niveau"],
        "Correction depuis la vérification globale",
        db_path=db_path,
        expected_active_version_id=int(version_id),
    )
    result["changed_fields"] = prepared["changed_fields"]
    if result.get("status") == "created":
        sync_ok, sync_message = sync_func()
        result["sync_ok"] = bool(sync_ok)
        result["sync_message"] = str(sync_message)
    return result


def _correction_prefix(version_id, session_id):
    return f"verification_correction_{int(version_id)}_{int(session_id)}"


def _clear_correction_state(prefix):
    for key in list(st.session_state):
        if key.startswith(prefix):
            st.session_state.pop(key, None)


def _render_session_correction(current):
    prefix = _correction_prefix(current["version_id"], current["session_id"])
    open_key = f"{prefix}_open"
    prepared_key = f"{prefix}_prepared"

    if not st.session_state.get(open_key):
        if st.button(
            "✏️ Corriger cette séance",
            key=f"{prefix}_start",
            width="stretch",
            help="Prépare une nouvelle version sans modifier la version affichée.",
        ):
            st.session_state[open_key] = True
            st.rerun()
        return

    st.markdown("### ✏️ Correction ciblée")
    st.caption(
        "Préparez la correction, contrôlez les changements, puis confirmez la création "
        "d’une nouvelle version. La version actuelle reste intacte."
    )

    with st.form(f"{prefix}_form"):
        first = st.columns(2)
        jour = first[0].text_input("Jour", value=current["jour"], key=f"{prefix}_jour")
        horaire = first[1].text_input("Horaire", value=current["horaire"], key=f"{prefix}_horaire")
        matiere = st.text_input("Matière", value=current["matiere"], key=f"{prefix}_matiere")
        enseignant = st.text_input(
            "Enseignant", value=current["enseignant"], key=f"{prefix}_enseignant"
        )
        second = st.columns(2)
        type_seance = second[0].text_input(
            "Type", value=current["type_seance"], key=f"{prefix}_type_seance"
        )
        groupe = second[1].text_input("Groupe", value=current["groupe"], key=f"{prefix}_groupe")
        third = st.columns(2)
        salle = third[0].text_input("Salle", value=current["salle"], key=f"{prefix}_salle")
        duree = third[1].text_input("Durée", value=current["duree"], key=f"{prefix}_duree")
        prepared = st.form_submit_button(
            "Préparer la correction",
            type="primary",
            use_container_width=True,
        )

    updates = {
        "jour": jour,
        "horaire": horaire,
        "matiere": matiere,
        "enseignant": enseignant,
        "type_seance": type_seance,
        "groupe": groupe,
        "salle": salle,
        "duree": duree,
    }
    if prepared:
        changes = []
        for field, label in CORRECTION_FIELDS:
            before = _clean(current.get(field))
            after = _clean(updates[field])
            if before != after:
                changes.append({"field": field, "label": label, "before": before, "after": after})
        if changes:
            st.session_state[prepared_key] = updates
        else:
            st.session_state.pop(prepared_key, None)
            st.info("Aucune différence à enregistrer pour cette séance.")

    pending = st.session_state.get(prepared_key)
    if pending:
        st.warning("Correction préparée — non enregistrée.")
        for field, label in CORRECTION_FIELDS:
            before = _clean(current.get(field))
            after = _clean(pending.get(field))
            if before != after:
                st.markdown(f"- **{label}** : {before or '—'} → {after or '—'}")

        confirm_key = f"{prefix}_confirm"
        confirmed = st.checkbox(
            "Je confirme la création d’une nouvelle version avec cette correction",
            key=confirm_key,
        )
        action_columns = st.columns(2)
        if action_columns[0].button(
            "Annuler la correction",
            key=f"{prefix}_cancel",
            use_container_width=True,
        ):
            _clear_correction_state(prefix)
            st.session_state[CORRECTION_FLASH_KEY] = {
                "kind": "info",
                "message": "Correction annulée. Aucune version n’a été créée.",
            }
            st.rerun()
        if action_columns[1].button(
            "💾 Enregistrer comme nouvelle version",
            key=f"{prefix}_save",
            type="primary",
            disabled=not confirmed,
            use_container_width=True,
        ):
            try:
                result = _save_session_correction(
                    current["version_id"], current["session_id"], pending
                )
                if result["status"] == "created":
                    message = (
                        f"Version V{result['version_number']} enregistrée localement et activée. "
                        "La vérification de cette nouvelle version repart sans statut hérité."
                    )
                    kind = "success" if result.get("sync_ok") else "warning"
                    if not result.get("sync_ok"):
                        message += " Synchronisation non confirmée : " + result.get("sync_message", "")
                elif result["status"] == "duplicate":
                    kind = "info"
                    message = (
                        f"Cette correction existe déjà dans V{result['version_number']} ; "
                        "aucune version supplémentaire n’a été créée."
                    )
                else:
                    kind = "info"
                    message = "Aucune différence à enregistrer."
                _clear_correction_state(prefix)
                st.session_state[CORRECTION_FLASH_KEY] = {"kind": kind, "message": message}
                st.rerun()
            except Exception as exc:
                st.error(f"Correction non enregistrée : {exc}")


def _reset_year(academic_year):
    rows = _load_console(academic_year)
    version_ids = sorted({
        int(row["version_id"])
        for row in rows
        if row.get("version_id") is not None
    })
    if not version_ids:
        return
    placeholders = ",".join("?" for _ in version_ids)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            f"DELETE FROM edt_manual_verification WHERE version_id IN ({placeholders})",
            version_ids,
        )
        conn.commit()
    sync_edt_changes()


def _status_color(status):
    return {
        "verified": "#16A34A",
        "review": "#EA580C",
        "pending": "#64748B",
    }.get(status, "#64748B")


def _field_card(label, value, color, large=False):
    safe_label = html.escape(label)
    safe_value = html.escape(value or "—")
    size = "23px" if large else "17px"
    return f"""
        <div style="
            border-radius:14px;
            border:1px solid {color}44;
            border-left:6px solid {color};
            background:{color}0D;
            padding:12px 14px;
            min-height:82px;">
            <div style="font-size:11px;font-weight:800;color:{color};
                        text-transform:uppercase;letter-spacing:.04em;">
                {safe_label}
            </div>
            <div style="font-size:{size};font-weight:800;margin-top:7px;
                        overflow-wrap:anywhere;">
                {safe_value}
            </div>
        </div>
    """


def _program_progress(rows, filiere, niveau):
    items = [
        row for row in rows
        if row.get("filiere") == filiere
        and row.get("niveau") == niveau
        and row.get("session_id") is not None
    ]
    if not items:
        return 0, 0, 0
    verified = sum(1 for row in items if row.get("verification_status") == "verified")
    review = sum(1 for row in items if row.get("verification_status") == "review")
    return verified, review, len(items)


def _global_progress(rows):
    sessions = [row for row in rows if row.get("session_id") is not None]
    total = len(sessions)
    verified = sum(1 for row in sessions if row.get("verification_status") == "verified")
    review = sum(1 for row in sessions if row.get("verification_status") == "review")
    pending = max(0, total - verified - review)
    return verified, review, pending, total


def _ordered_sessions(rows):
    return [row for row in rows if row.get("session_id") is not None]


def _current_index_key(year):
    return f"verification_console_index_{year}"


def _note_key(year, session_id):
    return f"verification_note_{year}_{session_id}"


def _move_next(year, total):
    key = _current_index_key(year)
    st.session_state[key] = min(st.session_state.get(key, 0) + 1, max(0, total - 1))


def _move_previous(year):
    key = _current_index_key(year)
    st.session_state[key] = max(st.session_state.get(key, 0) - 1, 0)


def _jump_to_program(year, sessions, filiere, niveau):
    for idx, item in enumerate(sessions):
        if item["filiere"] == filiere and item["niveau"] == niveau:
            st.session_state[_current_index_key(year)] = idx
            return


def _render_program_overview(rows, year):
    st.markdown("### 📚 Ordre global de vérification")
    st.caption(
        "L'ordre suit exactement : IAID → DAWM → ILCS → IDSD → MGPDI → FBTD → "
        "WM → MLT → GCCD → GITAM → GEE → RT, d'abord S1 puis S3."
    )

    for start in range(0, len(PROGRAM_ORDER), 4):
        cols = st.columns(4)
        for offset, (filiere, niveau) in enumerate(PROGRAM_ORDER[start:start + 4]):
            with cols[offset]:
                verified, review, total = _program_progress(rows, filiere, niveau)
                missing = any(
                    row.get("filiere") == filiere
                    and row.get("niveau") == niveau
                    and row.get("missing_timetable")
                    for row in rows
                )

                if missing and total == 0:
                    st.markdown(
                        f"""
                        <div style="border:1px solid #DC262655;border-radius:12px;padding:10px;
                                    border-left:5px solid #DC2626;min-height:94px;">
                            <b>❌ {filiere} - {niveau}</b><br>
                            <span style="font-size:12px;">Emploi actif introuvable</span>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                else:
                    done = verified == total and total > 0
                    icon = "✅" if done else ("⚠️" if review else "⏳")
                    color = "#16A34A" if done else ("#EA580C" if review else "#2563EB")
                    st.markdown(
                        f"""
                        <div style="border:1px solid {color}44;border-radius:12px;padding:10px;
                                    border-left:5px solid {color};min-height:94px;">
                            <b>{icon} {filiere} - {niveau}</b><br>
                            <span style="font-size:12px;">
                                {verified}/{total} vérifiées · {review} à revoir
                            </span>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                    if st.button(
                        f"Ouvrir {filiere} {niveau}",
                        key=f"verify_jump_{year}_{filiere}_{niveau}",
                        width="stretch",
                    ):
                        sessions = _ordered_sessions(rows)
                        _jump_to_program(year, sessions, filiere, niveau)
                        st.rerun()


def render_global_verification():
    ensure_verification_tables()

    st.title("✅ Vérification globale des emplois")
    st.caption(
        "Console de vérification manuelle séance par séance. "
        "Chaque validation est mémorisée dans estn.db."
    )

    years = _academic_years()
    if not years:
        st.info("Aucune année universitaire mémorisée.")
        return

    selected_year = st.selectbox(
        "Année universitaire",
        years,
        key="verification_academic_year",
    )

    rows = _load_console(selected_year)
    sessions = _ordered_sessions(rows)

    correction_flash = st.session_state.pop(CORRECTION_FLASH_KEY, None)
    if correction_flash:
        renderer = getattr(st, correction_flash.get("kind", "info"), st.info)
        renderer(correction_flash.get("message", ""))

    if not sessions:
        st.warning("Aucune séance disponible pour l'année sélectionnée.")
        _render_program_overview(rows, selected_year)
        return

    verified, review, pending, total = _global_progress(rows)

    st.markdown("### 📊 Progression globale")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total séances", total)
    c2.metric("✅ Vérifiées", verified)
    c3.metric("⚠️ À revoir", review)
    c4.metric("⏳ Restantes", pending)

    progress = verified / total if total else 0.0
    st.progress(progress, text=f"{verified}/{total} séances vérifiées — {progress * 100:.1f} %")

    with st.expander("📚 Voir l'ordre et l'avancement de tous les emplois", expanded=False):
        _render_program_overview(rows, selected_year)

    key = _current_index_key(selected_year)
    if key not in st.session_state:
        first_pending = next(
            (
                idx for idx, item in enumerate(sessions)
                if item.get("verification_status") != "verified"
            ),
            0,
        )
        st.session_state[key] = first_pending

    index = int(st.session_state[key])
    index = max(0, min(index, len(sessions) - 1))
    st.session_state[key] = index
    current = sessions[index]

    filiere = current["filiere"]
    niveau = current["niveau"]
    version = current["version_number"]
    status = current.get("verification_status", "pending")
    status_label = STATUS_LABELS.get(status, status)
    status_color = _status_color(status)

    program_sessions = [
        item for item in sessions
        if item["filiere"] == filiere and item["niveau"] == niveau
    ]
    local_position = next(
        (
            i + 1 for i, item in enumerate(program_sessions)
            if item["session_id"] == current["session_id"]
        ),
        1,
    )

    st.divider()
    st.markdown(
        f"""
        <div style="
            border-radius:18px;
            padding:17px 20px;
            background:linear-gradient(135deg,#0F172A 0%,#1E293B 100%);
            color:white;
            margin-bottom:14px;">
            <div style="font-size:13px;opacity:.75;">EMPLOI EN COURS</div>
            <div style="font-size:28px;font-weight:850;margin-top:3px;">
                {html.escape(filiere)} — {html.escape(niveau)} · V{int(version)}
            </div>
            <div style="font-size:13px;margin-top:7px;opacity:.82;">
                Séance {local_position}/{len(program_sessions)}
                · Global {index + 1}/{len(sessions)}
                · <span style="color:{status_color};font-weight:800;">{status_label}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("### 🖥️ Console séance")

    row1 = st.columns(3)
    with row1[0]:
        st.markdown(_field_card("Jour", current["jour"], "#2563EB", True), unsafe_allow_html=True)
    with row1[1]:
        st.markdown(_field_card("Horaire", current["horaire"], "#7C3AED", True), unsafe_allow_html=True)
    with row1[2]:
        st.markdown(_field_card("Salle", current["salle"], "#EA580C", True), unsafe_allow_html=True)

    row2 = st.columns(2)
    with row2[0]:
        st.markdown(_field_card("Matière", current["matiere"], "#0F766E", True), unsafe_allow_html=True)
    with row2[1]:
        st.markdown(_field_card("Enseignant", current["enseignant"], "#DC2626", True), unsafe_allow_html=True)

    row3 = st.columns(4)
    with row3[0]:
        st.markdown(_field_card("Type", current["type_seance"], "#D97706"), unsafe_allow_html=True)
    with row3[1]:
        st.markdown(_field_card("Groupe", current["groupe"], "#475569"), unsafe_allow_html=True)
    with row3[2]:
        st.markdown(_field_card("Durée", current["duree"], "#16A34A"), unsafe_allow_html=True)
    with row3[3]:
        source = current["source_document"]
        if current.get("page"):
            source = f'{source} · p.{current["page"]}'
        st.markdown(_field_card("Source", source, "#64748B"), unsafe_allow_html=True)

    missing_fields = []
    for field, label in [
        ("jour", "Jour"),
        ("horaire", "Horaire"),
        ("matiere", "Matière"),
        ("enseignant", "Enseignant"),
        ("salle", "Salle"),
    ]:
        if not _clean(current.get(field)):
            missing_fields.append(label)

    if missing_fields:
        st.error("⚠️ Champs essentiels manquants : " + ", ".join(missing_fields))

    _render_session_correction(current)

    note_key = _note_key(selected_year, current["session_id"])
    if note_key not in st.session_state:
        st.session_state[note_key] = current.get("verification_note", "")

    note = st.text_area(
        "Note de vérification (optionnelle)",
        key=note_key,
        placeholder="Ex. vérifier la salle, enseignant incorrect, horaire à confirmer...",
        height=80,
    )

    st.markdown("### 🎮 Navigation / décision")
    b1, b2, b3, b4 = st.columns([1, 1.25, 1.25, 1])

    with b1:
        if st.button(
            "⬅️ Précédente",
            disabled=index == 0,
            width="stretch",
            key=f"verify_prev_{current['session_id']}",
        ):
            _move_previous(selected_year)
            st.rerun()

    with b2:
        if st.button(
            "✅ Vérifier & suivante",
            type="primary",
            width="stretch",
            key=f"verify_ok_{current['session_id']}",
        ):
            _save_status(
                current["version_id"],
                current["session_id"],
                "verified",
                note,
            )
            _move_next(selected_year, len(sessions))
            st.rerun()

    with b3:
        if st.button(
            "⚠️ À revoir & suivante",
            width="stretch",
            key=f"verify_review_{current['session_id']}",
        ):
            _save_status(
                current["version_id"],
                current["session_id"],
                "review",
                note,
            )
            _move_next(selected_year, len(sessions))
            st.rerun()

    with b4:
        if st.button(
            "Suivante ➡️",
            disabled=index >= len(sessions) - 1,
            width="stretch",
            key=f"verify_next_{current['session_id']}",
        ):
            _move_next(selected_year, len(sessions))
            st.rerun()

    nav1, nav2 = st.columns(2)

    with nav1:
        jump = st.number_input(
            "Aller à la séance globale n°",
            min_value=1,
            max_value=len(sessions),
            value=index + 1,
            step=1,
            key=f"verification_jump_number_{selected_year}",
        )
        if st.button(
            "Aller",
            width="stretch",
            key=f"verification_jump_button_{selected_year}",
        ):
            st.session_state[key] = int(jump) - 1
            st.rerun()

    with nav2:
        if st.button(
            "🎯 Aller à la prochaine séance non vérifiée",
            width="stretch",
            key=f"verification_next_pending_{selected_year}",
        ):
            next_idx = next(
                (
                    idx for idx in range(index + 1, len(sessions))
                    if sessions[idx].get("verification_status") != "verified"
                ),
                None,
            )
            if next_idx is None:
                next_idx = next(
                    (
                        idx for idx, item in enumerate(sessions)
                        if item.get("verification_status") != "verified"
                    ),
                    index,
                )
            st.session_state[key] = next_idx
            st.rerun()

    st.divider()
    with st.expander("⚠️ Séances marquées « À revoir »", expanded=False):
        review_rows = [
            row for row in sessions
            if row.get("verification_status") == "review"
        ]
        if not review_rows:
            st.success("Aucune séance marquée à revoir.")
        else:
            review_df = pd.DataFrame([
                {
                    "Filière": row["filiere"],
                    "Semestre": row["niveau"],
                    "Version": f'V{row["version_number"]}',
                    "Jour": row["jour"],
                    "Horaire": row["horaire"],
                    "Matière": row["matiere"],
                    "Enseignant": row["enseignant"],
                    "Salle": row["salle"],
                    "Note": row.get("verification_note", ""),
                }
                for row in review_rows
            ])
            st.dataframe(review_df, width="stretch", hide_index=True)

    with st.expander("🛠️ Outils de vérification", expanded=False):
        st.warning(
            "La réinitialisation supprime uniquement les statuts de vérification manuelle "
            "de l'année sélectionnée. Les emplois et leurs versions ne sont pas supprimés."
        )
        confirm = st.checkbox(
            "Je confirme la réinitialisation de la progression",
            key=f"verification_reset_confirm_{selected_year}",
        )
        if st.button(
            "♻️ Réinitialiser la progression de cette année",
            disabled=not confirm,
            key=f"verification_reset_{selected_year}",
        ):
            _reset_year(selected_year)
            st.session_state[key] = 0
            st.rerun()

    if verified == total and total > 0:
        st.balloons()
        st.success(
            f"🎉 Vérification globale terminée : {verified}/{total} séances vérifiées."
        )
