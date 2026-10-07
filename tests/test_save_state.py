"""Real temporary SQLite and Streamlit checks for editor save feedback."""
import io
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import textwrap
import unittest
from unittest.mock import patch

import pandas as pd
from edt_memory import ensure_edt_memory_db, save_version, load_version_sessions
from edt_parser import build_intervenants_dataframe, xlsx_bytes
from edt_save_state import saved_state


def fixture():
    return pd.DataFrame([{'Jour':'Lundi', 'Matière':'Module fictif', 'Type':'CM',
        'Nom et prénom':'Enseignant Test', 'Horaire':'08:30-10:30', 'Durée':2.0,
        'Groupe':'G1', 'Salle':'A1', 'Filière':'TEST', 'Niveau':'S1',
        'Année universitaire':'2026-2027', 'Source PDF':'fictif.pdf', 'Page':'1'}])


class SaveStateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.db = Path(self.tmp.name) / 'test.db'
        ensure_edt_memory_db(self.db)
        self.frame = fixture()
        self.context = ('2026-2027', 'Automne', 'TEST', 'S1')

    def state(self, frame=None, context=None):
        return saved_state(self.frame if frame is None else frame,
                           *(context or self.context), db_path=self.db)

    def save(self, frame=None):
        return save_version(self.frame if frame is None else frame, *self.context, db_path=self.db)

    def test_correction_save_reopen_export_and_subsequent_edit(self):
        self.assertEqual(self.state()['status'], 'unsaved')
        first = self.save()
        self.assertEqual(self.state(), {'status':'saved', 'version_number':1, 'active':True})
        corrected = self.frame.copy()
        corrected.loc[0, 'Salle'] = 'B2'
        self.assertEqual(self.state(corrected)['status'], 'unsaved')
        second = self.save(corrected)
        reopened = load_version_sessions(second['version_id'], self.db)
        self.assertEqual(self.state(reopened)['version_number'], 2)
        exported = pd.read_excel(io.BytesIO(xlsx_bytes(build_intervenants_dataframe(reopened.to_dict('records')), reopened)), sheet_name=1)
        self.assertEqual(exported.iloc[0]['Salle'], 'B2')
        self.assertFalse(self.state()['active'])
        self.assertEqual(self.save()['status'], 'duplicate')
        self.assertFalse(self.state()['active'])
        corrected.loc[0, 'Salle'] = 'C3'
        self.assertEqual(self.state(corrected)['status'], 'unsaved')
        self.assertEqual(load_version_sessions(first['version_id'], self.db).iloc[0]['Salle'], 'A1')

    def test_context_is_not_shared_between_timetables_years_or_periods(self):
        self.save()
        for context in [('2027-2028','Automne','TEST','S1'),
                        ('2026-2027','Printemps','TEST','S1'),
                        ('2026-2027','Automne','OTHER','S1'),
                        ('2026-2027','Automne','TEST','S2')]:
            with self.subTest(context=context):
                self.assertEqual(self.state(context=context)['status'], 'unsaved')

    def test_addition_deletion_empty_and_incomplete(self):
        second = self.frame.copy()
        second.loc[0, 'Salle'] = 'B2'
        both = pd.concat([self.frame, second], ignore_index=True)
        self.save(both)
        self.assertEqual(self.state()['status'], 'unsaved')
        third = second.copy()
        third.loc[0, 'Salle'] = 'C3'
        self.assertEqual(self.state(pd.concat([both, third]))['status'], 'unsaved')
        self.assertEqual(self.state(self.frame.iloc[:0])['status'], 'empty')
        self.assertEqual(self.state(context=('', 'Automne','TEST','S1'))['status'], 'incomplete')

    def test_database_error_is_unknown_and_never_creates_database(self):
        self.save()
        with patch('edt_save_state.sqlite3.connect', side_effect=sqlite3.OperationalError('blocked')):
            self.assertEqual(self.state()['status'], 'unknown')
        missing = Path(self.tmp.name) / 'missing.db'
        self.assertEqual(saved_state(self.frame, *self.context, db_path=missing)['status'], 'unknown')
        self.assertFalse(missing.exists())

    def test_comparison_is_read_only_and_normalizes_like_save(self):
        self.save()
        before = self.db.read_bytes()
        normalized = self.frame.copy()
        normalized['Durée'] = '2'
        normalized['Année universitaire'] = ''
        self.assertEqual(self.state(normalized)['status'], 'saved')
        self.assertEqual(self.db.read_bytes(), before)

    def test_app_feedback_after_edit_save_rerun_and_failure(self):
        root = Path(self.tmp.name)
        source = Path(__file__).resolve().parents[1]
        for file in source.glob('*.py'):
            shutil.copy2(file, root / file.name)
        shutil.copy2(Path(__file__), root / 'fixture_test.py')
        app = textwrap.dedent('''
            from unittest.mock import patch
            import runpy
            import streamlit as st
            import edt_parser
            from fixture_test import fixture
            class Upload:
                name = 'fictif.pdf'
                def getvalue(self): return b'fake'
            original_editor = st.data_editor
            def editor(data, *args, **kwargs):
                if kwargs.get('key') == 'details_editor':
                    data = data.copy()
                    data['Salle'] = st.session_state.get('test_room', 'A1')
                return original_editor(data, *args, **kwargs)
            def save(*args, **kwargs):
                if st.session_state.get('test_fail'):
                    raise RuntimeError('Échec simulé')
                return original_save(*args, **kwargs)
            from edt_memory import save_version as original_save
            with patch('streamlit.file_uploader', side_effect=lambda label, **kw: [Upload()] if kw.get('accept_multiple_files') else None), patch('streamlit.data_editor', side_effect=editor), patch('edt_parser.extract_sessions_from_pdf_bytes', return_value=(fixture().to_dict('records'), [])), patch('agent_edt.ollama_status', return_value=(False, 'Simulation hors ligne')), patch('edt_memory.save_version', side_effect=save):
                runpy.run_path('app.py', run_name='__main__')
        ''')
        (root / 'harness.py').write_text(app, encoding='utf-8')
        script = textwrap.dedent('''
            from streamlit.testing.v1 import AppTest
            at = AppTest.from_file('harness.py', default_timeout=30).run()
            at.radio(key='main_module').set_value('📅 Emplois du temps').run()
            assert not at.exception, at.exception
            assert any('Séances enregistrées localement' in x.value for x in at.success)
            at.session_state['test_room'] = 'B2'
            at.run()
            assert not at.exception, at.exception
            assert sum('non enregistrées pour cet emploi' in x.value for x in at.warning) == 3
            at.button(key='edt_mem_save').click().run()
            assert not at.exception, at.exception
            assert sum('Séances enregistrées localement : V2' in x.value for x in at.success) == 3
            at.run()
            assert sum('Séances enregistrées localement : V2' in x.value for x in at.success) == 3
            at.session_state['test_room'] = 'C3'
            at.session_state['test_fail'] = True
            at.button(key='edt_mem_save').click().run()
            assert not at.exception, at.exception
            assert any('Enregistrement impossible' in x.value for x in at.error)
            assert sum('non enregistrées pour cet emploi' in x.value for x in at.warning) == 3
            at.session_state['test_room'] = 'A1'
            at.run()
            assert sum('V1 (archivée, non active)' in x.value for x in at.info) == 3
        ''')
        result = subprocess.run([sys.executable, '-c', script], cwd=root,
                                capture_output=True, text=True, timeout=100)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
