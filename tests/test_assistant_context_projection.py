import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from application.assistant_context_projection import assistant_context, specification_context
from application.assistant_request_policy import conversation_state


class AssistantContextTest(unittest.TestCase):
    def test_conversation_keeps_current_spec_and_authority_without_historical_payloads(self):
        current = {'voice_style': 'soft female lead', 'bpm': 72,
                   '_provenance': {'voice_style': {'origin': 'USER', 'confirmation': 'confirmed',
                                                  'note': 'history' * 2000}},
                   '_editor_phases': {'voice': 'history' * 2000}}
        project = {'id': 'song-alma', 'title': 'Alma', 'status': 'waiting_user_input',
                   'spec': {'revision': {'revision_id': 'r1', 'user_confirmation_status': 'pending'},
                            'json_spec': current},
                   'artifacts': [{'metadata': {'log': 'history' * 2000}}]}
        state = conversation_state({'professional_project': project, 'missing': ['ficha']})
        summary = state['professional_project']['spec']
        self.assertEqual(summary['json_spec']['voice_style'], 'soft female lead')
        self.assertEqual(summary['field_authority']['voice_style'],
                         {'origin': 'USER', 'confirmation': 'confirmed'})
        self.assertEqual(summary['revision']['user_confirmation_status'], 'pending')
        self.assertNotIn('artifacts', state['professional_project'])
        self.assertNotIn('_editor_phases', summary['json_spec'])
        self.assertLess(len(str(state)), 700)
        self.assertIn('_editor_phases', current)

    def test_spec_context_keeps_current_revision_and_sources_without_duplicate_phase_bodies(self):
        original = {'revision':{'revision_id':'r1'},'json_spec':{'bpm':97,'required_phrases':['Alma'],
            '_provenance':{'bpm':{'locked':True,'source':'USER'}}, '_editor_phases':{'intent':{'bpm':97}},
            '_retained_intent':{'voice_details':{'breaths':20}},
            '_lyrics_document':{'sha256':'abc','markdown':'Duerme, Alma.','sections':[]}}}
        projected = specification_context(original)
        self.assertEqual(projected['revision'],original['revision'])
        self.assertEqual(projected['json_spec']['bpm'],97)
        self.assertEqual(projected['json_spec']['_provenance'],original['json_spec']['_provenance'])
        self.assertNotIn('_editor_phases',projected['json_spec'])
        self.assertEqual(projected['json_spec']['_lyrics_document']['sha256'],'abc')
        self.assertIn('_editor_phases',original['json_spec'])
    def test_current_wishes_sources_and_revision_are_preserved_without_mutation(self):
        original = {"spec": {"revision": "r1", "required_phrases": ["hogar"], "voice_style": "suave"},
                    "assets": {"manifest": {"checksum": "abc"}, "intent": {"mood": "sereno"}},
                    "events": [{"phase": "intent", "status": "saved", "payload": {"log": "x" * 500}} for _ in range(20)]}
        projected = assistant_context(original)
        self.assertEqual(projected["spec"], original["spec"])
        self.assertEqual(projected["assets"], original["assets"])
        self.assertEqual(projected["history_event_count"], 20)
        self.assertEqual(len(projected["recent_events"]), 3)
        self.assertEqual(len(original["events"]), 20)
        projected["spec"]["voice_style"] = "otra"
        self.assertEqual(original["spec"]["voice_style"], "suave")
