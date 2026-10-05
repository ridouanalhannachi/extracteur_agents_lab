"""Conservative upload guard, with disposable SQLite and an in-memory Drive."""
import hashlib
import importlib.util
from pathlib import Path
import shutil
import sqlite3
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class Request:
    def __init__(self, callback):
        self.callback = callback

    def execute(self):
        return self.callback()


class FakeDrive:
    def __init__(self, content=None):
        self.content = content
        self.writes = []
        self.read_error = False

    def files(self):
        return self

    def metadata(self):
        if self.read_error:
            raise OSError("remote read unavailable")
        if self.content is None:
            return None
        return {"id": "fictional-db", "md5Checksum": hashlib.md5(self.content).hexdigest()}

    def copy(self, **kwargs):
        return Request(lambda: self._copy())

    def _copy(self):
        self.writes.append("copy")
        return {"id": "fictional-backup"}

    def update(self, media_body, **kwargs):
        return Request(lambda: self._write("update", media_body))

    def create(self, media_body, **kwargs):
        return Request(lambda: self._write("create", media_body))

    def _write(self, action, media):
        self.writes.append(action)
        self.content = Path(media).read_bytes()
        return self.metadata()


class DriveConcurrencyTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        shutil.copyfile(ROOT / "app_config.py", self.root / "app_config.py")
        config = load_module("app_config", self.root / "app_config.py")
        with patch.dict(sys.modules, {"app_config": config}):
            self.drive = load_module("concurrency_test_drive", ROOT / "gdrive_sync.py")
        self.local = config.DB_PATH
        self.make_db(self.local, "local correction")
        remote = self.root / "remote.db"
        self.make_db(remote, "remote correction")
        self.fake = FakeDrive(remote.read_bytes())
        self.original_local = self.local.read_bytes()
        self.original_remote = self.fake.content
        self.original_state = {"last_sync": "previous-sync", "last_synced_md5": "old-hash"}
        self.drive._save_state(self.original_state)
        for item in (
            patch.object(self.drive, "_service", return_value=self.fake),
            patch.object(self.drive, "ensure_drive_structure", return_value=("root", "backups")),
            patch.object(self.drive, "_drive_db", side_effect=lambda *args: self.fake.metadata()),
            patch.object(self.drive, "MediaFileUpload", side_effect=lambda path, **kw: path, create=True),
        ):
            item.start()
            self.addCleanup(item.stop)

    @staticmethod
    def make_db(path, value):
        with sqlite3.connect(path) as conn:
            conn.execute("CREATE TABLE sessions (correction TEXT)")
            conn.execute("INSERT INTO sessions VALUES (?)", (value,))

    def assert_preserved(self):
        self.assertEqual(self.local.read_bytes(), self.original_local)
        self.assertEqual(self.fake.content, self.original_remote)
        self.assertEqual(self.fake.writes, [])
        self.assertEqual(self.drive._load_state(), self.original_state)

    def test_existing_remote_blocks_manual_upload_with_or_without_backup(self):
        for backup in (True, False):
            with self.subTest(backup=backup):
                with self.assertRaisesRegex(RuntimeError, "protection atomique"):
                    self.drive.upload_database(create_remote_backup=backup)
                self.assert_preserved()

    def test_two_stale_clients_cannot_erase_remote_correction(self):
        second = self.root / "client-b.db"
        self.make_db(second, "client B correction")
        before = second.read_bytes()
        for client in (self.local, second):
            with patch.object(self.drive, "DB_PATH", client):
                with self.assertRaisesRegex(RuntimeError, "protection atomique"):
                    self.drive.upload_database(create_remote_backup=False)
        self.assertEqual(second.read_bytes(), before)
        self.assert_preserved()

    def test_remote_read_failure_stops_without_writes(self):
        self.fake.read_error = True
        with self.assertRaisesRegex(OSError, "remote read unavailable"):
            self.drive.upload_database()
        self.assert_preserved()

    def test_auto_upload_does_not_report_success_when_blocked(self):
        with patch.object(self.drive, "auto_sync_enabled", return_value=True), patch.object(self.drive, "is_connected", return_value=True):
            success, message = self.drive.auto_upload_after_change()
        self.assertFalse(success)
        self.assertIn("protection atomique", message)
        self.assertIn("locale conservée", message)
        self.assert_preserved()

    def test_sync_local_only_change_returns_conflict(self):
        self.original_state["last_synced_md5"] = self.fake.metadata()["md5Checksum"]
        self.drive._save_state(self.original_state)
        result = self.drive.sync_database()
        self.assertEqual(result["status"], "conflict")
        self.assertIn("protection atomique", result["message"])
        self.assert_preserved()

    def test_remote_appearing_between_sync_and_upload_is_not_overwritten(self):
        with patch.object(self.drive, "_drive_db", side_effect=[None, self.fake.metadata()]):
            result = self.drive.sync_database()
        self.assertEqual(result["status"], "conflict")
        self.assert_preserved()

    def test_first_creation_records_confirmed_upload(self):
        self.fake.content = None
        result = self.drive.sync_database()
        self.assertEqual(result["status"], "uploaded")
        self.assertEqual(self.fake.writes, ["create"])
        uploaded = self.root / "uploaded.db"
        uploaded.write_bytes(self.fake.content)
        with sqlite3.connect(uploaded) as conn:
            self.assertEqual(conn.execute("SELECT correction FROM sessions").fetchall(), [("local correction",)])
        self.assertEqual(self.local.read_bytes(), self.original_local)
        state = self.drive._load_state()
        self.assertEqual(state["last_action"], "upload")
        self.assertEqual(state["last_synced_md5"], self.fake.metadata()["md5Checksum"])
        self.assertFalse(self.drive.DRIVE_ENABLED)

    def test_identical_remote_remains_noop(self):
        self.fake.content = self.original_local
        result = self.drive.sync_database()
        self.assertEqual(result["status"], "up_to_date")
        self.assertEqual(self.fake.writes, [])
        self.assertEqual(self.local.read_bytes(), self.original_local)

    def test_manual_upload_of_identical_database_is_also_blocked(self):
        self.fake.content = self.original_local
        self.original_remote = self.original_local
        with self.assertRaisesRegex(RuntimeError, "protection atomique"):
            self.drive.upload_database()
        self.assert_preserved()

    def test_existing_remote_without_checksum_is_blocked(self):
        with patch.object(self.drive, "_drive_db", return_value={"id": "fictional-db"}):
            with self.assertRaisesRegex(RuntimeError, "protection atomique"):
                self.drive.upload_database(create_remote_backup=False)
        self.assert_preserved()

    def test_auto_upload_read_failure_does_not_report_success(self):
        self.fake.read_error = True
        with patch.object(self.drive, "auto_sync_enabled", return_value=True), patch.object(self.drive, "is_connected", return_value=True):
            success, message = self.drive.auto_upload_after_change()
        self.assertFalse(success)
        self.assertIn("remote read unavailable", message)
        self.assert_preserved()
