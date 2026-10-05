import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from application.song_specification_service import SongSpecificationService


class EngineCatalogTest(unittest.TestCase):
    def fields(self, task):
        catalog = SongSpecificationService().catalog({"task_type": task, "repainting_start": 0})
        return {field["id"]: field for group in catalog["groups"] for field in group["fields"]}

    def test_six_actions_and_conditional_inputs(self):
        for task in SongSpecificationService.ENGINE_FIELDS["task_type"]:
            fields = self.fields(task)
            self.assertEqual(fields["src_audio"]["applicable"], task != "text2music")
            self.assertEqual(fields["target_tracks"]["applicable"], task in {"lego", "extract", "complete"})
            self.assertEqual(fields["repainting_end"]["applicable"], task in {"repaint", "lego"})
            self.assertEqual(fields["audio_cover_strength"]["applicable"], task == "cover")
            self.assertEqual(fields["task_type"]["execution_status"], "candidate_plan_only")
        self.assertEqual(self.fields("repaint")["repainting_start"]["value"], 0)

    def test_catalog_does_not_fill_or_confirm_inputs(self):
        spec = {"task_type": "cover"}
        fields = self.fields("cover")
        self.assertTrue(fields["source_artifact_id"]["required_for_task"])
        self.assertIsNone(fields["source_artifact_id"]["value"])
        SongSpecificationService().catalog(spec)
        self.assertEqual(spec, {"task_type": "cover"})
