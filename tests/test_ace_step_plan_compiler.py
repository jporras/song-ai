import sys
import unittest
from copy import deepcopy
from pathlib import Path
from unittest.mock import Mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from application.ace_step_plan_compiler import AceStepPlanCompiler, PreviewAceStepPlan


class AceStepPlanCompilerTest(unittest.TestCase):
    def test_previews_all_six_modes_without_authorizing_execution(self):
        for task in ("text2music", "cover", "repaint", "lego", "extract", "complete"):
            with self.subTest(task=task):
                record = deepcopy(self.record)
                record["json_spec"].update(task_type=task, ace_step_config="acestep-v15-base",
                    src_audio="source.wav", instruction="guitar", target_tracks=["guitar"],
                    repainting_start=1, repainting_end=3)
                plan = AceStepPlanCompiler().compile(record, "" if task == "extract" else "Letra")
                self.assertEqual(plan["payload"]["task_type"], task)
                self.assertFalse(plan["ready_for_execution"])
                if task != "text2music":
                    self.assertEqual(plan["payload"]["src_audio"], "source.wav")
                    self.assertIn("source_artifact_verification", plan["pending"])

    def setUp(self):
        self.record = {"revision": {"revision_id": "r1", "user_confirmation_status": "confirmed", "deterministic_valid": True},
                       "missing_fields": [], "json_spec": {"bpm": 72, "key": "C major", "time_signature": "6/8",
                       "language": "Spanish", "duration_seconds": 120, "song_type": "balada", "emotion": "tierna",
                       "voice_style": "voz suave", "instruments": ["piano"], "required_phrases": ["Isabella"],
                       "future_requirement": {"melody_exact": True}}}

    def test_maps_handler_fields_and_preserves_all_requirements_without_authorizing_generation(self):
        original = deepcopy(self.record)
        plan = AceStepPlanCompiler().compile(self.record, "[Verse]\nIsabella, duerme")
        self.assertEqual(plan["payload"]["vocal_language"], "es")
        self.assertEqual(plan["payload"]["time_signature"], "6")
        self.assertEqual(plan["payload"]["key_scale"], "C major")
        self.assertEqual(plan["payload"]["bpm"], 72)
        self.assertEqual(plan["retained_spec"], self.record["json_spec"])
        self.assertIn("future_requirement", plan["field_routes"])
        self.assertFalse(plan["ready_for_execution"])
        self.assertEqual(self.record, original)

    def test_rejects_unconfirmed_invalid_and_unconnected_plans(self):
        for updates in ({"bpm": -20}, {"bpm": 72.4}, {"bpm": float("nan")}, {"bpm": True},
                        {"duration_seconds": 601}, {"time_signature": "7/8"}, {"key": "invalid"},
                        {"task_type": "cover"}, {"language": "invented"}):
            with self.subTest(updates=updates):
                record = deepcopy(self.record)
                record["json_spec"].update(updates)
                with self.assertRaises(ValueError):
                    AceStepPlanCompiler().compile(record, "Letra")
        self.record["revision"]["user_confirmation_status"] = "pending"
        with self.assertRaisesRegex(ValueError, "Confirma"):
            AceStepPlanCompiler().compile(self.record, "Letra")

    def test_does_not_truncate_caption_or_lyrics_and_declares_default(self):
        with self.assertRaises(ValueError):
            AceStepPlanCompiler().compile(self.record, "x" * 4097)
        self.record["json_spec"]["voice_style"] = "x" * 513
        with self.assertRaises(ValueError):
            AceStepPlanCompiler().compile(self.record, "Letra")
        self.record["json_spec"]["voice_style"] = "suave"
        self.record["json_spec"].pop("time_signature")
        self.assertEqual(AceStepPlanCompiler().compile(self.record, "Letra")["defaults"], {"time_signature": "4/4"})

    def test_preview_reads_active_project_without_mutation(self):
        store = Mock()
        store.get_song_project.return_value = {"spec": self.record}
        result = PreviewAceStepPlan(store).execute("song1", "Letra")
        self.assertEqual(result["spec_revision_id"], "r1")
        store.update_song_project_phase.assert_not_called()
        store.create_song_artifact.assert_not_called()
