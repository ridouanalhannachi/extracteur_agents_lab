"""Laboratory isolation checks, using only disposable paths and fake secrets."""
import importlib.util
import os
from pathlib import Path
import shutil
import sqlite3
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch


ROOT = Path(__file__).resolve().parents[1]


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class LabIsolationTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.lab = self.root / "lab"
        self.lab.mkdir()
        self.production = self.root / "production"
        self.production.mkdir()
        self.production_db = self.production / "estn.db"
        with sqlite3.connect(self.production_db) as conn:
            conn.execute("CREATE TABLE sentinel (value TEXT)")
            conn.execute("INSERT INTO sentinel VALUES ('production-test-only')")
        self.original_bytes = self.production_db.read_bytes()
        env = patch.dict(os.environ, {
            "APP_MODE": "streamlit_cloud", "APP_DATA_DIR": str(self.production),
            "GDRIVE_TOKEN_JSON": '{"token":"fake-not-a-real-secret"}',
            "GDRIVE_TOKEN_B64": "ZmFrZQ==", "DRIVE_ENABLED": "true",
        })
        env.start()
        self.addCleanup(env.stop)
        shutil.copyfile(ROOT / "app_config.py", self.lab / "app_config.py")
        self.config = load_module("app_config", self.lab / "app_config.py")
        modules = patch.dict(sys.modules, {"app_config": self.config})
        modules.start()
        self.addCleanup(modules.stop)
        self.drive = load_module("lab_test_drive", ROOT / "gdrive_sync.py")

    def tearDown(self):
        self.assertEqual(self.production_db.read_bytes(), self.original_bytes)
        self.assertEqual(list(self.production.iterdir()), [self.production_db])

    def test_inherited_environment_cannot_select_production_data(self):
        self.assertEqual(self.config.APP_MODE, "lab")
        self.assertFalse(self.config.IS_CLOUD)
        self.assertFalse(self.config.IS_STREAMLIT_CLOUD)
        self.assertFalse(self.config.DRIVE_ENABLED)
        self.assertEqual(self.config.DB_PATH, self.lab / "data-lab" / "estn-lab.db")
        with sqlite3.connect(self.config.DB_PATH) as conn:
            conn.execute("CREATE TABLE lab_only (value TEXT)")

    def test_existing_local_and_environment_tokens_are_ignored(self):
        self.drive.TOKEN_PATH.write_text('{"token":"fake"}')
        self.drive.CREDENTIALS_PATH.write_text('{"installed":{}}')
        with patch.object(self.drive, "_ensure_dirs") as dirs:
            self.assertFalse(self.drive.credentials_configured())
            self.assertIsNone(self.drive.get_credentials())
            self.assertFalse(self.drive.is_connected())
            dirs.assert_not_called()
        with self.assertRaisesRegex(RuntimeError, "désactivé"):
            self.drive.get_credentials(interactive=True)

    def test_all_public_remote_operations_stop_before_network(self):
        with patch.object(self.drive, "build", create=True) as network:
            for operation in (
                self.drive._service, self.drive.get_remote_info,
                self.drive.upload_database, self.drive.download_database,
            ):
                with self.subTest(operation=operation.__name__):
                    with self.assertRaisesRegex(RuntimeError, "désactivé"):
                        operation()
            network.assert_not_called()
        supplied_service = Mock()
        with self.assertRaisesRegex(RuntimeError, "désactivé"):
            self.drive.ensure_drive_structure(supplied_service)
        supplied_service.files.assert_not_called()

    def test_credentials_cannot_be_saved_and_auto_sync_cannot_be_enabled(self):
        with self.assertRaisesRegex(RuntimeError, "désactivé"):
            self.drive.save_credentials_json(b'{"installed":{}}')
        self.assertFalse(self.drive.CREDENTIALS_PATH.exists())
        with self.assertRaisesRegex(RuntimeError, "désactivé"):
            self.drive.enable_auto_sync(True)
        self.drive.STATE_PATH.write_text('{"auto_sync":true}')
        self.assertFalse(self.drive.auto_sync_enabled())
        with patch.object(self.drive, "upload_database") as upload:
            success, message = self.drive.auto_upload_after_change()
            self.assertFalse(success)
            self.assertIn("désactivée", message)
            upload.assert_not_called()

    def test_cloud_environment_bootstraps_locally_without_drive(self):
        bootstrap = load_module("lab_test_bootstrap", ROOT / "cloud_bootstrap.py")
        remote = Mock()
        with patch.dict(sys.modules, {"gdrive_sync": remote}):
            self.assertEqual(bootstrap.bootstrap_cloud_database()["status"], "local")
            remote.is_connected.assert_not_called()
            remote.download_database.assert_not_called()


if __name__ == "__main__":
    unittest.main()
