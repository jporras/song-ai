import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'backend'))
from core.storage import StorageManager
from application.local_intent_assistance import CollectLocalIntent
from application.model_orchestrator import ModelOrchestrator
from application.song_service import SongService


class LocalIntentAssistanceTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.addCleanup(self.folder.cleanup)
        self.store = StorageManager(Path(self.folder.name))
        self.song = self.store.create_song_project('Alma')['id']
        self.saved = self.store.upsert_song_spec(self.song, {
            'title':'Alma', 'creative_brief':'Celebrar su cumpleaños',
            '_provenance':{'creative_brief':{'source':'USER','locked':True}},
            '_retained_intent':{'instrumental':{'instruments':['piano']},
                               'melody':{'voice_style':'cálida'}, 'lyrics':{'theme':'cumpleaños'}}}, False, [])
        self.registry = Mock()
        self.registry.active_providers.return_value = {'interpreter':{'name':'test-gemma','capabilities':[]}}
        self.orchestrator = ModelOrchestrator(self.store, self.registry)
        self.usecase = CollectLocalIntent(self.store, self.orchestrator)

    def test_real_provider_guidance_is_task_evidence_without_spec_or_phase_edits(self):
        self.registry.interpret_with_active_provider.return_value = {
            'mode':'llama_cpp', 'summary':'Revisa instrumental, melodía vocal y letra.',
            'engine_steering':{'contract_sha256':'test-steering'}}
        before = self.store.get_song_project(self.song)
        service = SongService.__new__(SongService)
        service.storage, service.model_orchestrator = self.store, self.orchestrator
        result = service.collect_professional_spec(self.song, {'message':'Quiero más alegría',
            'spec_revision_id':self.saved['revision']['revision_id']})
        self.assertFalse(hasattr(service, 'professional_songs'))
        self.assertEqual(result['handoff']['task']['status'], 'completed')
        self.assertEqual(result['handoff']['result']['engine_steering']['contract_sha256'], 'test-steering')
        self.assertFalse(result['active_spec_modified'])
        self.assertNotIn('qwen', result)
        self.assertEqual(self.store.get_song_project(self.song)['spec'], before['spec'])
        self.assertEqual(self.store.get_song_project(self.song)['current_phase'], before['current_phase'])
        context = json.loads(self.registry.interpret_with_active_provider.call_args.args[0])['context']
        self.assertEqual(context['current_spec']['_retained_intent'],self.saved['json_spec']['_retained_intent'])
        self.assertEqual(context['user_request'], 'Quiero más alegría')
        self.assertFalse((Path(self.folder.name)/'projects'/self.song/'song_spec.json').exists())

    def test_mock_empty_and_provider_error_are_failed_without_overwriting_spec(self):
        for response in ({'mode':'local_mock','summary':'Ejemplo'}, {'mode':'llama_cpp','summary':''}):
            self.registry.interpret_with_active_provider.return_value = response
            result = self.usecase.execute(self.song, {'message':'Con guitarra'})
            self.assertEqual(result['handoff']['task']['status'], 'failed')
            self.assertEqual(self.store.get_song_project(self.song)['spec'], self.saved)
        self.registry.interpret_with_active_provider.side_effect = TimeoutError('timeout')
        result = self.usecase.execute(self.song, {'message':'Con guitarra'})
        self.assertEqual(result['handoff']['result']['mode'], 'provider_error')
        self.assertEqual(result['handoff']['task']['status'], 'failed')
        self.assertEqual(self.store.get_song_project(self.song)['spec'], self.saved)

    def test_invalid_request_or_stale_revision_creates_no_task(self):
        for payload in ({'message':''}, {'message':12}, {'message':'x'*8193},
                        {'message':'Con guitarra','spec_revision_id':'stale'}):
            with self.assertRaises(ValueError):
                self.usecase.execute(self.song, payload)
        self.assertEqual(self.store.list_tasks(), [])
        self.registry.interpret_with_active_provider.assert_not_called()

    def test_project_without_spec_stays_in_preparation(self):
        song = self.store.create_song_project('Nueva idea')['id']
        self.registry.interpret_with_active_provider.return_value = {'mode':'llama_cpp','summary':'Describe la ocasión.'}
        self.usecase.execute(song, {'message':'Una canción para mi familia'})
        context = json.loads(self.registry.interpret_with_active_provider.call_args.args[0])['context']
        self.assertTrue(context['preparation_without_spec'])
        self.assertIsNone(context['source_revision_id'])
        self.assertFalse(self.store.get_song_project(song).get('spec'))
