"""Transactional version activation checks using disposable SQLite data."""
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import edt_memory as memory


def _sessions(room, subject="Algorithmique"):
    return pd.DataFrame([{
        "Jour": "Lundi",
        "Matière": subject,
        "Type": "CM",
        "Nom et prénom": "Enseignant Test",
        "Horaire": "08:30-10:30",
        "Durée": 2.0,
        "Groupe": "G1",
        "Salle": room,
        "Filière": "IAID",
        "Niveau": "S1",
        "Année universitaire": "2026-2027",
        "Source PDF": "donnees-fictives.pdf",
        "Page": "1",
    }])


class VersionActivationTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.db = Path(self.directory.name) / "edt.db"
        self.first = memory.save_timetable_version(
            _sessions("A1"), "2026-2027", "Automne", "IAID", "S1",
            comment="Commentaire V1", db_path=self.db,
        )
        self.second = memory.save_timetable_version(
            _sessions("B2"), "2026-2027", "Automne", "IAID", "S1",
            comment="Commentaire V2", db_path=self.db,
        )

    def rows(self, sql, params=()):
        with sqlite3.connect(self.db) as conn:
            return conn.execute(sql, params).fetchall()

    def snapshot(self):
        return (
            self.rows("SELECT * FROM edt_versions ORDER BY id"),
            self.rows("SELECT * FROM edt_sessions ORDER BY id"),
        )

    def test_activation_switches_only_active_version_and_reports_both(self):
        result = memory.activate_timetable_version(
            self.first["timetable_id"], self.first["version_id"], self.db,
        )

        self.assertEqual(result["status"], "activated")
        self.assertEqual(result["version_number"], 1)
        self.assertEqual(result["previous_version_number"], 2)
        self.assertEqual(
            self.rows(
                "SELECT version_number, is_active, status FROM edt_versions "
                "ORDER BY version_number"
            ),
            [(1, 1, "Active"), (2, 0, "Archivée")],
        )
        self.assertIn("V1", result["message"])
        self.assertIn("V2", result["message"])

    def test_reactivating_active_version_is_idempotent(self):
        before = self.snapshot()
        result = memory.activate_timetable_version(
            self.second["timetable_id"], self.second["version_id"], self.db,
        )

        self.assertEqual(result["status"], "already_active")
        self.assertEqual(result["previous_version_number"], 2)
        self.assertEqual(self.snapshot(), before)

    def test_version_from_another_timetable_is_rejected_without_mutation(self):
        other = memory.save_timetable_version(
            _sessions("C3", subject="Réseaux"),
            "2026-2027", "Automne", "Réseaux", "S1",
            db_path=self.db,
        )
        before = self.snapshot()

        with self.assertRaisesRegex(ValueError, "autre emploi du temps"):
            memory.activate_timetable_version(
                self.first["timetable_id"], other["version_id"], self.db,
            )

        self.assertEqual(self.snapshot(), before)

    def test_missing_version_is_rejected_without_mutation(self):
        before = self.snapshot()
        with self.assertRaisesRegex(ValueError, "Version introuvable"):
            memory.activate_timetable_version(
                self.first["timetable_id"], 999_999, self.db,
            )
        self.assertEqual(self.snapshot(), before)

    def test_activation_preserves_sessions_comments_and_custom_statuses(self):
        with sqlite3.connect(self.db) as conn:
            conn.execute(
                "UPDATE edt_versions SET status='Validée' WHERE id=?",
                (self.second["version_id"],),
            )
            conn.execute(
                "UPDATE edt_versions SET status='Révisée' WHERE id=?",
                (self.first["version_id"],),
            )
        sessions_before = self.rows("SELECT * FROM edt_sessions ORDER BY id")
        immutable_before = self.rows(
            "SELECT id, timetable_id, version_number, imported_at, source_documents, "
            "source_hash, comment, sessions_count FROM edt_versions ORDER BY id"
        )

        memory.activate_timetable_version(
            self.first["timetable_id"], self.first["version_id"], self.db,
        )

        self.assertEqual(
            self.rows("SELECT status FROM edt_versions ORDER BY version_number"),
            [("Révisée",), ("Validée",)],
        )
        self.assertEqual(self.rows("SELECT * FROM edt_sessions ORDER BY id"), sessions_before)
        self.assertEqual(
            self.rows(
                "SELECT id, timetable_id, version_number, imported_at, source_documents, "
                "source_hash, comment, sessions_count FROM edt_versions ORDER BY id"
            ),
            immutable_before,
        )


if __name__ == "__main__":
    unittest.main()
