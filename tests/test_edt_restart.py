"""Real process restarts on disposable SQLite; no remote service is contacted.

Only the database path, Streamlit display state and Drive response are replaced.
Memory, correction, history and verification persistence use application code.
"""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import textwrap
import unittest


ROOT = Path(__file__).resolve().parents[1]
BOOTSTRAP = """
import json
from pathlib import Path
import sqlite3
import sys
import types
import pandas as pd

import app_config
# Bind defaults before importing persistence modules in every fresh interpreter.
app_config.DB_PATH = Path(sys.argv[1])
st = types.ModuleType('streamlit')
st.session_state = {}
sys.modules['streamlit'] = st
drive = types.ModuleType('gdrive_sync')
drive.auto_upload_after_change = lambda: (False, 'Drive fictif indisponible')
sys.modules['gdrive_sync'] = drive
import edt_memory as memory
import edt_verification_ui as verification

def rows(sql):
    with sqlite3.connect(app_config.DB_PATH) as conn:
        return conn.execute(sql).fetchall()

def save(frame):
    return memory.save_version(frame, '2026-2027', 'Automne', 'IAID', 'S1')

def snapshot():
    return {table: rows('SELECT * FROM ' + table + ' ORDER BY id') for table in (
        'edt_timetables', 'edt_versions', 'edt_sessions',
        'edt_version_changes', 'edt_version_change_summary',
        'edt_manual_verification')}
"""

SEED = """
frame = pd.DataFrame([{
    'Jour': 'Lundi', 'Matière': 'Module fictif', 'Type': 'CM',
    'Nom et prénom': 'Enseignant fictif', 'Horaire': '08:30-10:30',
    'Durée': 2.0, 'Groupe': 'G1', 'Salle': 'A1', 'Filière': 'IAID',
    'Niveau': 'S1', 'Année universitaire': '2026-2027',
    'Source PDF': 'document-fictif.pdf', 'Page': '1',
}])
result = save(frame)
assert result['version_number'] == 1
assert 'changes_error' not in result
session_id = rows('SELECT id FROM edt_sessions')[0][0]
verification._save_status(result['version_id'], session_id, 'review', 'Salle à corriger')
print(json.dumps(snapshot(), ensure_ascii=False))
"""

CORRECT = """
# Reload from disk only: no source document or DataFrame survives the first process.
timetables = memory.list_timetables()
assert len(timetables) == 1
version_id = memory.get_version_id(int(timetables.iloc[0]['id']), 1)
frame = memory.load_version_sessions(version_id)
assert frame.iloc[0]['Salle'] == 'A1'
frame.loc[0, 'Salle'] = 'B2'
result = save(frame)
assert result['version_number'] == 2
assert result['changes']['modified_count'] == 1
session_id = rows('SELECT id FROM edt_sessions WHERE version_id=' + str(result['version_id']))[0][0]
verification._save_status(result['version_id'], session_id, 'verified', 'Salle corrigée et contrôlée')
assert st.session_state['edt_pending_sync_error'] == 'Drive fictif indisponible'
print(json.dumps(snapshot(), ensure_ascii=False))
"""


class RestartPersistenceTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.db = Path(directory.name) / 'fictitious.db'

    def run_process(self, script):
        result = subprocess.run(
            [sys.executable, '-c', textwrap.dedent(BOOTSTRAP) + textwrap.dedent(script), str(self.db)],
            cwd=ROOT, capture_output=True, text=True, encoding='utf-8', timeout=30,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return json.loads(result.stdout)

    def test_correction_history_and_verification_survive_fresh_processes(self):
        self.run_process(SEED)
        saved = self.run_process(CORRECT)
        reopened = self.run_process("""
            memory.ensure_edt_memory_db()
            verification.ensure_verification_tables()
            assert st.session_state == {}, 'No previous UI state was carried over'
            assert rows('PRAGMA integrity_check') == [('ok',)]
            assert rows('SELECT version_number, is_active FROM edt_versions ORDER BY version_number') == [(1, 0), (2, 1)]
            assert rows('SELECT salle, source_document, page FROM edt_sessions ORDER BY id') == [
                ('A1', 'document-fictif.pdf', '1'), ('B2', 'document-fictif.pdf', '1')]
            assert rows('SELECT status, note FROM edt_manual_verification ORDER BY id') == [
                ('review', 'Salle à corriger'), ('verified', 'Salle corrigée et contrôlée')]
            console = [item for item in verification._load_console('2026-2027') if not item['missing_timetable']]
            assert len(console) == 1
            assert console[0]['salle'] == 'B2'
            assert console[0]['verification_status'] == 'verified'
            assert console[0]['verified_at']
            history = rows("SELECT changed_fields, old_data_json, new_data_json FROM edt_version_changes WHERE change_type='modified'")
            assert len(history) == 1
            assert json.loads(history[0][0]) == ['Salle']
            assert json.loads(history[0][1])['Salle'] == 'A1'
            assert json.loads(history[0][2])['Salle'] == 'B2'
            current = memory.load_version_sessions(console[0]['version_id'])
            assert save(current)['status'] == 'duplicate'
            assert rows('SELECT COUNT(*) FROM edt_versions') == [(2,)]
            print(json.dumps(snapshot(), ensure_ascii=False))
        """)
        self.assertEqual(reopened, saved, 'Restart and identical save must preserve every stored row')

    def test_legacy_migration_repeated_across_processes_preserves_history(self):
        self.run_process(SEED)
        saved = self.run_process(CORRECT)
        migrated = self.run_process("""
            # Reproduce the six missing legacy metadata columns, using fictitious data only.
            with sqlite3.connect(app_config.DB_PATH) as conn:
                for column in ('status', 'is_active', 'source_hash', 'source_documents', 'comment', 'sessions_count'):
                    conn.execute('ALTER TABLE edt_versions DROP COLUMN ' + column)
            memory.ensure_edt_memory_db()
            assert rows('SELECT version_number, is_active, sessions_count FROM edt_versions ORDER BY id') == [(1, 0, 1), (2, 1, 1)]
            print(json.dumps(snapshot(), ensure_ascii=False))
        """)
        for table in saved:
            if table != 'edt_versions':
                self.assertEqual(migrated[table], saved[table], table)
        repeated = self.run_process("""
            memory.ensure_edt_memory_db()
            verification.ensure_verification_tables()
            assert rows('PRAGMA integrity_check') == [('ok',)]
            active_id = rows('SELECT id FROM edt_versions WHERE is_active=1')[0][0]
            assert save(memory.load_version_sessions(active_id))['status'] == 'duplicate'
            print(json.dumps(snapshot(), ensure_ascii=False))
        """)
        self.assertEqual(repeated, migrated, 'Repeating migration and reload must not change any row')


if __name__ == '__main__':
    unittest.main()
