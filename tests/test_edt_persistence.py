"""Regression checks; all databases are disposable and Drive is mocked."""
import atexit
import ast
import importlib
import os
from pathlib import Path
import sqlite3
import sys
import tempfile
import types
import unittest
from unittest.mock import Mock, patch

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
_sandbox = tempfile.TemporaryDirectory()
atexit.register(_sandbox.cleanup)
with patch.dict(os.environ, {"APP_DATA_DIR": _sandbox.name, "APP_MODE": "local"}):
    import edt_memory as memory


def example_sessions():
    return pd.DataFrame([{
        "Jour": "Lundi", "Matière": "Algorithmique", "Type": "CM",
        "Nom et prénom": "Enseignant Test", "Horaire": "08:30-10:30",
        "Durée": 2.0, "Groupe": "G1", "Salle": "A1", "Filière": "IAID",
        "Niveau": "S1", "Année universitaire": "2026-2027",
        "Source PDF": "test.pdf", "Page": "1",
    }])


class MemoryTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.db = Path(self.directory.name) / "estn.db"
        self.frame = example_sessions()

    def save(self, frame=None):
        return memory.save_version(
            self.frame if frame is None else frame,
            "2026-2027", "Automne", "IAID", "S1", db_path=self.db,
        )

    def rows(self, sql):
        with sqlite3.connect(self.db) as conn:
            return conn.execute(sql).fetchall()

    def drop_columns(self, *columns):
        with sqlite3.connect(self.db) as conn:
            for column in columns:
                conn.execute(f'ALTER TABLE edt_versions DROP COLUMN "{column}"')

    def test_save_deduplicate_and_reload_corrected_version(self):
        first = self.save()
        duplicate = self.save()
        corrected = self.frame.copy()
        corrected.loc[0, "Salle"] = "B2"
        second = self.save(corrected)
        self.assertEqual((first["version_number"], second["version_number"]), (1, 2))
        self.assertEqual(duplicate["status"], "duplicate")
        self.assertEqual(memory.load_version_sessions(second["version_id"], self.db).iloc[0]["Salle"], "B2")
        self.assertEqual(memory.load_version_sessions(first["version_id"], self.db).iloc[0]["Salle"], "A1")
        self.assertEqual(self.rows("SELECT is_active FROM edt_versions ORDER BY version_number"), [(0,), (1,)])
        self.assertEqual(second["changes"]["modified_count"], 1)

    def test_missing_status_is_migrated_without_changing_sessions(self):
        first = self.save()
        before = self.rows("SELECT * FROM edt_sessions")
        self.drop_columns("status")
        memory.ensure_edt_memory_db(self.db)
        versions = memory.list_versions(first["timetable_id"], self.db)
        self.assertEqual(versions.iloc[0]["Statut"], "Active")
        self.assertEqual(self.rows("SELECT * FROM edt_sessions"), before)

    def test_all_six_legacy_columns_are_backfilled_idempotently(self):
        self.save()
        corrected = self.frame.copy()
        corrected.loc[0, "Salle"] = "B2"
        self.save(corrected)
        before = self.rows("SELECT * FROM edt_sessions")
        self.drop_columns("status", "is_active", "source_hash", "source_documents", "comment", "sessions_count")
        memory.ensure_edt_memory_db(self.db)
        migrated = self.rows("SELECT * FROM edt_versions ORDER BY id")
        memory.ensure_edt_memory_db(self.db)
        self.assertEqual(self.rows("SELECT * FROM edt_versions ORDER BY id"), migrated)
        self.assertEqual(self.rows("SELECT * FROM edt_sessions"), before)
        self.assertEqual(self.rows("SELECT is_active, sessions_count, source_documents FROM edt_versions ORDER BY id"),
                         [(0, 1, '["test.pdf"]'), (1, 1, '["test.pdf"]')])
        self.assertEqual(self.save(corrected)["status"], "duplicate")
        self.assertEqual(self.rows("PRAGMA integrity_check"), [("ok",)])

    def test_missing_active_flag_preserves_explicit_older_active_status(self):
        self.save()
        corrected = self.frame.copy()
        corrected.loc[0, "Salle"] = "B2"
        self.save(corrected)
        with sqlite3.connect(self.db) as conn:
            conn.execute("UPDATE edt_versions SET status=CASE WHEN version_number=1 THEN 'Active' ELSE 'Archivée' END")
        self.drop_columns("is_active")
        memory.ensure_edt_memory_db(self.db)
        self.assertEqual(self.rows("SELECT is_active FROM edt_versions ORDER BY id"), [(1,), (0,)])

    def test_existing_fields_and_comments_are_preserved(self):
        self.save()
        with sqlite3.connect(self.db) as conn:
            conn.execute("UPDATE edt_versions SET comment='Annotation à conserver', status='Validée'")
        before = self.rows("SELECT * FROM edt_versions")
        memory.ensure_edt_memory_db(self.db)
        self.assertEqual(self.rows("SELECT * FROM edt_versions"), before)

    def test_archive_uses_explicit_positional_database(self):
        result = memory.save_version(self.frame, "2026-2027", "Automne", "IAID", "S1", "", self.db)
        self.assertNotIn("changes_error", result)
        self.assertEqual(self.rows("SELECT to_version_id FROM edt_version_change_summary"), [(result["version_id"],)])

    def test_actual_manual_save_handler_reports_created_and_duplicate(self):
        # Execute the application's actual button handler, with UI/network doubles.
        source = Path(__file__).resolve().parents[1] / "app.py"
        tree = ast.parse(source.read_text(encoding="utf-8"))
        handler = next(node for node in ast.walk(tree) if isinstance(node, ast.If)
                       and isinstance(node.test, ast.Call)
                       and any(keyword.arg == "key" and isinstance(keyword.value, ast.Constant)
                               and keyword.value.value == "edt_mem_save" for keyword in node.test.keywords))
        code = compile(ast.Module(body=handler.body, type_ignores=[]), str(source), "exec")
        st = Mock()
        context = {
            "st": st, "subset": self.frame, "academic_year": "2026-2027",
            "period": "Automne", "filiere": "IAID", "niveau": "S1", "comment": "",
            "save_version": lambda *a: memory.save_version(*a, db_path=self.db),
            "sync_edt_changes": Mock(return_value=(False, "Drive indisponible")),
        }
        exec(code, context)
        st.error.assert_not_called()
        self.assertIn("V1", st.success.call_args.args[0])
        st.warning.assert_called_with("Drive indisponible")
        st.rerun.assert_not_called()  # Keep the failure visible immediately.
        exec(code, context)
        st.error.assert_not_called()
        self.assertIn("V1", st.info.call_args.args[0])
        self.assertEqual(self.rows("SELECT COUNT(*) FROM edt_versions"), [(1,)])

    def test_failed_migration_rolls_back_schema_changes(self):
        self.save()
        self.drop_columns("status", "sessions_count")
        original = memory._migrate_version_columns
        def fail_after_upgrade(conn):
            original(conn)
            raise RuntimeError("Simulated interruption")
        with patch.object(memory, "_migrate_version_columns", side_effect=fail_after_upgrade):
            with self.assertRaises(RuntimeError):
                memory.ensure_edt_memory_db(self.db)
        columns = {row[1] for row in self.rows("PRAGMA table_info(edt_versions)")}
        self.assertNotIn("status", columns)
        self.assertNotIn("sessions_count", columns)
        self.assertEqual(len(self.rows("SELECT * FROM edt_sessions")), 1)

    def test_duration_representations_do_not_create_extra_versions(self):
        for value in [2, "2", "2.0", 2.0, "2.00"]:
            with self.subTest(duration=value):
                frame = self.frame.copy()
                frame["Durée"] = [value]
                result = self.save(frame)
                self.assertEqual(result["version_number"], 1)
        self.assertEqual(self.rows("SELECT COUNT(*) FROM edt_versions"), [(1,)])

    def test_integer_duration_survives_hash_column_migration(self):
        frame = self.frame.copy()
        frame["Durée"] = ["2"]
        self.save(frame)
        self.drop_columns("source_hash")
        memory.ensure_edt_memory_db(self.db)
        self.assertEqual(self.save(frame)["status"], "duplicate")

    def test_old_format_hash_is_recognized_from_stored_sessions(self):
        import hashlib
        import json
        frame = self.frame.copy()
        frame["Durée"] = ["2.0"]
        first = self.save(frame)
        legacy_records = [{col: memory._clean(frame.iloc[0][col]) for col in memory.HASH_COLUMNS}]
        legacy_hash = hashlib.sha256(json.dumps(legacy_records, ensure_ascii=False,
            sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        with sqlite3.connect(self.db) as conn:
            conn.execute("UPDATE edt_versions SET source_hash=?", (legacy_hash,))
        result = self.save(frame)
        self.assertEqual(result["status"], "duplicate")
        self.assertEqual(result["version_id"], first["version_id"])
        frame["Durée"] = [2.5]
        self.assertEqual(self.save(frame)["version_number"], 2)


class BootstrapTests(unittest.TestCase):
    def setUp(self):
        self.bootstrap = importlib.import_module("cloud_bootstrap")
        flags = patch.multiple(self.bootstrap, IS_CLOUD=True, _BOOTSTRAPPED=False, _LAST_RESULT={})
        flags.start()
        self.addCleanup(flags.stop)
        self.drive = types.ModuleType("gdrive_sync")
        self.drive.is_connected = Mock(return_value=True)
        self.drive.get_remote_info = Mock(return_value={"id": "test-db"})
        self.drive.download_database = Mock()
        modules = patch.dict(sys.modules, {"gdrive_sync": self.drive})
        modules.start()
        self.addCleanup(modules.stop)

    def test_transient_download_failure_can_be_retried(self):
        self.drive.download_database.side_effect = [OSError("Réseau interrompu"), None]
        self.assertEqual(self.bootstrap.bootstrap_cloud_database()["status"], "error")
        self.assertEqual(self.bootstrap.bootstrap_cloud_database()["status"], "downloaded")
        self.assertEqual(self.drive.download_database.call_count, 2)

    def test_connection_failure_can_recover(self):
        self.drive.is_connected.side_effect = [False, True]
        self.assertEqual(self.bootstrap.bootstrap_cloud_database()["status"], "error")
        self.drive.download_database.assert_not_called()
        self.assertEqual(self.bootstrap.bootstrap_cloud_database()["status"], "downloaded")

    def test_missing_remote_does_not_start_empty_and_can_recover(self):
        self.drive.get_remote_info.side_effect = [None, {"id": "test-db"}]
        self.assertEqual(self.bootstrap.bootstrap_cloud_database()["status"], "error")
        self.drive.download_database.assert_not_called()
        self.assertEqual(self.bootstrap.bootstrap_cloud_database()["status"], "downloaded")

    def test_successful_restore_is_not_repeated_over_local_changes(self):
        self.assertEqual(self.bootstrap.bootstrap_cloud_database()["status"], "downloaded")
        self.drive.download_database.side_effect = AssertionError("Would overwrite local changes")
        self.assertEqual(self.bootstrap.bootstrap_cloud_database()["status"], "downloaded")
        self.drive.download_database.assert_called_once_with(create_local_backup=False)


class SyncTests(unittest.TestCase):
    def setUp(self):
        self.st = types.ModuleType("streamlit")
        self.st.session_state = {}
        self.st.warning = Mock()
        self.st.button = Mock(return_value=False)
        self.st.rerun = Mock()
        self.drive = types.ModuleType("gdrive_sync")
        self.drive.auto_upload_after_change = Mock(return_value=(False, "Drive indisponible"))
        modules = patch.dict(sys.modules, {"streamlit": self.st, "gdrive_sync": self.drive})
        modules.start()
        self.addCleanup(modules.stop)
        self.ui = importlib.import_module("edt_persistence_ui")
        self.verification = importlib.import_module("edt_verification_ui")
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.db = Path(self.directory.name) / "estn.db"
        db_patch = patch.object(self.verification, "DB_PATH", self.db)
        db_patch.start()
        self.addCleanup(db_patch.stop)

    def test_verification_survives_drive_failure_and_warns_after_rerun(self):
        self.verification._save_status(1, 2, "verified", "Contrôlé")
        with sqlite3.connect(self.db) as conn:
            self.assertEqual(conn.execute("SELECT status, note FROM edt_manual_verification").fetchone(),
                             ("verified", "Contrôlé"))
        self.ui.render_edt_sync_status()
        self.ui.render_edt_sync_status()
        self.assertEqual(self.st.warning.call_count, 2)
        self.assertIn("Drive indisponible", self.st.warning.call_args.args[0])

    def test_retry_succeeds_without_repeating_local_save(self):
        self.verification._save_status(1, 2, "verified")
        self.drive.auto_upload_after_change.return_value = (True, "Synchronisée")
        self.st.button.return_value = True
        self.ui.render_edt_sync_status()
        self.assertEqual(self.st.session_state, {})
        self.st.rerun.assert_called_once()
        with sqlite3.connect(self.db) as conn:
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM edt_manual_verification").fetchone()[0], 1)

    def test_unexpected_sync_exception_retains_local_save(self):
        self.drive.auto_upload_after_change.side_effect = RuntimeError("Réseau coupé")
        self.verification._save_status(1, 2, "review")
        self.ui.render_edt_sync_status()
        self.assertIn("Réseau coupé", self.st.warning.call_args.args[0])
        with sqlite3.connect(self.db) as conn:
            self.assertEqual(conn.execute("SELECT status FROM edt_manual_verification").fetchone()[0], "review")

    def test_reset_sync_failure_remains_visible(self):
        self.verification._save_status(1, 2, "verified")
        with patch.object(self.verification, "_load_console", return_value=[{"version_id": 1}]):
            self.verification._reset_year("2026-2027")
        with sqlite3.connect(self.db) as conn:
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM edt_manual_verification").fetchone()[0], 0)
        self.ui.render_edt_sync_status()
        self.st.warning.assert_called_once()


if __name__ == "__main__":
    unittest.main()
