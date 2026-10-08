"""Checks for the read-only contextual export of an archived EDT version."""
from __future__ import annotations

import io
from pathlib import Path
import sqlite3
import tempfile
import unittest

import pandas as pd

import edt_memory as memory
from edt_history_ui import _build_version_export


def _sessions(room: str, subject: str) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
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
            }
        ]
    )


class VersionExportTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.db = Path(self.directory.name) / "edt.db"
        self.first = memory.save_timetable_version(
            _sessions("A1", "Algorithmique"),
            "2026-2027",
            "Automne",
            "IAID",
            "S1",
            db_path=self.db,
        )
        self.second = memory.save_timetable_version(
            _sessions("B2", "Bases de données"),
            "2026-2027",
            "Automne",
            "IAID",
            "S1",
            db_path=self.db,
        )

    def _snapshot(self):
        with sqlite3.connect(self.db) as conn:
            return (
                conn.execute("SELECT * FROM edt_versions ORDER BY id").fetchall(),
                conn.execute("SELECT * FROM edt_sessions ORDER BY id").fetchall(),
            )

    def test_each_version_exports_two_sheets_with_its_own_exact_session(self):
        before = self._snapshot()

        _, first_data, first_name = _build_version_export(
            self.first["version_id"], self.db,
        )
        _, second_data, second_name = _build_version_export(
            self.second["version_id"], self.db,
        )
        first_book = pd.ExcelFile(io.BytesIO(first_data))
        second_book = pd.ExcelFile(io.BytesIO(second_data))

        self.assertEqual(first_name, f"EDT_{self.first['timetable_id']}_V1.xlsx")
        self.assertEqual(second_name, f"EDT_{self.second['timetable_id']}_V2.xlsx")
        self.assertEqual(first_book.sheet_names, ["Intervenants", "Séances détaillées"])
        self.assertEqual(second_book.sheet_names, ["Intervenants", "Séances détaillées"])
        first_details = pd.read_excel(first_book, sheet_name="Séances détaillées")
        second_details = pd.read_excel(second_book, sheet_name="Séances détaillées")
        self.assertEqual(first_details.loc[0, "Matière"], "Algorithmique")
        self.assertEqual(first_details.loc[0, "Salle"], "A1")
        self.assertEqual(second_details.loc[0, "Matière"], "Bases de données")
        self.assertEqual(second_details.loc[0, "Salle"], "B2")
        self.assertEqual(self._snapshot(), before)

    def test_filename_comes_from_database_and_missing_id_cannot_be_forged(self):
        before = self._snapshot()
        with sqlite3.connect(self.db) as conn:
            conn.execute(
                "UPDATE edt_versions SET timetable_id=91, version_number=7 WHERE id=?",
                (self.first["version_id"],),
            )
        changed = self._snapshot()

        _, _, export_name = _build_version_export(self.first["version_id"], self.db)
        self.assertEqual(export_name, "EDT_91_V7.xlsx")
        self.assertEqual(self._snapshot(), changed)

        with self.assertRaisesRegex(ValueError, "Version introuvable"):
            _build_version_export(999_999, self.db)
        self.assertEqual(self._snapshot(), changed)
        self.assertNotEqual(before, changed)

    def test_history_ui_exposes_versioned_name_and_zero_session_state(self):
        from streamlit.testing.v1 import AppTest

        with sqlite3.connect(self.db) as conn:
            conn.execute(
                "DELETE FROM edt_sessions WHERE version_id=?",
                (self.second["version_id"],),
            )
            # These archive tables are unrelated to export; omit them so this
            # focused AppTest does not depend on their historical schema.
            conn.execute("DROP TABLE IF EXISTS edt_version_changes")
            conn.execute("DROP TABLE IF EXISTS edt_version_change_summary")
        before = self._snapshot()
        sessions, export_data, export_name = _build_version_export(
            self.second["version_id"], self.db,
        )
        self.assertTrue(sessions.empty)
        self.assertEqual(export_data, b"")
        self.assertEqual(
            export_name,
            f"EDT_{self.second['timetable_id']}_V2.xlsx",
        )
        script = f"""
from pathlib import Path
import edt_history_ui
edt_history_ui.DB_PATH = Path({str(self.db)!r})
edt_history_ui.render_edt_history()
"""
        at = AppTest.from_string(script, default_timeout=20).run()
        self.assertFalse(at.exception)

        # The timetable defaults to its active V2, which has no stored session.
        self.assertTrue(any(
            "Aucune séance à télécharger pour cette version." in item.value
            for item in at.warning
        ))
        # Choose V1 explicitly and verify the contextual filename.
        at.button(
            key=f"history_version_button_{self.first['timetable_id']}_1"
        ).click().run()
        self.assertFalse(at.exception)
        # Streamlit 1.45 AppTest does not expose download_button. The helper
        # assertions above therefore verify its bytes, empty state and filename
        # directly, while AppTest verifies the visible warning and legend.
        self.assertTrue(any(
            "n’active pas la version" in item.value for item in at.caption
        ))
        self.assertEqual(self._snapshot(), before)


if __name__ == "__main__":
    unittest.main()
