import sys
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path
from unittest.mock import Mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from models.ace_step_generation_options import generation_options
from application.ace_step_plan_compiler import PreviewAceStepPlan
from adapters.ace_step_execution import AceStepExecutionArguments
from audio.ace_step_profiles import resolve_ace_step_profile


class GenerationOptionsTest(unittest.TestCase):
    def test_optional_api_defaults_and_explicit_lm_model(self):
        self.assertEqual(generation_options({}), {})
        self.assertEqual(generation_options({"generation_api": "high_level"}), {"generation_api": "high_level"})
        self.assertEqual(generation_options({"generation_api": "high_level_lm"}), {
            "generation_api": "high_level_lm", "lm_model_path": "acestep-5Hz-lm-1.7B"})
        for spec in ({"generation_api": "unknown"},
                     {"generation_api": "high_level_lm", "task_type": "repaint"},
                     {"generation_api": "high_level_lm", "lm_model_path": "../../other"}):
            with self.subTest(spec=spec), self.assertRaises(ValueError):
                generation_options(spec)

    def test_invalid_controls_and_turbo_guidance_are_rejected(self):
        for options in ({"seed": True}, {"seed": 1.2}, {"seed": -1},
                        {"inference_steps": 201}, {"shift": float("nan")},
                        {"ace_step_config": "acestep-v15-turbo", "inference_steps": 21},
                        {"ace_step_config": "acestep-v15-turbo", "guidance_scale": 7}):
            with self.subTest(options=options), self.assertRaises(ValueError):
                generation_options(options)

    def test_reference_checksum_and_controls_change_plan_and_exact_arguments(self):
        spec = {"bpm": 72, "key": "C major", "language": "es", "duration_seconds": 30,
                "song_type": "balada", "ace_step_config": "acestep-v15-base",
                "reference_artifact_id": "ref", "reference_audio": "reference.wav",
                "seed": 123, "inference_steps": 48, "guidance_scale": 6, "shift": 2}
        store = Mock()
        store.get_song_project.return_value = {"id": "song", "spec": {
            "revision": {"revision_id": "r", "user_confirmation_status": "confirmed", "deterministic_valid": True},
            "missing_fields": [], "json_spec": spec}}
        inspector = Mock()
        inspector.inspect.return_value = {"sha256": "first", "artifact_id": "ref", "file_path": "reference.wav"}
        preview = PreviewAceStepPlan(store, inspector)
        plan = preview.execute("song", "Letra")
        inspector.inspect.assert_called_once_with(store.get_song_project.return_value, "ref", "reference.wav")
        inspector.inspect.return_value = {"sha256": "changed", "artifact_id": "ref", "file_path": "reference.wav"}
        self.assertNotEqual(plan["plan_sha256"], preview.execute("song", "Letra")["plan_sha256"])
        item = {"effective_status": "approved", "inputs_current": True, "plan": plan}
        with tempfile.TemporaryDirectory() as folder:
            argv = AceStepExecutionArguments().build(item, resolve_ace_step_profile("base"), "python", Path(folder), Path(folder)/"out.wav")
        for flag, value in (("--reference-audio", "reference.wav"), ("--seed", "123"), ("--infer-step", "48"), ("--guidance-scale", "6"), ("--shift", "2")):
            self.assertEqual(argv.count(flag), 1)
            self.assertEqual(argv[argv.index(flag)+1], value)

    def test_reference_failure_blocks_plan(self):
        store = Mock()
        store.get_song_project.return_value = {"spec": {"revision": {
            "revision_id": "r", "user_confirmation_status": "confirmed", "deterministic_valid": True},
            "missing_fields": [], "json_spec": {"bpm": 72, "key": "C major", "language": "es",
                "duration_seconds": 30, "song_type": "balada", "reference_audio": "other.wav", "reference_artifact_id": "other"}}}
        inspector = Mock()
        inspector.inspect.side_effect = ValueError("otro proyecto")
        with self.assertRaisesRegex(ValueError, "otro proyecto"):
            PreviewAceStepPlan(store, inspector).execute("song", "Letra")
