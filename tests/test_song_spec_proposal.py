import json
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'backend'))
from application.song_spec_proposal import specification_proposal, latest_current_proposal, engine_input_check
from application.model_orchestrator import ModelOrchestrator
from application.song_service import SongService
from unittest.mock import Mock


class SongSpecProposalTest(unittest.TestCase):
    def test_status_tracks_only_the_current_project_request_and_recorded_stage(self):
        service = SongService.__new__(SongService)
        service.storage = Mock()
        service.storage.get_song_project.return_value = {'id': 'song'}
        other = {'task_id': 'old', 'task_type': 'compile_song_spec', 'status': 'completed', 'progress': 100,
                 'payload': {'project_id': 'song', 'client_request_id': 'old-request'}}
        service.storage.list_tasks.return_value = [other]
        self.assertEqual(service.song_specification_proposal_status('song', 'current')['step'], 1)
        current = {'task_id': 'current-task', 'task_type': 'compile_song_spec', 'status': 'running',
                   'progress': 40, 'payload': {'project_id': 'song', 'client_request_id': 'current'}}
        service.storage.list_tasks.return_value = [other, current]
        self.assertEqual(service.song_specification_proposal_status('song', 'current')['step'], 2)
        current['progress'] = 75
        self.assertEqual(service.song_specification_proposal_status('song', 'current')['step'], 3)
        self.assertEqual(service.song_specification_proposal_status('song', 'current')['task_id'], 'current-task')

    def test_model_response_marks_validation_stage_before_compiling(self):
        orchestrator = ModelOrchestrator.__new__(ModelOrchestrator)
        orchestrator.storage = Mock()
        orchestrator.provider_registry = Mock()
        orchestrator._can_run_provider_handoff = Mock(return_value=True)
        orchestrator._technical_prompt = Mock(return_value='prompt')
        orchestrator.provider_registry.technical_with_active_provider.return_value = {
            'summary': json.dumps({'spec': {'bpm': 72, 'voice_style': 'suave'},
                                   'conflicts': [], 'missing_fields': []}), 'mode': 'real'}
        result = orchestrator.build_provider_result('technical', 'compile_song_spec',
            {'_task_id': 'task-current', 'context': self.context()})
        self.assertEqual(result['mode'], 'provider_handoff')
        self.assertEqual(orchestrator.storage.update_task.call_args.kwargs['progress'], 75)

    def test_input_check_reports_structural_conflict_without_claiming_audio_verification(self):
        result = engine_input_check({'task_type': 'lego', 'ace_step_config': 'acestep-v15-turbo'})
        self.assertEqual(result['status'], 'conflict')
        self.assertIn('Base', result['errors'][0])
        self.assertFalse(result['generation_verified'])
        self.assertFalse(result['source_audio_verified'])

    def test_failed_compilation_is_recorded_as_failed_and_assistant_resumes(self):
        orchestrator = ModelOrchestrator.__new__(ModelOrchestrator)
        orchestrator.storage = Mock()
        orchestrator.require_planning_available = Mock()
        orchestrator.select_provider = Mock(return_value={'name': 'qwen', 'capabilities': []})
        orchestrator._can_run_provider_handoff = Mock(return_value=True)
        orchestrator.record_project_event = Mock()
        orchestrator.build_provider_result = Mock(return_value={'mode': 'provider_invalid_output',
            'provider_executed': True, 'summary': 'La ficha se conserva.', 'provider_error': 'JSON incompleto'})
        payload = {'model_role': 'technical', 'task_type': 'compile_song_spec',
                   'context': {'candidate_plan': {'task_type': 'lego', 'ace_step_config': 'acestep-v15-turbo'}}}
        orchestrator.run_handoff(payload)
        sent_context = orchestrator.storage.create_task.call_args.kwargs['payload']['context']
        self.assertIn('Base', sent_context['engine_input_validation']['errors'][0])
        self.assertNotIn('engine_input_validation', payload['context'])
        self.assertEqual(orchestrator.storage.update_task.call_args.kwargs['status'], 'failed')
        self.assertEqual(orchestrator.storage.complete_model_run.call_args.kwargs['status'], 'failed')
        self.assertEqual(orchestrator.record_project_event.call_args.kwargs['status'], 'reactivated')

    def context(self):
        return {'current_spec': {'bpm': 72, 'required_phrase': 'mi hogar'}, 'source_revision_id': 'r1',
                'fields': {'bpm': {'control': 'number'}, 'voice_style': {'control': 'text', 'required_for_spec': True}}}

    def test_proposal_preserves_current_requirements_and_is_not_confirmation(self):
        result = specification_proposal(json.dumps({'spec': {'bpm': 72, 'voice_style': 'suave'},
                  'conflicts': [], 'missing_fields': []}), self.context())
        self.assertEqual(result['spec']['required_phrase'], 'mi hogar')
        self.assertEqual(result['spec']['_provenance']['voice_style']['source'], 'qwen_proposal')
        self.assertFalse(result['active_spec_modified'])
        self.assertEqual(result['user_confirmation_status'], 'pending')

    def test_incomplete_or_changed_values_are_rejected(self):
        for spec in ({'bpm': 72}, {'bpm': 80, 'voice_style': 'suave'}, {'bpm': True, 'voice_style': 'suave'}):
            with self.subTest(spec=spec), self.assertRaises(ValueError):
                specification_proposal(json.dumps({'spec': spec, 'conflicts': [], 'missing_fields': []}), self.context())

    def test_missing_required_decisions_cannot_be_hidden(self):
        result = specification_proposal(json.dumps({'spec': {'bpm': 72, 'voice_style': None},
                   'conflicts': [], 'missing_fields': []}), self.context())
        self.assertIn('voice_style', result['missing_fields'])

    def test_populated_proposal_is_pending_confirmation_not_missing_data(self):
        result = specification_proposal(json.dumps({'spec': {'bpm': 72, 'voice_style': 'suave'},
            'conflicts': [], 'missing_fields': ['voice_style']}), self.context())
        self.assertEqual(result['missing_fields'], [])
        self.assertEqual(result['model_missing_fields'], ['voice_style'])
        self.assertEqual(result['user_confirmation_status'], 'pending')

    def test_bare_field_name_does_not_explain_a_conflict(self):
        with self.assertRaisesRegex(ValueError, 'contradiccion concreta'):
            specification_proposal(json.dumps({'spec': {'bpm': 72, 'voice_style': 'suave'},
                'conflicts': ['voice_style'], 'missing_fields': []}), self.context())

    def test_engine_conflict_is_reported_even_when_model_omits_it(self):
        spec = {'task_type': 'lego', 'ace_step_config': 'acestep-v15-turbo', 'src_audio': 'source.wav',
                'instruction': 'vocals', 'target_tracks': ['vocals']}
        context = {'current_spec': spec, 'source_revision_id': 'r1',
                   'fields': {key: {'control': 'list' if key == 'target_tracks' else 'text'} for key in spec}}
        result = specification_proposal(json.dumps({'spec': spec, 'conflicts': [], 'missing_fields': []}), context)
        self.assertTrue(result['conflicts'])
        self.assertEqual(result['model_conflicts'], [])

    def test_recovery_excludes_other_projects_stale_revisions_and_mock_results(self):
        proposal = {'validation_version': 2, 'source_revision_id': 'r1', 'spec': {'bpm': 72},
                    'coverage': {'covered': 1, 'total': 1}, 'missing_fields': [], 'conflicts': []}
        task = {'task_id': 't1', 'task_type': 'compile_song_spec', 'status': 'completed',
                'created_at': '2026-10-07', 'payload': {'project_id': 'song'},
                'result': {'mode': 'provider_handoff', 'provider_executed': True, 'spec_proposal': proposal}}
        self.assertEqual(latest_current_proposal([task], 'song', 'r1')['task_id'], 't1')
        self.assertIsNone(latest_current_proposal([task], 'other', 'r1'))
        self.assertIsNone(latest_current_proposal([task], 'song', 'r2'))
        task['result']['mode'] = 'mock_handoff'
        self.assertIsNone(latest_current_proposal([task], 'song', 'r1'))
