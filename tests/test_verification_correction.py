"""Safe, versioned correction from the global verification console."""
import sqlite3
import importlib
import tempfile
from pathlib import Path
import textwrap
import unittest

import pandas as pd

import edt_memory as memory


class VerificationCorrectionTests(unittest.TestCase):
    def setUp(self):
        self.verification = importlib.import_module("edt_verification_ui")
        self.directory = tempfile.TemporaryDirectory()
        self.db = Path(self.directory.name) / "fictional.db"
        self.frame = pd.DataFrame([
            {
                "Jour": "Lundi", "Matière": "Réseaux", "Type": "CM",
                "Nom et prénom": "Enseignant Test", "Horaire": "08:30-10:30",
                "Durée": 2.0, "Groupe": "G1", "Salle": "A1", "Filière": "IAID",
                "Niveau": "S1", "Année universitaire": "2026-2027",
                "Source PDF": "fictif.pdf", "Page": "1",
            },
            {
                "Jour": "Mardi", "Matière": "Bases de données", "Type": "TD",
                "Nom et prénom": "Enseignant Démo", "Horaire": "10:30-12:30",
                "Durée": 2.0, "Groupe": "G2", "Salle": "B2", "Filière": "IAID",
                "Niveau": "S1", "Année universitaire": "2026-2027",
                "Source PDF": "fictif.pdf", "Page": "2",
            },
        ])
        self.first = memory.save_timetable_version(
            self.frame, "2026-2027", "Automne", "IAID", "S1", "Initiale",
            db_path=self.db,
        )
        with sqlite3.connect(self.db) as connection:
            self.session_ids = [
                row[0] for row in connection.execute(
                    "SELECT id FROM edt_sessions WHERE version_id=? ORDER BY id",
                    (self.first["version_id"],),
                ).fetchall()
            ]

    def tearDown(self):
        self.directory.cleanup()

    def rows(self, query, parameters=()):
        with sqlite3.connect(self.db) as connection:
            return connection.execute(query, parameters).fetchall()

    def test_preparation_is_read_only_and_changes_only_the_selected_session(self):
        before = self.rows("SELECT * FROM edt_sessions ORDER BY id")
        prepared = self.verification._prepare_corrected_version(
            self.first["version_id"], self.session_ids[0],
            {"salle": "C3", "horaire": "09:00-11:00"}, self.db,
        )

        self.assertEqual(
            [(item["label"], item["before"], item["after"]) for item in prepared["changed_fields"]],
            [("Horaire", "08:30-10:30", "09:00-11:00"), ("Salle", "A1", "C3")],
        )
        self.assertEqual(prepared["details"].iloc[0]["Salle"], "C3")
        self.assertEqual(prepared["details"].iloc[1]["Salle"], "B2")
        self.assertEqual(self.rows("SELECT * FROM edt_sessions ORDER BY id"), before)

    def test_explicit_save_creates_v2_preserves_v1_and_reports_sync_failure(self):
        sync_calls = []

        result = self.verification._save_session_correction(
            self.first["version_id"], self.session_ids[0], {"salle": "C3"}, self.db,
            sync_func=lambda: (sync_calls.append(True) and True, "Drive indisponible"),
        )

        self.assertEqual(result["status"], "created")
        self.assertEqual(result["version_number"], 2)
        self.assertFalse(result["sync_ok"])
        self.assertEqual(len(sync_calls), 1)
        self.assertEqual(
            self.rows("SELECT version_number, is_active FROM edt_versions ORDER BY version_number"),
            [(1, 0), (2, 1)],
        )
        self.assertEqual(
            self.rows("SELECT salle FROM edt_sessions WHERE version_id=? ORDER BY id", (self.first["version_id"],)),
            [("A1",), ("B2",)],
        )
        self.assertEqual(
            self.rows("SELECT salle FROM edt_sessions WHERE version_id=? ORDER BY id", (result["version_id"],)),
            [("C3",), ("B2",)],
        )

    def test_no_change_and_repeated_save_do_not_create_extra_versions(self):
        sync_calls = []
        unchanged = self.verification._save_session_correction(
            self.first["version_id"], self.session_ids[0], {"salle": "A1"}, self.db,
            sync_func=lambda: (sync_calls.append(True) and True, "ok"),
        )
        self.assertEqual(unchanged["status"], "no_changes")
        self.assertEqual(sync_calls, [])

        first_save = self.verification._save_session_correction(
            self.first["version_id"], self.session_ids[0], {"salle": "C3"}, self.db,
            sync_func=lambda: (sync_calls.append(True) and True, "ok"),
        )
        repeated = self.verification._save_session_correction(
            self.first["version_id"], self.session_ids[0], {"salle": "C3"}, self.db,
            sync_func=lambda: (sync_calls.append(True) and True, "ok"),
        )

        self.assertEqual(first_save["status"], "created")
        self.assertEqual(repeated["status"], "duplicate")
        self.assertEqual(repeated["version_id"], first_save["version_id"])
        self.assertEqual(self.rows("SELECT COUNT(*) FROM edt_versions"), [(2,)])
        self.assertEqual(len(sync_calls), 1)

    def test_session_from_another_version_is_rejected_without_mutation(self):
        before = self.rows("SELECT * FROM edt_versions ORDER BY id")
        with self.assertRaisesRegex(ValueError, "ne correspond pas"):
            self.verification._prepare_corrected_version(
                self.first["version_id"], 999_999, {"salle": "C3"}, self.db,
            )
        self.assertEqual(self.rows("SELECT * FROM edt_versions ORDER BY id"), before)

    def test_invalid_duration_is_rejected_without_creating_a_version(self):
        for invalid in ("deux heures", "0", "-1", "NaN", "inf", "1e309"):
            with self.subTest(invalid=invalid):
                with self.assertRaisesRegex(ValueError, "durée doit être"):
                    self.verification._save_session_correction(
                        self.first["version_id"], self.session_ids[0], {"duree": invalid},
                        self.db, sync_func=lambda: (True, "ok"),
                    )
        self.assertEqual(self.rows("SELECT COUNT(*) FROM edt_versions"), [(1,)])

    def test_stale_correction_cannot_replace_a_newer_active_version(self):
        newer = self.frame.copy()
        newer.loc[1, "Salle"] = "B9"
        second = memory.save_timetable_version(
            newer, "2026-2027", "Automne", "IAID", "S1", "Autre correction",
            db_path=self.db,
        )

        with self.assertRaisesRegex(RuntimeError, "n’est plus active"):
            self.verification._save_session_correction(
                self.first["version_id"], self.session_ids[0], {"salle": "C3"},
                self.db, sync_func=lambda: (True, "ok"),
            )

        self.assertEqual(
            self.rows("SELECT version_number, is_active FROM edt_versions ORDER BY version_number"),
            [(1, 0), (2, 1)],
        )
        self.assertEqual(
            self.rows("SELECT salle FROM edt_sessions WHERE version_id=? ORDER BY id", (second["version_id"],)),
            [("A1",), ("B9",)],
        )

    def test_ui_prepares_cancels_then_confirms_a_new_version(self):
        from streamlit.testing.v1 import AppTest

        harness = Path(self.directory.name) / "verification_harness.py"
        harness.write_text(
            textwrap.dedent(
                f'''\
                from pathlib import Path
                import edt_verification_ui as ui

                ui.DB_PATH = Path({str(self.db)!r})
                ui.sync_edt_changes = lambda: (False, "Drive désactivé pour le test")
                ui.render_global_verification()
                '''
            ),
            encoding="utf-8",
        )
        prefix = f"verification_correction_{self.first['version_id']}_{self.session_ids[0]}"

        at = AppTest.from_file(str(harness), default_timeout=30).run()
        self.assertFalse(at.exception, at.exception)
        at.button(key=f"{prefix}_start").click().run()
        at.text_input(key=f"{prefix}_salle").set_value("C3")
        next(button for button in at.button if button.label == "Préparer la correction").click().run()
        self.assertTrue(any("non enregistrée" in item.value for item in at.warning))
        self.assertEqual(self.rows("SELECT COUNT(*) FROM edt_versions"), [(1,)])

        at.button(key=f"{prefix}_cancel").click().run()
        self.assertEqual(self.rows("SELECT COUNT(*) FROM edt_versions"), [(1,)])
        self.assertTrue(any("Aucune version n’a été créée" in item.value for item in at.info))

        at.button(key=f"{prefix}_start").click().run()
        at.text_input(key=f"{prefix}_salle").set_value("C3")
        next(button for button in at.button if button.label == "Préparer la correction").click().run()
        at.checkbox(key=f"{prefix}_confirm").check().run()
        at.button(key=f"{prefix}_save").click().run()
        self.assertFalse(at.exception, at.exception)
        self.assertEqual(
            self.rows("SELECT version_number, is_active FROM edt_versions ORDER BY version_number"),
            [(1, 0), (2, 1)],
        )
        self.assertTrue(any("V2" in item.value for item in at.warning))


if __name__ == "__main__":
    unittest.main()
