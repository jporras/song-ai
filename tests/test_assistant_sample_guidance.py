import sys
import unittest
from unittest.mock import Mock
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from application.song_service import SongService
from application.model_orchestrator import ModelOrchestrator


class AssistantSampleGuidanceTest(unittest.TestCase):
    def test_changing_question_keeps_project_prefix_and_creative_context(self):
        service = SongService.__new__(SongService)
        project = {'set': {'project_name': 'Tarde', 'description': 'Calma en casa'},
                   'assets': {'instrumental': {'intent': {'instruments': ['piano']}},
                              'melody': {'intent': {'voice': 'suave'}},
                              'lyrics': {'manifest': {'provider': 'mock'},
                                         'intent': {'language': 'Spanish'}, 'content': 'Duerme'}}}
        questions = ['Propone cuatro lineas cantables', 'Incluye Ana María y José']
        prompts = [service._build_gemma_prompt(project, {'question': q}, {}) for q in questions]
        self.assertEqual(*(p.rsplit('Peticion actual que debes responder: ', 1)[0] for p in prompts))
        for question, prompt in zip(questions, prompts):
            self.assertEqual(prompt.count(question), 1)
            self.assertTrue(prompt.endswith(question))
            for required in ('Calma en casa', 'piano', 'suave', 'Spanish', 'sample previo es opcional'):
                self.assertIn(required, prompt)
            self.assertNotIn('Duerme', prompt)

    def test_ace_readiness_and_recommendations_do_not_restore_midi_requirement(self):
        service = SongService.__new__(SongService)
        service.list_drafts = Mock(return_value=[])
        service.list_sets = Mock(return_value=[])
        service.storage = Mock()
        service.storage.list_song_projects.return_value = []
        project = {'samples': [], 'songs': [], 'phase_data': {'intent': {'status': 'saved'}},
                   'set': {'instrumental_id': 'i', 'melody_id': 'm', 'lyrics_id': 'l'}}
        active = {'spec': {'json_spec': {'task_type': 'text2music'}}, 'current_phase': 'LYRICS_GENERATION'}
        result = service._workflow_readiness(project, active)
        self.assertTrue(result['editor_ready_for_production'])
        self.assertNotIn('MIDI', ' '.join(result['recommendations']))
        self.assertIn('sample', ' '.join(result['recommendations']))
        project['set']['melody_id'] = ''
        self.assertFalse(service._workflow_readiness(project, active)['editor_ready_for_production'])

    def test_ace_route_keeps_three_pieces_without_requiring_legacy_midi(self):
        orchestrator = ModelOrchestrator.__new__(ModelOrchestrator)
        context = {'set': {'instrumental_id': 'i', 'melody_id': 'm', 'lyrics_id': 'l'},
                   'phase_data': {'intent': {'status': 'saved'}},
                   'active_professional_project': {'spec': {'json_spec': {'task_type': 'text2music'}}},
                   'professional_next': {'status': 'pending', 'recommendation': 'Revisar sample'}}
        result = orchestrator._validate_sqlite_project_context(context)
        self.assertNotIn('fase:midi', result['missing_items'])
        self.assertEqual(result['next_action'], 'Revisar sample')
        context['set']['lyrics_id'] = ''
        self.assertIn('lyrics_id', orchestrator._validate_sqlite_project_context(context)['missing_items'])

    def test_guidance_offers_optional_sample_with_and_without_active_set(self):
        service = SongService.__new__(SongService)
        project = {"set": {"project_name": "Mi idea", "description": "Una celebracion"},
                   "assets": {name: {"intent": {}, "content": ""}
                              for name in ("instrumental", "melody", "lyrics")}}
        for context in (None, project):
            with self.subTest(active_set=context is not None):
                prompt = service._build_gemma_prompt(context, {"question": "Que sigue?"}, {})
                self.assertIn("sample previo es opcional", prompt)
                self.assertNotIn("sample vigente de ese set", prompt)
                self.assertIn("ficha/request confirmados", prompt)
                self.assertIn("sample mock no acredita produccion real", prompt)
                self.assertNotIn("No presentes sample", prompt)

    def test_initial_guidance_identifies_preparation_and_missing_pieces(self):
        service = SongService.__new__(SongService)
        prompt = service._build_gemma_prompt(None, {}, {"missing": ["letra"]})
        self.assertIn("preparando las tres piezas obligatorias", prompt)
        self.assertIn("instrumental, melodia vocal y letra", prompt)
        self.assertIn("'missing': ['letra']", prompt)
