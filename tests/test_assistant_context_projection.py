import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from application.assistant_context_projection import assistant_context, specification_context


class AssistantContextTest(unittest.TestCase):
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
