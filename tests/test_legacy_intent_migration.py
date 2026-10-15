import sys
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'backend'))
from core.storage import StorageManager
from application.legacy_intent_migration import LegacyIntentMigration


class MigrationTest(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.addCleanup(self.folder.cleanup)
        self.store = StorageManager(Path(self.folder.name))
        self.song = self.store.create_song_project('Idea', user_id='set:legacy')['id']
        self.original = self.store.upsert_song_spec(self.song, {'bpm':97,'emotion':'triste'},
            True, [], user_confirmation_status='confirmed')
        self.phases = {'intent': {'updated_at':'2026-10-07', 'data': {'intent': {
            'bpm':72, 'key':'Am', 'language':'Spanish', 'instruments':['piano'],
            'description':'Despedida íntima'}}}, 'midi': {'data': {'notes': ['legacy']}}}
        self.store.get_indexed_set = lambda set_id: {'set_id':'legacy'}
        self.store.list_project_phase_data = lambda set_id: deepcopy(self.phases)
        self.migration = LegacyIntentMigration(self.store)

    def test_preview_preserves_current_values_and_all_source_context(self):
        proposal = self.migration.preview(self.song)
        self.assertNotIn('bpm',proposal['additions'])
        self.assertEqual(proposal['conflicts'][0]['current'],97)
        self.assertEqual(proposal['additions']['key']['value'],'Am')
        self.assertIn('midi',proposal['source_context']['phase_data'])
        self.assertEqual(self.store.get_song_project(self.song)['spec']['revision']['revision_id'],
                         self.original['revision']['revision_id'])

    def test_apply_creates_pending_revision_with_sources_and_keeps_history(self):
        proposal=self.migration.preview(self.song)
        result=self.migration.apply(self.song, {'revision_id':proposal['revision_id'],
            'source_sha256':proposal['source_sha256'],'fields':['key','instruments']})
        self.assertEqual(result['json_spec']['bpm'],97)
        self.assertEqual(result['json_spec']['key'],'Am')
        self.assertEqual(result['revision']['user_confirmation_status'],'pending')
        self.assertEqual(result['json_spec']['_provenance']['key']['source'],'historical_inference')
        self.assertEqual(result['json_spec']['_provenance']['key']['sources'][0]['phase'],'intent')
        self.assertEqual(self.store.list_tasks()[0]['result']['proposal']['source_sha256'],proposal['source_sha256'])
        self.assertEqual(self.original['json_spec'],{'bpm':97,'emotion':'triste'})

    def test_conflicts_and_stale_sources_are_rejected(self):
        proposal=self.migration.preview(self.song)
        request={'revision_id':proposal['revision_id'],'source_sha256':proposal['source_sha256'],'fields':['bpm']}
        with self.assertRaises(ValueError):self.migration.apply(self.song,request)
        self.phases['intent']['data']['intent']['key']='C Major'
        request['fields']=['key']
        with self.assertRaisesRegex(ValueError,'Cambió'):self.migration.apply(self.song,request)

    def test_disagreement_between_phases_is_not_silently_resolved(self):
        self.phases['music-plan']={'data':{'musicPlan':{'key':'C Major'}}}
        proposal=self.migration.preview(self.song)
        self.assertNotIn('key',proposal['additions'])
        self.assertTrue(any(c['field']=='key' and c['resolution']=='needs_review' for c in proposal['conflicts']))


if __name__=='__main__':unittest.main()
