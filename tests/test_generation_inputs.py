import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from models.generation_inputs import musical_phase_inputs


class GenerationInputsTest(unittest.TestCase):
    def test_persistence_metadata_does_not_change_musical_inputs(self):
        record = {"data": {"musicPlan": {"bpm": 100}}, "updated_at": "before", "status": "pending"}
        revised = {**record, "updated_at": "after", "status": "completed", "change_source": "AI"}
        self.assertEqual(musical_phase_inputs({"music-plan": record}),
                         musical_phase_inputs({"music-plan": revised}))

    def test_known_navigation_fields_are_excluded_without_mutating_records(self):
        records = {"production": {"data": {"production": {"productionProjectId": "id", "productionGlobalStatus": "done"}}},
                   "lyrics": {"data": {"lyricsEditor": {"path": "file", "content": "Mi letra"}}}}
        result = musical_phase_inputs(records)
        self.assertNotIn("production", result)
        self.assertEqual(result["lyrics"]["lyricsEditor"], {"content": "Mi letra"})
        self.assertEqual(records["lyrics"]["data"]["lyricsEditor"]["path"], "file")

    def test_unknown_and_musical_fields_are_preserved(self):
        for phase, data in (("voice", {"voice": {"vibrato": 2}}),
                            ("production", {"production": {"provider": "future"}}),
                            ("future", {"new_parameter": 1})):
            self.assertEqual(musical_phase_inputs({phase: {"data": data}}), {phase: data})
