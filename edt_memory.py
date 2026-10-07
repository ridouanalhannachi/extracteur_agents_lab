from __future__ import annotations

import hashlib
import json
import re
import sqlite3
import unicodedata
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd

from app_config import DB_PATH

SESSION_COLUMNS = [
    "Jour", "Matière", "Type", "Nom et prénom", "Horaire", "Durée",
    "Groupe", "Salle", "Filière", "Niveau", "Année universitaire",
    "Source PDF", "Page",
]

HASH_COLUMNS = [
    "Jour", "Matière", "Type", "Nom et prénom", "Horaire", "Durée",
    "Groupe", "Salle", "Filière", "Niveau", "Année universitaire",
]

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
    return re.sub(r"\s+", " ", str(value)).strip()

def _norm(value):
    text = unicodedata.normalize("NFKD", _clean(value))
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()

def infer_period(niveau):
    m = re.search(r"([1-6])", _clean(niveau))
    if not m:
        return ""
    return "Automne" if int(m.group(1)) % 2 == 1 else "Printemps"

def ensure_edt_memory_db(db_path=DB_PATH):
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as conn:
        # Serialize schema upgrades and roll back all additions if one fails.
        conn.execute("BEGIN IMMEDIATE")
        conn.execute('''
            CREATE TABLE IF NOT EXISTS edt_timetables (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                academic_year TEXT NOT NULL,
                period TEXT NOT NULL,
                filiere TEXT NOT NULL,
                niveau TEXT NOT NULL,
                created_at TEXT NOT NULL,
                UNIQUE(academic_year, period, filiere, niveau)
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS edt_versions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timetable_id INTEGER NOT NULL,
                version_number INTEGER NOT NULL,
                imported_at TEXT NOT NULL,
                source_documents TEXT,
                source_hash TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'Active',
                is_active INTEGER NOT NULL DEFAULT 1,
                comment TEXT,
                sessions_count INTEGER NOT NULL DEFAULT 0,
                FOREIGN KEY(timetable_id) REFERENCES edt_timetables(id),
                UNIQUE(timetable_id, version_number)
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS edt_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                version_id INTEGER NOT NULL,
                jour TEXT,
                matiere TEXT,
                type_seance TEXT,
                enseignant TEXT,
                horaire TEXT,
                duree REAL,
                groupe TEXT,
                salle TEXT,
                filiere TEXT,
                niveau TEXT,
                academic_year TEXT,
                source_document TEXT,
                page TEXT,
                FOREIGN KEY(version_id) REFERENCES edt_versions(id)
            )
        ''')
        _migrate_version_columns(conn)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_edt_versions_timetable ON edt_versions(timetable_id, version_number)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_edt_sessions_version ON edt_sessions(version_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_edt_sessions_teacher ON edt_sessions(enseignant)")
        conn.commit()

def _migrate_version_columns(conn):
    """Upgrade legacy EDT versions without deleting sessions or history."""
    columns = {row[1] for row in conn.execute("PRAGMA table_info(edt_versions)")}
    additions = {
        "source_documents": "TEXT",
        "source_hash": "TEXT NOT NULL DEFAULT ''",
        "status": "TEXT NOT NULL DEFAULT 'Archivée'",
        "is_active": "INTEGER NOT NULL DEFAULT 0",
        "comment": "TEXT",
        "sessions_count": "INTEGER NOT NULL DEFAULT 0",
    }
    missing = set(additions) - columns
    for column, definition in additions.items():
        if column in missing:
            conn.execute(f'ALTER TABLE edt_versions ADD COLUMN "{column}" {definition}')

    if "is_active" in missing:
        # Prefer a pre-existing Active status; otherwise use the latest version.
        for (timetable_id,) in conn.execute("SELECT DISTINCT timetable_id FROM edt_versions").fetchall():
            active = None
            if "status" in columns:
                active = conn.execute(
                    "SELECT id FROM edt_versions WHERE timetable_id=? AND status='Active' "
                    "ORDER BY version_number DESC LIMIT 1", (timetable_id,),
                ).fetchone()
            if active is None:
                active = conn.execute(
                    "SELECT id FROM edt_versions WHERE timetable_id=? "
                    "ORDER BY version_number DESC LIMIT 1", (timetable_id,),
                ).fetchone()
            if active:
                conn.execute("UPDATE edt_versions SET is_active=1 WHERE id=?", active)
    if "status" in missing:
        conn.execute(
            "UPDATE edt_versions SET status=CASE WHEN is_active=1 THEN 'Active' ELSE 'Archivée' END"
        )
    if "sessions_count" in missing:
        conn.execute(
            "UPDATE edt_versions SET sessions_count=(SELECT COUNT(*) FROM edt_sessions "
            "WHERE version_id=edt_versions.id)"
        )
    if missing & {"source_hash", "source_documents"}:
        for (version_id,) in conn.execute("SELECT id FROM edt_versions").fetchall():
            frame = pd.read_sql_query('''
                SELECT jour AS "Jour", matiere AS "Matière", type_seance AS "Type",
                       enseignant AS "Nom et prénom", horaire AS "Horaire", duree AS "Durée",
                       groupe AS "Groupe", salle AS "Salle", filiere AS "Filière",
                       niveau AS "Niveau", academic_year AS "Année universitaire",
                       source_document AS "Source PDF"
                FROM edt_sessions WHERE version_id=? ORDER BY id
            ''', conn, params=(version_id,))
            if "source_hash" in missing and not frame.empty:
                conn.execute("UPDATE edt_versions SET source_hash=? WHERE id=?",
                             (sessions_hash(frame), version_id))
            if "source_documents" in missing:
                sources = sorted({_clean(x) for x in frame["Source PDF"] if _clean(x)})
                conn.execute("UPDATE edt_versions SET source_documents=? WHERE id=?",
                             (json.dumps(sources, ensure_ascii=False), version_id))

def _canonical_records(details):
    frame = details.copy()
    for col in HASH_COLUMNS:
        if col not in frame.columns:
            frame[col] = ""
    frame = frame[HASH_COLUMNS].fillna("")
    records = [{col: _clean(row[col]) for col in HASH_COLUMNS} for _, row in frame.iterrows()]
    # SQLite stores durations as REAL: 2, '2' and 2.0 represent one value.
    for record in records:
        try:
            duration = Decimal(record["Durée"])
            if duration.is_finite():
                record["Durée"] = format(duration.normalize(), "f") if duration else "0"
        except InvalidOperation:
            pass
    records.sort(key=lambda r: (
        _norm(r["Jour"]), _norm(r["Horaire"]), _norm(r["Matière"]),
        _norm(r["Nom et prénom"]), _norm(r["Type"]), _norm(r["Groupe"]),
        _norm(r["Salle"])
    ))
    return records

def sessions_hash(details):
    payload = json.dumps(_canonical_records(details), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()

def _get_or_create_timetable(conn, academic_year, period, filiere, niveau):
    row = conn.execute(
        "SELECT id FROM edt_timetables WHERE academic_year=? AND period=? AND filiere=? AND niveau=?",
        (academic_year, period, filiere, niveau),
    ).fetchone()
    if row:
        return int(row[0])
    cur = conn.execute(
        "INSERT INTO edt_timetables (academic_year, period, filiere, niveau, created_at) VALUES (?, ?, ?, ?, ?)",
        (academic_year, period, filiere, niveau, _now()),
    )
    return int(cur.lastrowid)

def save_timetable_version(details, academic_year, period, filiere, niveau,
                           comment="Import automatique à l'upload", db_path=DB_PATH):
    ensure_edt_memory_db(db_path)
    academic_year = _clean(academic_year)
    period = _clean(period)
    filiere = _clean(filiere)
    niveau = _clean(niveau)

    if not academic_year or not period or not filiere or not niveau:
        raise ValueError("Année universitaire, période, filière et semestre sont obligatoires.")
    if details is None or details.empty:
        raise ValueError("Aucune séance à enregistrer.")

    frame = details.copy()
    for col in SESSION_COLUMNS:
        if col not in frame.columns:
            frame[col] = ""
    frame["Filière"] = filiere
    frame["Niveau"] = niveau
    frame["Année universitaire"] = academic_year

    source_hash = sessions_hash(frame)
    sources = sorted({_clean(x) for x in frame["Source PDF"].tolist() if _clean(x)})

    with sqlite3.connect(db_path) as conn:
        timetable_id = _get_or_create_timetable(conn, academic_year, period, filiere, niveau)

        duplicate = conn.execute(
            "SELECT id, version_number FROM edt_versions WHERE timetable_id=? AND source_hash=? "
            "ORDER BY version_number DESC LIMIT 1",
            (timetable_id, source_hash),
        ).fetchone()
        if duplicate is None:
            # Older releases hashed the display format of durations. Compare the
            # stored sessions before creating a new version with a new hash format.
            candidates = conn.execute(
                "SELECT id, version_number FROM edt_versions WHERE timetable_id=? "
                "ORDER BY version_number DESC", (timetable_id,),
            ).fetchall()
            for candidate in candidates:
                stored = pd.read_sql_query('''
                    SELECT jour AS "Jour", matiere AS "Matière", type_seance AS "Type",
                           enseignant AS "Nom et prénom", horaire AS "Horaire", duree AS "Durée",
                           groupe AS "Groupe", salle AS "Salle", filiere AS "Filière",
                           niveau AS "Niveau", academic_year AS "Année universitaire"
                    FROM edt_sessions WHERE version_id=? ORDER BY id
                ''', conn, params=(candidate[0],))
                if sessions_hash(stored) == source_hash:
                    duplicate = candidate
                    conn.execute("UPDATE edt_versions SET source_hash=? WHERE id=?",
                                 (source_hash, candidate[0]))
                    break
        if duplicate:
            return {
                "status": "duplicate",
                "timetable_id": timetable_id,
                "version_id": int(duplicate[0]),
                "version_number": int(duplicate[1]),
                "message": f"Déjà mémorisé : V{int(duplicate[1])}.",
            }

        max_v = conn.execute(
            "SELECT COALESCE(MAX(version_number), 0) FROM edt_versions WHERE timetable_id=?",
            (timetable_id,),
        ).fetchone()[0]
        version_number = int(max_v) + 1

        conn.execute(
            "UPDATE edt_versions "
            "SET is_active=0, status=CASE WHEN status='Active' THEN 'Archivée' ELSE status END "
            "WHERE timetable_id=? AND is_active=1",
            (timetable_id,),
        )

        cur = conn.execute('''
            INSERT INTO edt_versions (
                timetable_id, version_number, imported_at, source_documents,
                source_hash, status, is_active, comment, sessions_count
            ) VALUES (?, ?, ?, ?, ?, 'Active', 1, ?, ?)
        ''', (
            timetable_id, version_number, _now(),
            json.dumps(sources, ensure_ascii=False), source_hash,
            _clean(comment), int(len(frame)),
        ))
        version_id = int(cur.lastrowid)

        for _, row in frame.iterrows():
            try:
                duree_value = float(row.get("Durée")) if _clean(row.get("Durée")) else None
            except Exception:
                duree_value = None
            conn.execute('''
                INSERT INTO edt_sessions (
                    version_id, jour, matiere, type_seance, enseignant,
                    horaire, duree, groupe, salle, filiere, niveau,
                    academic_year, source_document, page
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                version_id,
                _clean(row.get("Jour", "")),
                _clean(row.get("Matière", "")),
                _clean(row.get("Type", "")),
                _clean(row.get("Nom et prénom", "")),
                _clean(row.get("Horaire", "")),
                duree_value,
                _clean(row.get("Groupe", "")),
                _clean(row.get("Salle", "")),
                filiere,
                niveau,
                academic_year,
                _clean(row.get("Source PDF", "")),
                _clean(row.get("Page", "")),
            ))
        conn.commit()

    return {
        "status": "created",
        "timetable_id": timetable_id,
        "version_id": version_id,
        "version_number": version_number,
        "message": f"V{version_number} mémorisée automatiquement.",
    }

def auto_save_uploaded_timetables(sessions, db_path=DB_PATH):
    ensure_edt_memory_db(db_path)
    if sessions is None or sessions.empty:
        return []

    frame = sessions.copy().fillna("")
    for col in SESSION_COLUMNS:
        if col not in frame.columns:
            frame[col] = ""

    results = []
    grouped = frame.groupby(["Année universitaire", "Filière", "Niveau"], dropna=False, sort=True)

    for (academic_year, filiere, niveau), group in grouped:
        academic_year = _clean(academic_year)
        filiere = _clean(filiere)
        niveau = _clean(niveau)
        period = infer_period(niveau)

        missing = []
        if not academic_year:
            missing.append("année universitaire")
        if not filiere:
            missing.append("filière")
        if not niveau:
            missing.append("semestre")
        if not period:
            missing.append("période")

        if missing:
            results.append({
                "status": "skipped",
                "academic_year": academic_year,
                "filiere": filiere,
                "niveau": niveau,
                "period": period,
                "message": "Mémoire automatique suspendue : " + ", ".join(missing) + " manquant(e)(s).",
            })
            continue

        result = save_timetable_version(
            group,
            academic_year=academic_year,
            period=period,
            filiere=filiere,
            niveau=niveau,
            db_path=db_path,
        )
        result.update({
            "academic_year": academic_year,
            "filiere": filiere,
            "niveau": niveau,
            "period": period,
        })
        results.append(result)

    return results

def list_timetables(db_path=DB_PATH):
    ensure_edt_memory_db(db_path)
    with sqlite3.connect(db_path) as conn:
        return pd.read_sql_query('''
            SELECT
                t.id,
                t.academic_year AS "Année universitaire",
                t.period AS "Période",
                t.filiere AS "Filière",
                t.niveau AS "Niveau",
                COUNT(v.id) AS "Nb versions",
                MAX(CASE WHEN v.is_active=1 THEN v.version_number END) AS "Version active"
            FROM edt_timetables t
            LEFT JOIN edt_versions v ON v.timetable_id=t.id
            GROUP BY t.id, t.academic_year, t.period, t.filiere, t.niveau
            ORDER BY t.academic_year DESC, t.period, t.filiere, t.niveau
        ''', conn)

def list_versions(timetable_id, db_path=DB_PATH):
    ensure_edt_memory_db(db_path)
    with sqlite3.connect(db_path) as conn:
        frame = pd.read_sql_query('''
            SELECT
                id,
                version_number AS "Version",
                imported_at AS "Date import",
                status AS "Statut",
                is_active AS "Active",
                sessions_count AS "Séances",
                source_documents AS "Documents",
                comment AS "Commentaire"
            FROM edt_versions
            WHERE timetable_id=?
            ORDER BY version_number DESC
        ''', conn, params=(int(timetable_id),))
    if not frame.empty:
        frame["Version"] = frame["Version"].map(lambda x: f"V{int(x)}")
        frame["Active"] = frame["Active"].map(lambda x: "✅" if int(x) else "")
        def fmt_docs(raw):
            try:
                return ", ".join(json.loads(raw or "[]"))
            except Exception:
                return raw or ""
        frame["Documents"] = frame["Documents"].map(fmt_docs)
    return frame

def get_version_id(timetable_id, version_number, db_path=DB_PATH):
    ensure_edt_memory_db(db_path)
    with sqlite3.connect(db_path) as conn:
        row = conn.execute(
            "SELECT id FROM edt_versions WHERE timetable_id=? AND version_number=?",
            (int(timetable_id), int(version_number)),
        ).fetchone()
    return int(row[0]) if row else None


def activate_timetable_version(timetable_id, version_id, db_path=DB_PATH):
    """Make an existing timetable version active without changing its contents.

    The ownership check and both flag updates share one immediate transaction so
    another writer cannot move the active version between those operations.
    Business-specific statuses are preserved: only the generic ``Active`` and
    ``Archivée`` values follow the active flag.
    """
    ensure_edt_memory_db(db_path)
    try:
        timetable_id = int(timetable_id)
        version_id = int(version_id)
    except (TypeError, ValueError) as exc:
        raise ValueError("L'emploi du temps et la version doivent être identifiés.") from exc

    with sqlite3.connect(db_path) as conn:
        conn.execute("BEGIN IMMEDIATE")
        target = conn.execute(
            "SELECT version_number, is_active FROM edt_versions "
            "WHERE id=? AND timetable_id=?",
            (version_id, timetable_id),
        ).fetchone()
        if target is None:
            raise ValueError(
                "Version introuvable ou rattachée à un autre emploi du temps."
            )

        version_number, is_active = int(target[0]), bool(target[1])
        if is_active:
            return {
                "status": "already_active",
                "timetable_id": timetable_id,
                "version_id": version_id,
                "version_number": version_number,
                "previous_version_id": version_id,
                "previous_version_number": version_number,
                "message": f"V{version_number} est déjà la version active.",
            }

        previous = conn.execute(
            "SELECT id, version_number FROM edt_versions "
            "WHERE timetable_id=? AND is_active=1 "
            "ORDER BY version_number DESC LIMIT 1",
            (timetable_id,),
        ).fetchone()
        conn.execute(
            "UPDATE edt_versions "
            "SET is_active=0, "
            "status=CASE WHEN status='Active' THEN 'Archivée' ELSE status END "
            "WHERE timetable_id=? AND is_active=1",
            (timetable_id,),
        )
        conn.execute(
            "UPDATE edt_versions "
            "SET is_active=1, "
            "status=CASE WHEN status='Archivée' THEN 'Active' ELSE status END "
            "WHERE id=? AND timetable_id=?",
            (version_id, timetable_id),
        )
        conn.commit()

    previous_version_id = int(previous[0]) if previous else None
    previous_version_number = int(previous[1]) if previous else None
    previous_label = (
        f"V{previous_version_number}" if previous_version_number is not None
        else "aucune version"
    )
    return {
        "status": "activated",
        "timetable_id": timetable_id,
        "version_id": version_id,
        "version_number": version_number,
        "previous_version_id": previous_version_id,
        "previous_version_number": previous_version_number,
        "message": (
            f"V{version_number} est maintenant active "
            f"(précédemment : {previous_label})."
        ),
    }

def load_version_sessions(version_id, db_path=DB_PATH):
    ensure_edt_memory_db(db_path)
    with sqlite3.connect(db_path) as conn:
        return pd.read_sql_query('''
            SELECT
                jour AS "Jour",
                matiere AS "Matière",
                type_seance AS "Type",
                enseignant AS "Nom et prénom",
                horaire AS "Horaire",
                duree AS "Durée",
                groupe AS "Groupe",
                salle AS "Salle",
                filiere AS "Filière",
                niveau AS "Niveau",
                academic_year AS "Année universitaire",
                source_document AS "Source PDF",
                page AS "Page"
            FROM edt_sessions
            WHERE version_id=?
            ORDER BY jour, horaire, matiere, enseignant
        ''', conn, params=(int(version_id),))

def save_version(*args, **kwargs):
    return save_timetable_version(*args, **kwargs)


def list_memory(*args, **kwargs):
    return list_timetables(*args, **kwargs)

# === V7.3 CHANGE ARCHIVE ===
from edt_changes import archive_new_version_changes as _archive_new_version_changes

_original_save_timetable_version_v73 = save_timetable_version


def save_timetable_version(*args, **kwargs):
    result = _original_save_timetable_version_v73(*args, **kwargs)

    if isinstance(result, dict) and result.get("status") == "created":
        try:
            db_path = kwargs.get("db_path", args[6] if len(args) > 6 else DB_PATH)
            result["changes"] = _archive_new_version_changes(result, db_path=db_path)
        except Exception as exc:
            result["changes_error"] = str(exc)

    return result
