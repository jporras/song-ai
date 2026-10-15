import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'backend'))
from core.storage import StorageManager
from application.music_spec_revision_service import MusicSpecRevisionService
from application.song_service import SongService


class LocalRevisionsTest(unittest.TestCase):
    def test_local_confirmation_without_historical_service_preserves_evidence(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as folder:
            store=StorageManager(Path(folder))
            song=store.create_song_project('Idea')['id']
            saved=store.upsert_song_spec(song,{'bpm':72},False,[],deterministic_valid=True,
                user_confirmation_status='pending')
            service=SongService.__new__(SongService)
            service.storage=store
            with patch('application.professional_song_service.ProfessionalSongService', side_effect=AssertionError('legacy dependency')):
                result=service.confirm_professional_specification(song,{'revision_id':saved['revision']['revision_id']})
            self.assertEqual(result['spec']['revision']['user_confirmation_status'],'confirmed')
            self.assertTrue(result['spec']['revision']['deterministic_valid'])
            self.assertFalse(result['spec']['approved_by_qwen'])
            with self.assertRaises(ValueError):
                MusicSpecRevisionService(store).confirm_song_specification(song,{'revision_id':saved['revision']['revision_id']})
            self.assertEqual(len(store.list_song_spec_revisions(song)),2)
