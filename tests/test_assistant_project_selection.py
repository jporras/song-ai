import sys
import unittest
from pathlib import Path
from unittest.mock import Mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'backend'))
from application.assistant_project_selection import resolve_assistant_song
from application.song_service import SongService
from application.assistant_request_policy import conversation_state


class AssistantProjectSelectionTest(unittest.TestCase):
    def test_song_derives_its_own_set_and_rejects_foreign_or_missing_context(self):
        store = Mock()
        song = {'id': 'isabella', 'user_id': 'set:isabella-set'}
        store.get_song_project.return_value = song
        self.assertEqual(resolve_assistant_song(store, 'isabella', ''), ('isabella-set', song))
        self.assertEqual(resolve_assistant_song(store, 'isabella', 'isabella-set'), ('isabella-set', song))
        with self.assertRaises(ValueError): resolve_assistant_song(store, 'isabella', 'alma-set')
        store.get_song_project.return_value = None
        with self.assertRaises(ValueError): resolve_assistant_song(store, 'missing', '')
        store.get_song_project.return_value = {'id': 'initial', 'user_id': 'local-user'}
        self.assertEqual(resolve_assistant_song(store, 'initial', '')[0], '')
        with self.assertRaises(ValueError): resolve_assistant_song(store, 'initial', 'unrelated')

    def test_set_only_selection_does_not_choose_an_unrelated_song(self):
        store = Mock()
        self.assertEqual(resolve_assistant_song(store, '', 'alma-set'), ('alma-set', None))
        store.get_song_project.assert_not_called()

    def test_mismatch_stops_before_models_and_default_set_selection(self):
        service = SongService.__new__(SongService)
        service.storage = Mock()
        service.storage.get_song_project.return_value = {'id': 'isabella', 'user_id': 'set:isabella-set'}
        service.model_orchestrator = Mock()
        service.model_orchestrator.active_audio_task.return_value = None
        service.list_sets, service.get_project, service._run_gemma_or_fallback = Mock(), Mock(), Mock()
        with self.assertRaises(ValueError):
            service.gemma_assistant({'song_id': 'isabella', 'set_id': 'alma-set'})
        service.list_sets.assert_not_called()
        service.get_project.assert_not_called()
        service._run_gemma_or_fallback.assert_not_called()
        service.model_orchestrator.run_handoff.assert_not_called()

    def test_catalog_context_survives_prompt_projection_without_authorizing_actions(self):
        service = SongService.__new__(SongService)
        service.storage = Mock()
        tools = service.music_tool_catalog()
        self.assertEqual(len(tools['tools']), 12)
        state = conversation_state({'music_tools': tools})
        prompt = service._build_gemma_prompt(None, {}, state)
        self.assertIn('spec.reject_proposal', prompt)
        self.assertIn('automatic_execution', prompt)
        self.assertTrue(all(tool['model_can_execute'] is False for tool in tools['tools']))
