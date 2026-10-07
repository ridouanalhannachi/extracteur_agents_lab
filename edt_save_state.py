"""Read-only comparison of the selected editor content with local versions."""
from pathlib import Path
import sqlite3

import pandas as pd

from edt_memory import DB_PATH, _clean, sessions_hash


def saved_state(details, academic_year, period, filiere, niveau, db_path=DB_PATH):
    """Use persisted session values, never a transient success or cached UI flag."""
    context = tuple(_clean(x) for x in (academic_year, period, filiere, niveau))
    if not all(context):
        return {"status": "incomplete"}
    if details is None or details.empty:
        return {"status": "empty"}
    frame = details.copy()
    frame["Année universitaire"], frame["Filière"], frame["Niveau"] = context[0], context[2], context[3]
    fingerprint = sessions_hash(frame)
    try:
        # mode=ro prevents creating a missing database or changing versions.
        with sqlite3.connect(Path(db_path).resolve().as_uri() + "?mode=ro", uri=True) as conn:
            versions = conn.execute("""
                SELECT v.id, v.version_number, v.is_active FROM edt_versions v
                JOIN edt_timetables t ON t.id=v.timetable_id
                WHERE t.academic_year=? AND t.period=? AND t.filiere=? AND t.niveau=?
                ORDER BY v.version_number DESC
            """, context).fetchall()
            for version_id, number, active in versions:
                stored = pd.read_sql_query("""
                    SELECT jour AS "Jour", matiere AS "Matière", type_seance AS "Type",
                    enseignant AS "Nom et prénom", horaire AS "Horaire", duree AS "Durée",
                    groupe AS "Groupe", salle AS "Salle", filiere AS "Filière",
                    niveau AS "Niveau", academic_year AS "Année universitaire"
                    FROM edt_sessions WHERE version_id=? ORDER BY id
                """, conn, params=(version_id,))
                if sessions_hash(stored) == fingerprint:
                    return {"status": "saved", "version_number": number, "active": bool(active)}
    except (sqlite3.Error, pd.errors.DatabaseError, OSError):
        return {"status": "unknown"}
    return {"status": "unsaved"}


def render_saved_state(target, state, label):
    """Render only the explicitly selected timetable, never claim all are saved."""
    prefix = f"{label} — "
    status = state["status"]
    if status == "saved":
        version = state["version_number"]
        if state["active"]:
            target.success(prefix + f"Séances enregistrées localement : V{version} (active).")
        else:
            target.info(prefix + f"Séances déjà enregistrées : V{version} (archivée, non active).")
    elif status == "unsaved":
        target.warning(prefix + "Modifications / séances non enregistrées pour cet emploi. "
                       "Ouvrez « 3 · Enregistrer / Versions », puis enregistrez la version.")
    elif status == "incomplete":
        target.warning(prefix + "Renseignez année, période, filière et semestre pour vérifier l’enregistrement.")
    elif status == "empty":
        target.info("Aucune séance à enregistrer. Les versions existantes sont conservées.")
    else:
        target.warning(prefix + "État d’enregistrement non vérifiable. Aucun succès confirmé.")
