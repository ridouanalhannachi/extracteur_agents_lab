import sqlite3
from app_config import DB_PATH

EXPECTED = {
    "from_version_id": "INTEGER",
    "to_version_id": "INTEGER",
    "change_type": "TEXT",
    "matiere": "TEXT",
    "enseignant": "TEXT",
    "groupe": "TEXT",
    "type_seance": "TEXT",
    "changed_fields": "TEXT",
    "old_data_json": "TEXT",
    "new_data_json": "TEXT",
    "created_at": "TEXT",
}

print("Base :", DB_PATH)

with sqlite3.connect(DB_PATH) as conn:
    exists = conn.execute("""
        SELECT 1
        FROM sqlite_master
        WHERE type='table'
          AND name='edt_version_changes'
    """).fetchone()

    if not exists:
        print("Table edt_version_changes absente.")
        raise SystemExit(1)

    current = {
        row[1]
        for row in conn.execute(
            "PRAGMA table_info(edt_version_changes)"
        ).fetchall()
    }

    print("\nColonnes avant migration :")
    for column in sorted(current):
        print(" -", column)

    print("\nMigration :")

    for column, definition in EXPECTED.items():
        if column not in current:
            conn.execute(
                f'ALTER TABLE edt_version_changes '
                f'ADD COLUMN "{column}" {definition}'
            )
            print(" + ajout :", column)
        else:
            print(" = existe :", column)

    conn.commit()

    final_columns = [
        row[1]
        for row in conn.execute(
            "PRAGMA table_info(edt_version_changes)"
        ).fetchall()
    ]

    count = conn.execute(
        "SELECT COUNT(*) FROM edt_version_changes"
    ).fetchone()[0]

print("\nColonnes finales :")
for column in final_columns:
    print(" -", column)

print("\nChangements conservés :", count)
print("✅ Migration terminée sans suppression de données")
