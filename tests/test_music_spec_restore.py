import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'backend'))
from core.storage import StorageManager
from application.music_spec_restore import RestoreMusicSpec
from application.song_service import SongService
import json


class RestoreTest(unittest.TestCase):
    def test_revalidation_keeps_model_approval_separate_and_accepts_only_valid_inputs(self):
        from application.music_spec_edit import EditMusicSpec
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as folder:
            store = StorageManager(Path(folder))
            song = store.create_song_project('Idea')['id']
            spec = dict(bpm=72,key='Am',language='es',time_signature='4/4',duration_seconds=30,
                        song_type='balada',ace_step_config='acestep-v15-base')
            old = store.upsert_song_spec(song,spec,True,[])
            current = store.upsert_song_spec(song,{**spec,'bpm':90},True,[])
            restored = RestoreMusicSpec(store).execute(song,{'revision_id':current['revision']['revision_id'],
                'source_revision_id':old['revision']['revision_id']})
            saved = EditMusicSpec(store).execute(song,{'revision_id':restored['revision']['revision_id'],
                'values':{'ace_step_config':'acestep-v15-base'}})
            self.assertTrue(saved['revision']['deterministic_valid'])
            self.assertFalse(saved['approved_by_qwen'])
            self.assertEqual(saved['revision']['user_confirmation_status'],'pending')
            # Changing validation evidence alone must create a new revision.
            changed = store.upsert_song_spec(song,saved['json_spec'],False,[],
                technical_review_mode=saved['revision']['technical_review_mode'],user_confirmation_status='pending',
                deterministic_valid=False)
            self.assertNotEqual(saved['revision']['revision_id'],changed['revision']['revision_id'])
            self.assertFalse(changed['revision']['deterministic_valid'])

    def test_restore_creates_pending_revision_and_preserves_history(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as folder:
            store = StorageManager(Path(folder))
            song = store.create_song_project('Idea')['id']
            old = store.upsert_song_spec(song, {'bpm':72}, True, [], user_confirmation_status='confirmed')
            current = store.upsert_song_spec(song, {'bpm':90}, True, [], user_confirmation_status='confirmed')
            request = {'revision_id':current['revision']['revision_id'], 'source_revision_id':old['revision']['revision_id']}
            service = SongService.__new__(SongService)
            service.storage = store
            service.get_professional_specification = lambda song_id: store.get_song_project(song_id)['spec']
            restored = service.restore_music_spec(song, request)
            exported = json.loads((Path(folder)/'projects'/song/'song_spec.json').read_text(encoding='utf-8'))
            self.assertEqual(exported['revision_id'], restored['revision']['revision_id'])
            self.assertEqual(restored['json_spec']['bpm'],72)
            self.assertEqual(restored['revision']['user_confirmation_status'],'pending')
            self.assertFalse(restored['approved_by_qwen'])
            self.assertEqual(len(store.list_song_spec_revisions(song)),3)
            from application.music_spec_edit import EditMusicSpec
            # Restored state is deliberately not automatically eligible for confirmation.
            self.assertFalse(restored['revision']['deterministic_valid'])
            self.assertEqual(store.list_song_spec_revisions(song)[-1]['json_spec'],{'bpm':72})
            with self.assertRaises(ValueError): RestoreMusicSpec(store).execute(song,request)
            request['revision_id']=restored['revision']['revision_id']
            request['source_revision_id']='foreign'
            with self.assertRaises(ValueError): RestoreMusicSpec(store).execute(song,request)
            self.assertEqual(len(store.list_song_spec_revisions(song)),3)
