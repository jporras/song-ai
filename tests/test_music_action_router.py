import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'backend'))
from application.music_action_router import MusicActionRouter, MusicToolRegistry, MusicTool, local_music_tools
from application.song_service import SongService
from core.storage import StorageManager


class MusicActionRouterTest(unittest.TestCase):
    def setUp(self):
        self.store = Mock()
        self.store.get_song_project.return_value = {'spec': {'revision': {'revision_id': 'r1'}}}
        self.handler = Mock(return_value={'done': True})
        self.registry = MusicToolRegistry()
        self.registry.register(MusicTool('spec.edit', 'Guardar', 'edit', {'values': dict}, ('values',)), self.handler)
        self.router = MusicActionRouter(self.store, self.registry)
        self.request = {'tool_id': 'spec.edit', 'revision_id': 'r1', 'user_authorized': True, 'parameters': {'values': {'bpm': 97}}}

    def test_invalid_or_ambiguous_requests_fail_before_dispatch_or_event(self):
        for changes in ({'tool_id': 'invented'}, {'user_authorized': False}, {'user_authorized': 'true'},
                        {'revision_id': 'r0'}, {'parameters': {'project_id': 'other'}},
                        {'parameters': {'values': []}}, {'parameters': {}}, {'targets': ['one', 'two']}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.router.execute('one', {**self.request, **changes})
        self.handler.assert_not_called()
        self.store.create_song_event.assert_not_called()

    def test_authorized_dispatch_records_source_and_does_not_mutate_request(self):
        def action(song, revision, params):
            params['values']['bpm'] = 120
            return 'done'
        self.handler.side_effect = action
        result = self.router.execute('one', self.request)
        self.assertEqual(result['source_revision_id'], 'r1')
        self.assertEqual(self.request['parameters']['values']['bpm'], 97)
        event = self.store.create_song_event.call_args.kwargs['payload']['music_action']
        self.assertEqual(event['parameters']['values']['bpm'], 97)
        self.assertFalse(event['result_quality_verified'])

    def test_missing_project_and_handler_failure_do_not_publish_success(self):
        self.store.get_song_project.return_value = None
        with self.assertRaises(ValueError): self.router.execute('missing', self.request)
        self.store.get_song_project.return_value = {'spec': {'revision': {'revision_id': 'r1'}}}
        self.handler.side_effect = ValueError('native validation')
        with self.assertRaisesRegex(ValueError, 'native validation'): self.router.execute('one', self.request)
        self.store.create_song_event.assert_not_called()

    def test_duplicate_registration_and_catalog_serialization(self):
        with self.assertRaises(ValueError):
            self.registry.register(MusicTool('spec.edit', 'Duplicada', 'edit', {}), Mock())
        catalog = json.loads(json.dumps(self.registry.catalog()))
        self.assertTrue(catalog[0]['requires_user_authorization'])
        self.assertFalse(catalog[0]['model_can_execute'])

    def test_each_registered_operation_calls_only_its_existing_handler(self):
        service = Mock()
        params = {
            'spec.read': {}, 'spec.propose': {}, 'spec.edit': {'values': {'bpm': 97}},
            'spec.confirm': {}, 'spec.reject_proposal': {'task_id': 'proposal'}, 'spec.restore': {'source_revision_id': 'old'}, 'plan.read': {},
            'plan.prepare': {'lyrics': 'Texto'}, 'plan.approve': {'plan_id': 'plan', 'plan_sha256': 'hash', 'lyrics_confirmed': True},
            'candidate.start': {'plan_sha256': 'hash', 'exploratory_audio_authorized': True},
            'candidate.read': {'task_id': 'job'}, 'candidate.cancel': {'task_id': 'job'}}
        methods = ['get_professional_specification', 'propose_song_specification', 'edit_music_spec',
                   'confirm_professional_specification', 'reject_song_spec_proposal', 'restore_music_spec', 'latest_ace_step_plan',
                   'prepare_ace_step_plan', 'approve_ace_step_plan', 'ace_candidate_jobs.start',
                   'ace_candidate_jobs.get', 'ace_candidate_jobs.cancel']
        registry = local_music_tools(service)
        for tool_id, method in zip(params, methods):
            service.reset_mock()
            MusicActionRouter(self.store, registry).execute('one', {**self.request, 'tool_id': tool_id, 'parameters': params[tool_id]})
            handler = service
            for name in method.split('.'): handler = getattr(handler, name)
            self.assertEqual(handler.call_count, 1, tool_id)
            self.assertEqual(handler.call_args.args[0], 'one')
        self.assertIn('bpm', next(t for t in registry.catalog() if t['id'] == 'spec.edit')['control_ids'])

    def test_real_sqlite_edit_range_revision_isolation_and_audit(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as folder:
            store = StorageManager(Path(folder))
            song = store.create_song_project('Alma')['id']
            other = store.create_song_project('Isabella')['id']
            record = store.upsert_song_spec(song, dict(bpm=72, key='Am', language='es', time_signature='4/4',
                duration_seconds=120, song_type='balada', emotion='calma', ace_step_config='acestep-v15-base'), False, [])
            service = SongService.__new__(SongService)
            service.storage = store
            request = {**self.request, 'revision_id': record['revision']['revision_id']}
            with self.assertRaises(ValueError): service.execute_music_action(other, request)
            with self.assertRaises(ValueError):
                service.execute_music_action(song, {**request, 'parameters': {'values': {'bpm': 301}}})
            self.assertEqual(store.get_song_project(song)['spec'], record)
            service.execute_music_action(song, request)
            updated = store.get_song_project(song)['spec']
            self.assertEqual(updated['json_spec']['bpm'], 97)
            self.assertEqual(updated['revision']['user_confirmation_status'], 'pending')
            with self.assertRaises(ValueError): service.execute_music_action(song, request)
            audit = [e['payload']['music_action'] for e in store.list_song_project_events(song) if 'music_action' in e['payload']]
            self.assertEqual(len(audit), 1)
            self.assertEqual(audit[0]['source_revision_id'], request['revision_id'])
            self.assertIsNone(store.get_song_project(other).get('spec'))
