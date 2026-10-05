import sqlite3
from app_config import DB_PATH

print("Base :", DB_PATH)

with sqlite3.connect(DB_PATH) as conn:
    columns = {
        row[1]
        for row in conn.execute("PRAGMA table_info(edt_versions)").fetchall()
    }

    migrations = {
        "source_documents": "TEXT",
        "source_hash": "TEXT NOT NULL DEFAULT ''",
        "status": "TEXT NOT NULL DEFAULT 'Active'",
        "is_active": "INTEGER NOT NULL DEFAULT 1",
        "comment": "TEXT",
        "sessions_count": "INTEGER NOT NULL DEFAULT 0",
    }

    for column, definition in migrations.items():
        if column not in columns:
            print(f"Ajout colonne : {column}")
            conn.execute(
                f"ALTER TABLE edt_versions ADD COLUMN {column} {definition}"
            )
        else:
            print(f"Déjà présente : {column}")

    conn.commit()

    print("\nStructure finale edt_versions :")
    for row in conn.execute("PRAGMA table_info(edt_versions)"):
        print(row)

print("\n✅ Migration terminée")
