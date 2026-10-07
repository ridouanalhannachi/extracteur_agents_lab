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


if __name__ == "__main__":
    unittest.main()
