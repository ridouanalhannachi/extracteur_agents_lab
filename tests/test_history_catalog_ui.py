"""Focused checks for the history catalog filters."""
import unittest
import sqlite3
import tempfile
from pathlib import Path

import pandas as pd

from edt_history_ui import _filter_history_catalog, _reset_history_filters


class HistoryCatalogFilterTests(unittest.TestCase):
    def setUp(self):
        self.catalog = pd.DataFrame(
            [
                {
                    "id": 11,
                    "Année universitaire": "2025-2026",
                    "Période": "Automne",
                    "Filière": "Filière A",
                    "Semestre": "S1",
                },
                {
                    "id": 22,
                    "Année universitaire": "2026-2027",
                    "Période": "Printemps",
                    "Filière": "Filière B",
                    "Semestre": "S2",
                },
            ]
        )

    def test_default_and_combined_filters_preserve_expected_rows(self):
        initial = _filter_history_catalog(self.catalog, {})
        self.assertEqual(initial["id"].tolist(), [11, 22])

        filtered = _filter_history_catalog(
            self.catalog,
            {"Filière": "Filière B", "Semestre": "S2"},
        )
        self.assertEqual(filtered["id"].tolist(), [22])
        self.assertEqual(self.catalog["id"].tolist(), [11, 22])

    def test_empty_filter_result_is_explicit_to_the_caller(self):
        filtered = _filter_history_catalog(
            self.catalog,
            {"Période": "Automne", "Semestre": "S2"},
        )
        self.assertTrue(filtered.empty)

    def test_reset_restores_all_filter_values(self):
        state = {
            "history_year": "2026-2027",
            "history_period": "Printemps",
            "history_filiere": "Filière B",
            "history_semester": "S2",
            "unrelated": "preserved",
        }
        _reset_history_filters(state)
        self.assertEqual(
            [state[key] for key in (
                "history_year", "history_period", "history_filiere", "history_semester"
            )],
            ["Tous"] * 4,
        )
        self.assertEqual(state["unrelated"], "preserved")

    def test_streamlit_catalog_count_filter_reset_and_empty_state(self):
        from streamlit.testing.v1 import AppTest

        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "history.db"
            with sqlite3.connect(database) as conn:
                conn.executescript(
                    """
                    CREATE TABLE edt_timetables (
                        id INTEGER PRIMARY KEY, academic_year TEXT, period TEXT,
                        filiere TEXT, niveau TEXT, created_at TEXT
                    );
                    CREATE TABLE edt_versions (
                        id INTEGER PRIMARY KEY, timetable_id INTEGER,
                        version_number INTEGER, imported_at TEXT,
                        source_documents TEXT, source_hash TEXT, status TEXT,
                        is_active INTEGER, comment TEXT, sessions_count INTEGER
                    );
                    INSERT INTO edt_timetables VALUES
                        (11, '2025-2026', 'Automne', 'Filière A', 'S1', '2026-01-01'),
                        (22, '2026-2027', 'Printemps', 'Filière B', 'S2', '2026-01-02');
                    INSERT INTO edt_versions VALUES
                        (101, 11, 1, '2026-01-01', '[]', 'a', 'Active', 1, '', 0),
                        (202, 22, 1, '2026-01-02', '[]', 'b', 'Active', 1, '', 0);
                    """
                )

            script = f"""
from pathlib import Path
import edt_history_ui
edt_history_ui.DB_PATH = Path({str(database)!r})
edt_history_ui.render_edt_history()
"""
            at = AppTest.from_string(script, default_timeout=20).run()
            self.assertFalse(at.exception)
            self.assertTrue(any("2 résultat(s) sur 2" in item.value for item in at.caption))

            at.selectbox(key="history_filiere").set_value("Filière B").run()
            self.assertFalse(at.exception)
            self.assertTrue(any("1 résultat(s) sur 2" in item.value for item in at.caption))

            at.selectbox(key="history_period").set_value("Automne").run()
            self.assertTrue(any("Aucun emploi ne correspond" in item.value for item in at.warning))

            at.button(key="history_reset_filters").click().run()
            self.assertFalse(at.exception)
            self.assertEqual(at.selectbox(key="history_filiere").value, "Tous")
            self.assertEqual(at.selectbox(key="history_period").value, "Tous")
            self.assertTrue(any("2 résultat(s) sur 2" in item.value for item in at.caption))

    def test_archived_version_requires_confirmation_then_becomes_active(self):
        from streamlit.testing.v1 import AppTest

        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "history-actions.db"
            with sqlite3.connect(database) as conn:
                conn.executescript(
                    """
                    CREATE TABLE edt_timetables (
                        id INTEGER PRIMARY KEY, academic_year TEXT, period TEXT,
                        filiere TEXT, niveau TEXT, created_at TEXT
                    );
                    CREATE TABLE edt_versions (
                        id INTEGER PRIMARY KEY, timetable_id INTEGER,
                        version_number INTEGER, imported_at TEXT,
                        source_documents TEXT, source_hash TEXT, status TEXT,
                        is_active INTEGER, comment TEXT, sessions_count INTEGER
                    );
                    CREATE TABLE edt_sessions (
                        id INTEGER PRIMARY KEY, version_id INTEGER, jour TEXT,
                        matiere TEXT, type_seance TEXT, enseignant TEXT,
                        horaire TEXT, duree REAL, groupe TEXT, salle TEXT,
                        filiere TEXT, niveau TEXT, academic_year TEXT,
                        source_document TEXT, page TEXT
                    );
                    INSERT INTO edt_timetables VALUES
                        (11, '2026-2027', 'Automne', 'Filière A', 'S1', '2026-01-01');
                    INSERT INTO edt_versions VALUES
                        (101, 11, 1, '2026-01-01', '[]', 'a', 'Archivée', 0, 'Initiale', 1),
                        (102, 11, 2, '2026-02-01', '[]', 'b', 'Active', 1, 'Révisée', 1);
                    INSERT INTO edt_sessions VALUES
                        (1, 101, 'Lundi', 'Algèbre', 'Cours', 'Enseignant A',
                         '08:00', 2, 'G1', 'A1', 'Filière A', 'S1', '2026-2027', 'fictif.pdf', '1'),
                        (2, 102, 'Mardi', 'Analyse', 'TD', 'Enseignant B',
                         '10:00', 2, 'G1', 'A2', 'Filière A', 'S1', '2026-2027', 'fictif.pdf', '2');
                    """
                )

            script = f"""
from pathlib import Path
import edt_history_ui
edt_history_ui.DB_PATH = Path({str(database)!r})
edt_history_ui.render_edt_history()
"""
            at = AppTest.from_string(script, default_timeout=20).run()
            self.assertFalse(at.exception)

            at.button(key="history_version_button_11_1").click().run()
            activate = at.button(key="history_activate_version_11_101")
            self.assertTrue(activate.disabled)
            self.assertTrue(any("V1 sélectionnée — Archivée" in item.value for item in at.info))

            at.checkbox(key="history_confirm_activate_11_101").check().run()
            self.assertFalse(at.button(key="history_activate_version_11_101").disabled)
            at.button(key="history_activate_version_11_101").click().run()
            self.assertFalse(at.exception)
            self.assertTrue(any(
                "V1 est maintenant active ; V2 a été archivée" in item.value
                for item in at.success
            ))
            self.assertTrue(any("V1 sélectionnée — Active" in item.value for item in at.info))

            with sqlite3.connect(database) as conn:
                rows = conn.execute(
                    "SELECT version_number, is_active FROM edt_versions ORDER BY version_number"
                ).fetchall()
                sessions = conn.execute("SELECT COUNT(*) FROM edt_sessions").fetchone()[0]
            self.assertEqual(rows, [(1, 1), (2, 0)])
            self.assertEqual(sessions, 2)


if __name__ == "__main__":
    unittest.main()
