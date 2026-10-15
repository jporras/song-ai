import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'backend'))
from core.storage import StorageManager
from application.song_service import SongService


class RejectSongSpecProposalTest(unittest.TestCase):
    def test_reject_persists_without_spec_change_and_survives_reload(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as folder:
            store = StorageManager(Path(folder))
            song = store.create_song_project('Alma')['id']
            other = store.create_song_project('Isabella')['id']
            spec = store.upsert_song_spec(song, {'title': 'Alma'}, False, [])
            revision = spec['revision']['revision_id']
            store.create_task('proposal', 'compile_song_spec', 'technical', {'project_id': song}, 'Fixture')
            store.update_task('proposal', 'completed', 100, 'Fixture', {'mode': 'provider_handoff',
                'provider_executed': True, 'spec_proposal': {'validation_version': 2, 'source_revision_id': revision,
                'coverage': {'covered': 1, 'total': 1}, 'missing_fields': [], 'conflicts': [], 'spec': {'title': 'Alma'}}})
            service = SongService.__new__(SongService)
            service.storage = store
            self.assertEqual(service.get_professional_specification(song)['technical_proposal']['task_id'], 'proposal')
            request = {'tool_id': 'spec.reject_proposal', 'revision_id': revision, 'user_authorized': True,
                       'parameters': {'task_id': 'foreign'}}
            with self.assertRaises(ValueError): service.execute_music_action(song, request)
            with self.assertRaises(ValueError): service.execute_music_action(other, {**request, 'parameters': {'task_id': 'proposal'}})
            service.execute_music_action(song, {**request, 'parameters': {'task_id': 'proposal'}})
            service.storage = StorageManager(Path(folder))
            self.assertIsNone(service.get_professional_specification(song)['technical_proposal'])
            self.assertEqual(service.storage.get_song_project(song)['spec'], spec)
            self.assertEqual(service.storage.list_tasks()[0]['status'], 'completed')
