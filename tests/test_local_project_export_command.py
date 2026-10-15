import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'backend'))
from core.storage import StorageManager
from application.song_service import SongService


class LocalExportCommandTests(unittest.TestCase):
    def test_confirmation_and_set_fail_before_export_or_new_events(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as folder:
            store = StorageManager(Path(folder))
            song = store.create_song_project('Alma')['id']
            service = SongService.__new__(SongService)
            service.storage, service.local_project_exports = store, Mock()
            before = store.list_song_project_events(song)
            with self.assertRaisesRegex(ValueError,'Completa la ficha'):
                service.export_professional_song(song)
            store.upsert_song_spec(song, {'title':'Alma'}, False, [], deterministic_valid=True,
                                   user_confirmation_status='pending')
            with self.assertRaisesRegex(ValueError,'confirma la ficha'):
                service.export_professional_song(song)
            store.upsert_song_spec(song, {'title':'Alma'}, False, [], deterministic_valid=True,
                                   user_confirmation_status='confirmed')
            with self.assertRaisesRegex(ValueError,'set valido'):
                service.export_professional_song(song)
            service.local_project_exports.export.assert_not_called()
            self.assertEqual(store.list_song_project_events(song),before)

    def test_validated_export_uses_local_service_and_preserves_sqlite_spec(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as folder:
            store = StorageManager(Path(folder))
            song = store.create_song_project('Alma')['id']
            saved = store.upsert_song_spec(song, {'title':'Alma'}, False, [], deterministic_valid=True,
                                          user_confirmation_status='confirmed')
            directory = store.data_dir/'projects'/song
            directory.mkdir(parents=True,exist_ok=True)
            for format_ in ('wav','mp3','flac'):
                (directory/f'final_song.{format_}').write_bytes(b'fixture')
            service = SongService.__new__(SongService)
            service.storage, service.local_project_exports = store, Mock()
            service.local_project_exports.export.return_value = {'fixture':'export_dispatched'}
            # Only orchestration is exercised here; this double is not audio/sample evidence.
            with patch('application.local_project_export_command.FinalProductionGate.require_for_project',return_value={}):
                self.assertEqual(service.export_professional_song(song), {'fixture':'export_dispatched'})
                (directory/'final_song.flac').unlink()
                with self.assertRaisesRegex(ValueError,'final_song.flac'):
                    service.export_professional_song(song)
            service.local_project_exports.export.assert_called_once_with(song)
            self.assertEqual(store.get_song_project(song)['spec'],saved)
            events = [e for e in store.list_song_project_events(song) if e['phase']=='EXPORT']
            self.assertEqual(len(events),1)
