"""Search-result navigation to the exact read-only History context."""
from __future__ import annotations

from pathlib import Path
import sqlite3
import tempfile
import unittest

import pandas as pd

import edt_memory as memory
from edt_global_search_ui import _session_result_label
from edt_history_ui import (
    INVALID_SESSION_TARGET_MESSAGE,
    _consume_session_open_intent,
    _version_session_filter_keys,
)
from ui_navigation import HISTORY_SESSION_INTENT_KEY
from ui_navigation import HISTORY_SESSION_FOCUS_KEY


def _frame(room):
    return pd.DataFrame([{
        "Jour": "Lundi", "Horaire": "08:30-10:30",
        "Matière": "Algorithmique", "Type": "CM",
        "Nom et prénom": "Alice Test", "Groupe": "G1", "Salle": room,
        "Durée": 2.0, "Filière": "IAID", "Niveau": "S1",
        "Année universitaire": "2026-2027",
        "Source PDF": "donnees-fictives.pdf", "Page": "1",
    }])


class SearchHistoryNavigationTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.db = Path(self.directory.name) / "edt.db"
        self.v1 = memory.save_timetable_version(
            _frame("A1"), "2026-2027", "Automne", "IAID", "S1",
            db_path=self.db,
        )
        self.v2 = memory.save_timetable_version(
            _frame("B2"), "2026-2027", "Automne", "IAID", "S1",
            db_path=self.db,
        )
        with sqlite3.connect(self.db) as conn:
            self.v1_session_id = conn.execute(
                "SELECT id FROM edt_sessions WHERE version_id=?",
                (self.v1["version_id"],),
            ).fetchone()[0]

    def snapshot(self):
        with sqlite3.connect(self.db) as conn:
            return (
                conn.execute("SELECT * FROM edt_versions ORDER BY id").fetchall(),
                conn.execute("SELECT * FROM edt_sessions ORDER BY id").fetchall(),
            )

    def test_intent_is_validated_and_consumed_once(self):
        state = {HISTORY_SESSION_INTENT_KEY: {
            "timetable_id": self.v1["timetable_id"],
            "version_id": self.v1["version_id"],
            "session_id": self.v1_session_id,
        }}
        target, error = _consume_session_open_intent(state, self.db)
        self.assertIsNone(error)
        self.assertEqual(target["session_id"], self.v1_session_id)
        self.assertNotIn(HISTORY_SESSION_INTENT_KEY, state)
        self.assertEqual(_consume_session_open_intent(state, self.db), (None, None))

    def test_ambiguous_time_slots_have_distinct_labels_and_open_exact_session(self):
        from streamlit.testing.v1 import AppTest

        ambiguous_db = Path(self.directory.name) / "ambiguous.db"
        rows = pd.concat([
            _frame("A1").assign(**{
                "Matière": "Programmation",
                "Nom et prénom": "Alice Test",
                "Groupe": "G1",
            }),
            _frame("B2").assign(**{
                "Matière": "Programmation",
                "Nom et prénom": "Bruno Test",
                "Groupe": "G2",
            }),
        ], ignore_index=True)
        version = memory.save_timetable_version(
            rows, "2026-2027", "Automne", "IAID", "S1",
            db_path=ambiguous_db,
        )
        with sqlite3.connect(ambiguous_db) as conn:
            expected_session_id = conn.execute(
                "SELECT id FROM edt_sessions WHERE enseignant='Bruno Test'"
            ).fetchone()[0]
            indexed = pd.read_sql_query(
                '''
                SELECT s.*, v.version_number, t.filiere, t.niveau
                FROM edt_sessions s
                JOIN edt_versions v ON v.id=s.version_id
                JOIN edt_timetables t ON t.id=v.timetable_id
                ORDER BY s.id
                ''',
                conn,
            )
        labels = [_session_result_label(row) for _, row in indexed.iterrows()]
        self.assertEqual(len(set(labels)), 2)
        self.assertIn("Ens. Alice Test | Groupe G1 | Salle A1", labels[0])
        self.assertIn("Ens. Bruno Test | Groupe G2 | Salle B2", labels[1])

        script = f"""
from pathlib import Path
import edt_global_search_ui
import edt_history_ui
import ui_navigation
edt_global_search_ui.DB_PATH = Path({str(ambiguous_db)!r})
edt_history_ui.DB_PATH = Path({str(ambiguous_db)!r})
module = ui_navigation.render_navigation()
if module == ui_navigation.MODULES[3]:
    edt_global_search_ui.render_global_edt_search()
elif module == ui_navigation.MODULES[5]:
    edt_history_ui.render_edt_history()
"""
        at = AppTest.from_string(script, default_timeout=20).run()
        at.radio(key="main_module").set_value("🔎 Recherche globale").run()
        at.text_input(key="global_edt_search_query").set_value("Programmation").run()
        selectbox = at.selectbox(key="global_edt_search_selected_session")
        self.assertEqual(len(set(selectbox.options)), 2)
        bruno_label = next(option for option in selectbox.options if "Bruno Test" in option)
        selectbox.select(bruno_label).run()
        at.button(key="global_edt_search_open_history").click().run()
        self.assertEqual(
            at.session_state[HISTORY_SESSION_FOCUS_KEY],
            {
                "timetable_id": version["timetable_id"],
                "version_id": version["version_id"],
                "session_id": expected_session_id,
            },
        )

    def test_cross_version_and_missing_targets_are_rejected(self):
        for intent in (
            {
                "timetable_id": self.v1["timetable_id"],
                "version_id": self.v2["version_id"],
                "session_id": self.v1_session_id,
            },
            {"timetable_id": 999, "version_id": 999, "session_id": 999},
        ):
            target, error = _consume_session_open_intent(
                {HISTORY_SESSION_INTENT_KEY: intent}, self.db,
            )
            self.assertIsNone(target)
            self.assertEqual(error, INVALID_SESSION_TARGET_MESSAGE)

    def test_invalid_ui_target_shows_only_the_exact_error_context(self):
        from streamlit.testing.v1 import AppTest

        script = f"""
from pathlib import Path
import streamlit as st
import edt_history_ui
from ui_navigation import HISTORY_SESSION_INTENT_KEY
edt_history_ui.DB_PATH = Path({str(self.db)!r})
if "invalid_target_seeded" not in st.session_state:
    st.session_state["invalid_target_seeded"] = True
    st.session_state[HISTORY_SESSION_INTENT_KEY] = {{
        "timetable_id": {self.v1["timetable_id"]},
        "version_id": {self.v2["version_id"]},
        "session_id": {self.v1_session_id},
    }}
edt_history_ui.render_edt_history()
"""
        at = AppTest.from_string(script, default_timeout=20).run()
        self.assertFalse(at.exception)
        self.assertEqual([item.value for item in at.error], [INVALID_SESSION_TARGET_MESSAGE])
        self.assertFalse(at.selectbox)
        self.assertNotIn(HISTORY_SESSION_INTENT_KEY, at.session_state)

    def test_ui_opens_archived_version_marks_target_preserves_filters_and_db(self):
        from streamlit.testing.v1 import AppTest

        before = self.snapshot()
        filter_keys = _version_session_filter_keys(
            self.v1["timetable_id"], self.v2["version_id"],
        )
        script = f"""
from pathlib import Path
import edt_global_search_ui
import edt_history_ui
import ui_navigation
edt_global_search_ui.DB_PATH = Path({str(self.db)!r})
edt_history_ui.DB_PATH = Path({str(self.db)!r})
module = ui_navigation.render_navigation()
if module == ui_navigation.MODULES[3]:
    edt_global_search_ui.render_global_edt_search()
elif module == ui_navigation.MODULES[5]:
    edt_history_ui.render_edt_history()
"""
        at = AppTest.from_string(script, default_timeout=20).run()
        at.session_state[filter_keys["search"]] = "à conserver"
        at.radio(key="main_module").set_value("🔎 Recherche globale").run()
        at.text_input(key="global_edt_search_query").set_value("Algorithmique").run()
        archived_label = next(
            option for option in at.selectbox(key="global_edt_search_selected_session").options
            if "V1" in option
        )
        at.selectbox(key="global_edt_search_selected_session").select(archived_label).run()
        at.button(key="global_edt_search_open_history").click().run()

        self.assertEqual(at.radio(key="main_module").value, "🗂️ Historique EDT")
        self.assertNotIn(HISTORY_SESSION_INTENT_KEY, at.session_state)
        self.assertEqual(
            at.session_state[HISTORY_SESSION_FOCUS_KEY],
            {
                "timetable_id": self.v1["timetable_id"],
                "version_id": self.v1["version_id"],
                "session_id": self.v1_session_id,
            },
        )
        self.assertEqual(
            at.session_state[f"edt_history_selected_version_{self.v1['timetable_id']}"],
            self.v1["version_id"],
        )
        self.assertEqual(at.session_state[filter_keys["search"]], "à conserver")
        self.assertTrue(any(
            "Séance recherchée ouverte dans V1 (archivée)." in item.value
            for item in at.success
        ))

        at.run()
        self.assertNotIn(HISTORY_SESSION_INTENT_KEY, at.session_state)
        self.assertEqual(
            at.session_state[f"edt_history_selected_version_{self.v1['timetable_id']}"],
            self.v1["version_id"],
        )
        self.assertTrue(any(
            "Séance recherchée ouverte dans V1 (archivée)." in item.value
            for item in at.success
        ))

        at.button(key="history_clear_session_focus").click().run()
        self.assertNotIn(HISTORY_SESSION_FOCUS_KEY, at.session_state)
        self.assertFalse(any(
            "Séance recherchée ouverte" in item.value for item in at.success
        ))
        self.assertEqual(
            at.session_state[f"edt_history_selected_version_{self.v1['timetable_id']}"],
            self.v1["version_id"],
        )
        self.assertEqual(at.session_state[filter_keys["search"]], "à conserver")
        self.assertEqual(self.snapshot(), before)


if __name__ == "__main__":
    unittest.main()
