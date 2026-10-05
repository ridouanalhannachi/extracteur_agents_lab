from __future__ import annotations

import json
import re
import sqlite3
import unicodedata
from datetime import datetime, timezone
from difflib import SequenceMatcher

import pandas as pd

from app_config import DB_PATH

FIELDS = [
    "Jour", "Matière", "Type", "Nom et prénom",
    "Horaire", "Durée", "Groupe", "Salle"
]

LABELS = {
    "Jour": "Jour",
    "Matière": "Matière",
    "Type": "Type",
    "Nom et prénom": "Enseignant",
    "Horaire": "Horaire",
    "Durée": "Durée",
    "Groupe": "Groupe",
    "Salle": "Salle",
}


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


def _ratio(a, b):
    a = _norm(a)
    b = _norm(b)
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a, b).ratio()


def ensure_changes_db(db_path=DB_PATH):
    with sqlite3.connect(db_path) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS edt_version_changes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                from_version_id INTEGER,
                to_version_id INTEGER NOT NULL,
                change_type TEXT NOT NULL,
                changed_fields TEXT,
                old_data_json TEXT,
                new_data_json TEXT,
                created_at TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS edt_version_change_summary (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                from_version_id INTEGER,
                to_version_id INTEGER NOT NULL UNIQUE,
                unchanged_count INTEGER NOT NULL DEFAULT 0,
                modified_count INTEGER NOT NULL DEFAULT 0,
                added_count INTEGER NOT NULL DEFAULT 0,
                removed_count INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL
            )
        """)
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_edt_changes_to_version "
            "ON edt_version_changes(to_version_id)"
        )
        conn.commit()


def _load_sessions(version_id, db_path=DB_PATH):
    with sqlite3.connect(db_path) as conn:
        rows = conn.execute("""
            SELECT jour, matiere, type_seance, enseignant,
                   horaire, duree, groupe, salle
            FROM edt_sessions
            WHERE version_id=?
            ORDER BY id
        """, (int(version_id),)).fetchall()

    return [
        {
            "Jour": _clean(r[0]),
            "Matière": _clean(r[1]),
            "Type": _clean(r[2]),
            "Nom et prénom": _clean(r[3]),
            "Horaire": _clean(r[4]),
            "Durée": _clean(r[5]),
            "Groupe": _clean(r[6]),
            "Salle": _clean(r[7]),
        }
        for r in rows
    ]


def _exact_signature(row):
    return tuple(_norm(row.get(field, "")) for field in FIELDS)


def _match_score(old, new):
    subject = _ratio(old.get("Matière"), new.get("Matière"))
    teacher = _ratio(old.get("Nom et prénom"), new.get("Nom et prénom"))
    same_type = 1.0 if _norm(old.get("Type")) == _norm(new.get("Type")) else 0.0
    same_group = 1.0 if _norm(old.get("Groupe")) == _norm(new.get("Groupe")) else 0.0
    same_day = 1.0 if _norm(old.get("Jour")) == _norm(new.get("Jour")) else 0.0
    same_hour = 1.0 if _norm(old.get("Horaire")) == _norm(new.get("Horaire")) else 0.0

    return (
        subject * 0.42
        + teacher * 0.25
        + same_type * 0.11
        + same_group * 0.08
        + same_day * 0.07
        + same_hour * 0.07
    )


def _changed_fields(old, new):
    return [
        LABELS[field]
        for field in FIELDS
        if _norm(old.get(field, "")) != _norm(new.get(field, ""))
    ]


def detect_changes(from_version_id, to_version_id, db_path=DB_PATH):
    old_rows = _load_sessions(from_version_id, db_path)
    new_rows = _load_sessions(to_version_id, db_path)

    old_used = set()
    new_used = set()
    unchanged = 0

    new_by_sig = {}
    for j, row in enumerate(new_rows):
        new_by_sig.setdefault(_exact_signature(row), []).append(j)

    for i, old in enumerate(old_rows):
        candidates = new_by_sig.get(_exact_signature(old), [])
        j = next((x for x in candidates if x not in new_used), None)
        if j is not None:
            old_used.add(i)
            new_used.add(j)
            unchanged += 1

    remaining_old = [i for i in range(len(old_rows)) if i not in old_used]
    remaining_new = [j for j in range(len(new_rows)) if j not in new_used]

    scored = []
    for i in remaining_old:
        for j in remaining_new:
            score = _match_score(old_rows[i], new_rows[j])
            subject = _ratio(old_rows[i].get("Matière"), new_rows[j].get("Matière"))
            teacher = _ratio(old_rows[i].get("Nom et prénom"), new_rows[j].get("Nom et prénom"))
            if score >= 0.60 and (subject >= 0.70 or teacher >= 0.78):
                scored.append((score, i, j))

    scored.sort(reverse=True)
    paired_old = set()
    paired_new = set()
    changes = []

    for score, i, j in scored:
        if i in paired_old or j in paired_new:
            continue
        old = old_rows[i]
        new = new_rows[j]
        changed = _changed_fields(old, new)
        if not changed:
            continue
        paired_old.add(i)
        paired_new.add(j)
        changes.append({
            "change_type": "modified",
            "changed_fields": changed,
            "old": old,
            "new": new,
        })

    for i in remaining_old:
        if i not in paired_old:
            changes.append({
                "change_type": "removed",
                "changed_fields": [],
                "old": old_rows[i],
                "new": {},
            })

    for j in remaining_new:
        if j not in paired_new:
            changes.append({
                "change_type": "added",
                "changed_fields": [],
                "old": {},
                "new": new_rows[j],
            })

    return {
        "baseline": False,
        "unchanged_count": unchanged,
        "modified_count": sum(x["change_type"] == "modified" for x in changes),
        "added_count": sum(x["change_type"] == "added" for x in changes),
        "removed_count": sum(x["change_type"] == "removed" for x in changes),
        "rows": changes,
    }


def archive_new_version_changes(save_result, db_path=DB_PATH):
    ensure_changes_db(db_path)

    timetable_id = int(save_result["timetable_id"])
    version_id = int(save_result["version_id"])
    version_number = int(save_result["version_number"])

    previous_id = None
    if version_number > 1:
        with sqlite3.connect(db_path) as conn:
            row = conn.execute(
                "SELECT id FROM edt_versions "
                "WHERE timetable_id=? AND version_number < ? "
                "ORDER BY version_number DESC LIMIT 1",
                (timetable_id, version_number),
            ).fetchone()
        if row:
            previous_id = int(row[0])

    if previous_id is None:
        result = {
            "baseline": True,
            "unchanged_count": 0,
            "modified_count": 0,
            "added_count": 0,
            "removed_count": 0,
            "rows": [],
        }
    else:
        result = detect_changes(previous_id, version_id, db_path)

    with sqlite3.connect(db_path) as conn:
        conn.execute("DELETE FROM edt_version_changes WHERE to_version_id=?", (version_id,))
        conn.execute("DELETE FROM edt_version_change_summary WHERE to_version_id=?", (version_id,))

        conn.execute("""
            INSERT INTO edt_version_change_summary (
                from_version_id, to_version_id,
                unchanged_count, modified_count, added_count, removed_count,
                created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            previous_id,
            version_id,
            int(result["unchanged_count"]),
            int(result["modified_count"]),
            int(result["added_count"]),
            int(result["removed_count"]),
            _now(),
        ))

        for item in result["rows"]:
            conn.execute("""
                INSERT INTO edt_version_changes (
                    from_version_id, to_version_id, change_type,
                    changed_fields, old_data_json, new_data_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                previous_id,
                version_id,
                item["change_type"],
                json.dumps(item.get("changed_fields", []), ensure_ascii=False),
                json.dumps(item.get("old", {}), ensure_ascii=False),
                json.dumps(item.get("new", {}), ensure_ascii=False),
                _now(),
            ))

        conn.commit()

    result["from_version_id"] = previous_id
    result["to_version_id"] = version_id
    return result


def changes_dataframe(changes):
    rows = []
    labels = {
        "modified": "🟠 Modifiée",
        "added": "🟢 Ajoutée",
        "removed": "🔴 Supprimée",
    }

    for item in (changes or {}).get("rows", []):
        old = item.get("old") or {}
        new = item.get("new") or {}
        display = new if new else old

        before = " | ".join(
            x for x in [
                _clean(old.get("Jour")),
                _clean(old.get("Horaire")),
                _clean(old.get("Salle")),
                _clean(old.get("Nom et prénom")),
            ] if x
        )
        after = " | ".join(
            x for x in [
                _clean(new.get("Jour")),
                _clean(new.get("Horaire")),
                _clean(new.get("Salle")),
                _clean(new.get("Nom et prénom")),
            ] if x
        )

        rows.append({
            "Changement": labels.get(item["change_type"], item["change_type"]),
            "Matière": _clean(display.get("Matière")),
            "Enseignant": _clean(display.get("Nom et prénom")),
            "Type": _clean(display.get("Type")),
            "Groupe": _clean(display.get("Groupe")),
            "Champs modifiés": ", ".join(item.get("changed_fields", [])),
            "Avant": before,
            "Après": after,
        })

    return pd.DataFrame(rows)
