"""AppTest regression for the interactive timetable correction draft."""
import importlib.util
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import textwrap
import unittest


@unittest.skipUnless(
    importlib.util.find_spec("streamlit"), "Streamlit required for UI checks"
)
class CorrectionInteractionsTests(unittest.TestCase):
    def test_draft_navigation_undo_rows_new_upload_and_database_isolation(self):
        """Exercise the whole correction loop with fictional uploads and SQLite."""
        source = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for file in source.glob("*.py"):
                shutil.copy2(file, root / file.name)

            harness = textwrap.dedent(
                r'''
                from unittest.mock import patch
                import runpy
                import pandas as pd
                import streamlit as st
                from edt_correction_state import DRAFT_KEY


                class Upload:
                    def __init__(self, identity):
                        self.name = f"{identity}.pdf"
                        self.identity = identity

                    def getvalue(self):
                        return f"fictional-{self.identity}".encode("utf-8")


                def fixture(name):
                    second = name == "second.pdf"
                    return [{
                        "Jour": "Mardi" if second else "Lundi",
                        "Matière": "Nouveau module" if second else "Module fictif",
                        "Type": "TD" if second else "CM",
                        "Nom et prénom": "Enseignant Test",
                        "Horaire": "10:30-12:30" if second else "08:30-10:30",
                        "Durée": 2.0,
                        "Groupe": "G1",
                        "Salle": "C1" if second else "A1",
                        "Filière": "TEST",
                        "Niveau": "S1",
                        "Année universitaire": "2026-2027",
                        "Source PDF": name,
                        "Page": "1",
                    }]


                def upload(label, **kwargs):
                    if kwargs.get("accept_multiple_files"):
                        return [Upload(st.session_state.get("test_upload_id", "first"))]
                    return None


                def extract(_data, name, **_kwargs):
                    return fixture(name), []


                original_editor = st.data_editor


                def editor(data, *args, **kwargs):
                    rendered = original_editor(data, *args, **kwargs)
                    if kwargs.get("key") != "details_editor":
                        return rendered

                    current = st.session_state.get(DRAFT_KEY)
                    if not isinstance(current, pd.DataFrame):
                        current = data
                    current = current.copy()
                    action = st.session_state.pop("test_editor_action", None)
                    if action == "edit":
                        current.loc[current.index[0], "Salle"] = st.session_state.get("test_room", "B2")
                    elif action == "add":
                        added = current.iloc[[0]].copy()
                        added.loc[:, "Matière"] = "Module ajouté"
                        added.loc[:, "Salle"] = "D4"
                        current = pd.concat([current, added], ignore_index=True)
                    elif action == "delete":
                        current = current.iloc[:-1].reset_index(drop=True)
                    elif action is None:
                        current = rendered

                    st.session_state["test_seen_rooms"] = current["Salle"].tolist()
                    st.session_state["test_seen_rows"] = len(current)
                    return current


                with (
                    patch("streamlit.file_uploader", side_effect=upload),
                    patch("streamlit.data_editor", side_effect=editor),
                    patch("edt_parser.extract_sessions_from_pdf_bytes", side_effect=extract),
                    patch("agent_edt.ollama_status", return_value=(False, "Simulation hors ligne")),
                ):
                    runpy.run_path("app.py", run_name="__main__")
                '''
            )
            (root / "harness.py").write_text(harness, encoding="utf-8")

            scenario = textwrap.dedent(
                r'''
                import sqlite3
                from streamlit.testing.v1 import AppTest
                from app_config import DB_PATH


                def database_snapshot():
                    with sqlite3.connect(DB_PATH) as connection:
                        versions = connection.execute(
                            "SELECT id, version_number, sessions_count FROM edt_versions ORDER BY id"
                        ).fetchall()
                        sessions = connection.execute(
                            "SELECT version_id, salle FROM edt_sessions ORDER BY id"
                        ).fetchall()
                    return versions, sessions


                at = AppTest.from_file("harness.py", default_timeout=30).run()
                assert not at.exception, at.exception
                at.radio(key="main_module").set_value("📅 Emplois du temps").run()
                assert not at.exception, at.exception
                assert at.session_state["test_seen_rooms"] == ["A1"]
                initial_database = database_snapshot()
                assert len(initial_database[0]) == 1

                # AppTest does not expose an editing API for st.data_editor. The
                # harness injects the same DataFrame returned by a browser edit.
                at.session_state["test_editor_action"] = "edit"
                at.run()
                assert not at.exception, at.exception
                assert at.session_state["test_seen_rooms"] == ["B2"]
                assert database_snapshot() == initial_database

                # Leaving the editor unmounts its widget. Returning must seed it
                # from the durable draft instead of re-extracting A1.
                at.radio(key="main_module").set_value("🏠 Accueil").run()
                at.radio(key="main_module").set_value("📅 Emplois du temps").run()
                assert not at.exception, at.exception
                assert at.session_state["test_seen_rooms"] == ["B2"]

                # Apply makes B2 the local checkpoint without writing SQLite.
                at.button(key="edt_details_apply").click().run()
                assert not at.exception, at.exception
                assert at.session_state["test_seen_rooms"] == ["B2"]
                assert any("Corrections appliquées au brouillon local" in x.value for x in at.success)
                assert database_snapshot() == initial_database

                # A new pending edit can be cancelled back to the last applied
                # checkpoint B2, not to the original extraction A1.
                at.session_state["test_room"] = "C3"
                at.session_state["test_editor_action"] = "edit"
                at.run()
                assert at.session_state["test_seen_rooms"] == ["C3"]
                at.button(key="edt_details_reset").click().run()
                assert not at.exception, at.exception
                assert at.session_state["test_seen_rooms"] == ["B2"]
                assert database_snapshot() == initial_database

                # Dynamic rows are part of the same draft contract.
                at.session_state["test_editor_action"] = "add"
                at.run()
                assert at.session_state["test_seen_rows"] == 2
                at.radio(key="main_module").set_value("🏠 Accueil").run()
                at.radio(key="main_module").set_value("📅 Emplois du temps").run()
                assert at.session_state["test_seen_rows"] == 2
                at.button(key="edt_details_reset").click().run()
                assert at.session_state["test_seen_rows"] == 1
                assert database_snapshot() == initial_database

                # A genuinely different upload must discard the old draft. Its
                # automatic baseline version is allowed, but V1 remains untouched.
                at.session_state["test_upload_id"] = "second"
                at.run()
                assert not at.exception, at.exception
                assert at.session_state["test_seen_rooms"] == ["C1"]
                assert any(
                    "brouillon de correction a été réinitialisé" in item.value
                    for item in at.info
                )
                new_database = database_snapshot()
                assert len(new_database[0]) == 2
                assert initial_database[1][0][1] == "A1"
                assert new_database[1][0][1] == "A1"
                '''
            )
            result = subprocess.run(
                [sys.executable, "-c", scenario],
                cwd=root,
                capture_output=True,
                text=True,
                timeout=120,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
