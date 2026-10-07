"""Real Streamlit routing checks on a disposable empty laboratory."""
import importlib.util
from pathlib import Path
import shutil
import tempfile
import unittest

@unittest.skipUnless(importlib.util.find_spec("streamlit"), "Streamlit required for UI checks")
class NavigationTests(unittest.TestCase):
    def run_scenario(self, scenario):
        import os
        import subprocess
        import textwrap
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for file in Path(__file__).resolve().parents[1].glob("*.py"):
                shutil.copy2(file, root / file.name)
            script = """from pathlib import Path
from streamlit.testing.v1 import AppTest
import app_config
assert app_config.DB_PATH.is_relative_to(Path.cwd())
at = AppTest.from_file('app.py', default_timeout=20).run()
assert not at.exception
""" + textwrap.dedent(scenario)
            env = dict(os.environ, PYTHONPATH=str(root))
            result = subprocess.run([__import__('sys').executable, '-c', script],
                cwd=root, env=env, capture_output=True, text=True, timeout=60)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_home_shortcuts_and_return(self):
        self.run_scenario("""
            assert at.radio(key="main_module").value == "🏠 Accueil"
            keys = [button.key for button in at.button if str(button.key).startswith("home_")]
            assert len(keys) == 6
            for key in keys:
                at.button(key=key).click().run()
                assert not at.exception
                assert at.radio(key="main_module").value == key[5:]
                at.radio(key="main_module").set_value("🏠 Accueil").run()
                assert not at.exception
        """)

    def test_ocr_settings_survive_navigation_and_drive_stays_disabled(self):
        self.run_scenario("""
            at.checkbox[0].check().run()
            at.text_input[0].set_value("fictitious-ocr-path").run()
            at.radio(key="main_module").set_value("☁️ Google Drive").run()
            assert not at.exception
            assert any("désactiv" in item.value.lower() for item in at.info)
            at.radio(key="main_module").set_value("📅 Emplois du temps").run()
            assert not at.exception
            assert at.checkbox[0].value
            assert at.text_input[0].value == "fictitious-ocr-path"
        """)
