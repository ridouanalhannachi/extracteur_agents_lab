"""Interactive, version-isolated filters for the selected history timetable."""
from __future__ import annotations

import io
from pathlib import Path
import sqlite3
import tempfile
import unittest

import pandas as pd

import edt_memory as memory
from edt_history_ui import (
    _build_version_export,
    _filter_version_sessions,
    _reset_version_session_filters,
    _version_session_filter_keys,
)


def _frame(rows):
    defaults = {
        "Type": "CM",
        "Durée": 2.0,
        "Filière": "IAID",
        "Niveau": "S1",
        "Année universitaire": "2026-2027",
        "Source PDF": "donnees-fictives.pdf",
        "Page": "1",
    }
    return pd.DataFrame([{**defaults, **row} for row in rows])


V1_ROWS = [
    {
        "Jour": "Lundi", "Matière": "Algorithmique",
        "Nom et prénom": "Alice Test", "Horaire": "08:30-10:30",
        "Groupe": "G1", "Salle": "A1",
    },
    {
        "Jour": "Mardi", "Matière": "Bases de données",
        "Nom et prénom": "Bruno Test", "Horaire": "10:30-12:30",
        "Groupe": "G2", "Salle": "B2",
    },
    {
        "Jour": "Lundi", "Matière": "Réseaux",
        "Nom et prénom": "Alice Test", "Horaire": "14:00-16:00",
        "Groupe": "G2", "Salle": "C3",
    },
]

V2_ROWS = [
    {
        "Jour": "Mercredi", "Matière": "Systèmes",
        "Nom et prénom": "Chloé Test", "Horaire": "09:00-11:00",
        "Groupe": "G3", "Salle": "D4",
    },
    {
        "Jour": "Jeudi", "Matière": "Statistiques",
        "Nom et prénom": "David Test", "Horaire": "11:00-13:00",
        "Groupe": "G4", "Salle": "E5",
    },
]


class PureVersionSessionFilterTests(unittest.TestCase):
    def setUp(self):
        self.sessions = pd.DataFrame([
            {
                "Jour": row["Jour"], "Horaire": row["Horaire"],
                "Matière": row["Matière"], "Enseignant": row["Nom et prénom"],
                "Groupe": row["Groupe"], "Salle": row["Salle"],
            }
            for row in V1_ROWS
        ])

    def test_default_and_each_text_field_are_supported_without_mutation(self):
        before = self.sessions.copy(deep=True)
        self.assertEqual(len(_filter_version_sessions(self.sessions)), 3)
        for query, subject in [
            ("algo", "Algorithmique"),
            ("bruno", "Bases de données"),
            ("g1", "Algorithmique"),
            ("b2", "Bases de données"),
            ("14:00", "Réseaux"),
            ("reseaux", "Réseaux"),
        ]:
            result = _filter_version_sessions(self.sessions, search=query)
            self.assertEqual(result["Matière"].tolist(), [subject])
        pd.testing.assert_frame_equal(self.sessions, before)

    def test_individual_combined_and_zero_results(self):
        self.assertEqual(
            _filter_version_sessions(self.sessions, day="Lundi")["Matière"].tolist(),
            ["Algorithmique", "Réseaux"],
        )
        self.assertEqual(
            _filter_version_sessions(self.sessions, teacher="Alice Test")["Matière"].tolist(),
            ["Algorithmique", "Réseaux"],
        )
        self.assertEqual(
            _filter_version_sessions(self.sessions, group="G2")["Matière"].tolist(),
            ["Bases de données", "Réseaux"],
        )
        combined = _filter_version_sessions(
            self.sessions, search="réseaux", day="Lundi",
            teacher="Alice Test", group="G2",
        )
        self.assertEqual(combined["Salle"].tolist(), ["C3"])
        self.assertTrue(
            _filter_version_sessions(self.sessions, search="introuvable").empty
        )

    def test_reset_and_keys_are_isolated_by_timetable_and_version(self):
        first = _version_session_filter_keys(7, 11)
        second = _version_session_filter_keys(7, 12)
        state = {
            first["search"]: "algo", first["day"]: "Lundi",
            first["teacher"]: "Alice Test", first["group"]: "G1",
            second["search"]: "stat", second["day"]: "Jeudi",
        }
        _reset_version_session_filters(7, 11, state)
        self.assertEqual(
            [state[first[name]] for name in ("search", "day", "teacher", "group")],
            ["", "Tous", "Tous", "Tous"],
        )
        self.assertEqual(state[second["search"]], "stat")
        self.assertEqual(state[second["day"]], "Jeudi")


class VersionSessionFilterAppTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.db = Path(self.directory.name) / "edt.db"
        self.first = memory.save_timetable_version(
            _frame(V1_ROWS), "2026-2027", "Automne", "IAID", "S1",
            db_path=self.db,
        )
        self.second = memory.save_timetable_version(
            _frame(V2_ROWS), "2026-2027", "Automne", "IAID", "S1",
            db_path=self.db,
        )
        with sqlite3.connect(self.db) as conn:
            conn.execute("DROP TABLE IF EXISTS edt_version_changes")
            conn.execute("DROP TABLE IF EXISTS edt_version_change_summary")

    def snapshot(self):
        with sqlite3.connect(self.db) as conn:
            return (
                conn.execute("SELECT * FROM edt_versions ORDER BY id").fetchall(),
                conn.execute("SELECT * FROM edt_sessions ORDER BY id").fetchall(),
            )

    def app(self):
        from streamlit.testing.v1 import AppTest

        script = f"""
from pathlib import Path
import edt_history_ui
edt_history_ui.DB_PATH = Path({str(self.db)!r})
edt_history_ui.render_edt_history()
"""
        return AppTest.from_string(script, default_timeout=20).run()

    @staticmethod
    def has_caption(at, text):
        return any(text in item.value for item in at.caption)

    def test_ui_zero_reset_version_return_and_read_only_guarantees(self):
        before_db = self.snapshot()
        _, before_export, _ = _build_version_export(
            self.second["version_id"], self.db,
        )
        before_exported_sessions = pd.read_excel(
            io.BytesIO(before_export),
            sheet_name="Séances détaillées",
        )
        timetable_id = self.first["timetable_id"]
        v1_keys = _version_session_filter_keys(timetable_id, self.first["version_id"])
        v2_keys = _version_session_filter_keys(timetable_id, self.second["version_id"])

        at = self.app()
        self.assertFalse(at.exception)
        self.assertTrue(self.has_caption(at, "2 séance(s) affichée(s) sur 2"))
        self.assertTrue(self.has_caption(at, "Excel conserve toutes les séances"))

        at.text_input(key=v2_keys["search"]).set_value("introuvable").run()
        self.assertTrue(self.has_caption(at, "0 séance(s) affichée(s) sur 2"))
        self.assertTrue(any(
            "Aucune séance ne correspond aux filtres" in item.value
            for item in at.warning
        ))
        at.button(
            key=f"history_session_filter_reset_{timetable_id}_{self.second['version_id']}"
        ).click().run()
        self.assertEqual(at.session_state[v2_keys["search"]], "")
        self.assertTrue(self.has_caption(at, "2 séance(s) affichée(s) sur 2"))

        at.text_input(key=v2_keys["search"]).set_value("systèmes").run()
        self.assertTrue(self.has_caption(at, "1 séance(s) affichée(s) sur 2"))
        at.button(key=f"history_version_button_{timetable_id}_1").click().run()
        self.assertTrue(self.has_caption(at, "3 séance(s) affichée(s) sur 3"))
        at.selectbox(key=v1_keys["day"]).select("Lundi").run()
        self.assertTrue(self.has_caption(at, "2 séance(s) affichée(s) sur 3"))
        at.button(key=f"history_version_button_{timetable_id}_2").click().run()
        self.assertEqual(at.session_state[v2_keys["search"]], "systèmes")
        self.assertTrue(self.has_caption(at, "1 séance(s) affichée(s) sur 2"))
        at.button(key=f"history_version_button_{timetable_id}_1").click().run()
        self.assertEqual(at.session_state[v1_keys["day"]], "Lundi")
        self.assertTrue(self.has_caption(at, "2 séance(s) affichée(s) sur 3"))

        _, after_export, _ = _build_version_export(
            self.second["version_id"], self.db,
        )
        after_exported_sessions = pd.read_excel(
            io.BytesIO(after_export),
            sheet_name="Séances détaillées",
        )
        pd.testing.assert_frame_equal(
            after_exported_sessions,
            before_exported_sessions,
        )
        self.assertEqual(self.snapshot(), before_db)


if __name__ == "__main__":
    unittest.main()
