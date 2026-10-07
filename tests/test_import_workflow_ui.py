"""Regression checks for the import workflow hierarchy and stable widget keys."""
import ast
import importlib.util
import shutil
import subprocess
import tempfile
import textwrap
import unittest
from pathlib import Path


APP_PATH = Path(__file__).resolve().parents[1] / "app.py"
APP_SOURCE = APP_PATH.read_text(encoding="utf-8")
APP_TREE = ast.parse(APP_SOURCE)


def _with_block(name):
    for node in ast.walk(APP_TREE):
        if not isinstance(node, ast.With) or len(node.items) != 1:
            continue
        expression = node.items[0].context_expr
        if isinstance(expression, ast.Name) and expression.id == name:
            return node
    raise AssertionError(f"Bloc Streamlit introuvable : {name}")


def _source(node):
    return ast.get_source_segment(APP_SOURCE, node) or ""


class ImportWorkflowUiTests(unittest.TestCase):
    def test_tabs_follow_the_correction_export_memory_assistant_workflow(self):
        expected = [
            "1 · Corriger les séances",
            "2 · Vérifier et exporter",
            "3 · Enregistrer / Versions",
            "4 · Assistant local",
        ]
        tab_assignments = [
            node for node in ast.walk(APP_TREE)
            if isinstance(node, ast.Assign)
            and isinstance(node.value, ast.Call)
            and isinstance(node.value.func, ast.Attribute)
            and node.value.func.attr == "tabs"
        ]
        self.assertEqual(len(tab_assignments), 1)
        labels = ast.literal_eval(tab_assignments[0].value.args[0])
        self.assertEqual(labels, expected)

    def test_export_status_metrics_and_document_control_stay_in_export_tab(self):
        export_source = _source(_with_block("export_tab"))
        for expected in (
            "Prêt pour export",
            "séance(s) à compléter",
            'metric("Séances détectées"',
            'metric("Lignes enseignants/matières"',
            'metric("Documents traités"',
            'st.expander("Contrôle par document"',
            'key="intervenants_editor"',
        ):
            self.assertIn(expected, export_source)

    def test_existing_editor_and_memory_action_keys_are_preserved(self):
        correction_source = _source(_with_block("correction_tab"))
        memory_source = _source(_with_block("memory_tab"))
        self.assertIn('key="details_editor"', correction_source)
        self.assertIn('key="edt_mem_save"', memory_source)

    def test_version_recording_is_distinguished_from_global_verification(self):
        memory_source = _source(_with_block("memory_tab"))
        self.assertIn("Enregistrer une version conserve", memory_source)
        self.assertIn("ne remplace pas la « Vérification globale »", memory_source)

    def test_sidebar_labels_do_not_pretend_to_contain_the_export_action(self):
        self.assertNotIn('st.header("3. Export")', APP_SOURCE)
        self.assertIn('st.header("Résultat généré")', APP_SOURCE)

    @unittest.skipUnless(importlib.util.find_spec("streamlit"), "Streamlit required for UI checks")
    def test_empty_import_screen_exposes_the_three_step_path(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for file in APP_PATH.parent.glob("*.py"):
                shutil.copy2(file, root / file.name)
            script = textwrap.dedent("""
                from streamlit.testing.v1 import AppTest
                at = AppTest.from_file('app.py', default_timeout=20).run()
                assert not at.exception
                at.radio(key='main_module').set_value('📅 Emplois du temps').run()
                assert not at.exception
                assert any(
                    'importez les documents' in item.value
                    and 'onglets numérotés' in item.value
                    and 'enregistrer une version' in item.value
                    for item in at.info
                )
            """)
            result = subprocess.run(
                [__import__("sys").executable, "-c", script],
                cwd=root,
                capture_output=True,
                text=True,
                timeout=60,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
