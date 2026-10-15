import sys
import unittest
from types import SimpleNamespace, ModuleType
from unittest.mock import Mock, patch
from tools.acestep_high_level import generate


class HighLevelAdapterTest(unittest.TestCase):
    def setUp(self):
        self.args = SimpleNamespace(generation_api="high_level_lm", task_type="text2music",
            checkpoint_path="weights", lm_model_path="acestep-5Hz-lm-1.7B", bpm=72,
            key_scale="C Major", time_signature="4", vocal_language="es", duration=30,
            reference_audio="", src_audio="", infer_step=32, guidance_scale=7, seed=42,
            shift=None, config_path="acestep-v15-base", repainting_start=0,
            repainting_end=-1, audio_cover_strength=1, chunk_mask_mode="auto", instruction="")
        self.lm = Mock(llm_initialized=True)
        self.lm.initialize.return_value = ("ready", True)
        self.api = ModuleType("acestep.inference")
        self.api.GenerationParams = lambda **kw: SimpleNamespace(**kw)
        self.api.GenerationConfig = lambda **kw: SimpleNamespace(**kw)
        self.api.generate_music = Mock(return_value=SimpleNamespace(success=True, error=None,
            audios=[{"params": {"caption": "idea", "lyrics": "letra", "vocal_language": "es", "audio_codes": "codes"}}],
            extra_outputs={"time_costs": {"lm_total_time": 1}}))
        lm_module = ModuleType("acestep.llm_inference")
        lm_module.LLMHandler = Mock(return_value=self.lm)
        self.modules = {"acestep": ModuleType("acestep"), "acestep.inference": self.api,
                        "acestep.llm_inference": lm_module}

    def run_adapter(self):
        self.diag = {"runtime": {}}
        with patch.dict(sys.modules, self.modules):
            return generate(Mock(), self.args, "idea", "letra", self.diag, "output")

    def test_explicit_seed_no_rewrites_lm_evidence_and_unload(self):
        self.run_adapter()
        _, _, params, config = self.api.generate_music.call_args.args
        self.assertTrue(params.thinking)
        self.assertFalse(params.use_cot_caption)
        self.assertFalse(params.use_cot_language)
        self.assertFalse(params.use_cot_metas)
        self.assertEqual(config.seeds, [42])
        self.assertFalse(config.use_random_seed)
        self.assertTrue(self.diag["runtime"]["generation_api"]["lm_used"])
        self.lm.unload.assert_called_once()

    def test_engine_observations_are_not_filled_from_wrapper_defaults(self):
        self.api.generate_music.return_value.audios[0]['params']['shift'] = 1
        self.run_adapter()
        observed = self.diag['runtime']['generation_api']['engine_reported_options']
        self.assertEqual(observed, {'shift':1})
        self.assertNotIn('guidance_scale', observed)
        self.assertIn('guidance_scale', self.diag['runtime']['generation_api']['input_correspondence']['unreported_fields'])

    def test_reported_changes_to_connected_inputs_fail_closed(self):
        changes = {'bpm': 99, 'duration': 60, 'keyscale': 'D Minor',
                   'src_audio': 'another.wav', 'audio_cover_strength': .5,
                   'inference_steps': 8, 'guidance_scale': 1, 'shift': 2,
                   'seed': 7, 'task_type': 'cover'}
        effective = self.api.generate_music.return_value.audios[0]['params']
        for field, value in changes.items():
            with self.subTest(field=field):
                effective[field] = value
                with self.assertRaisesRegex(RuntimeError, field):
                    self.run_adapter()
                self.assertEqual(self.diag['runtime']['generation_api']['status'], 'failed')
                self.assertIn(field, self.diag['runtime']['generation_api']['input_correspondence']['mismatched_fields'])
                del effective[field]

    def test_high_level_without_lm_does_not_initialize_model(self):
        self.args.generation_api = "high_level"
        self.run_adapter()
        self.lm.initialize.assert_not_called()
        self.assertFalse(self.diag["runtime"]["generation_api"]["lm_used"])

    def test_failure_no_codes_and_modified_inputs_are_not_success(self):
        for values in ({"caption": "changed"}, {"audio_codes": ""}):
            with self.subTest(values=values):
                self.api.generate_music.return_value.audios[0]["params"].update(values)
                with self.assertRaises(RuntimeError):
                    self.run_adapter()
                self.assertEqual(self.diag["runtime"]["generation_api"]["status"], "failed")
                self.api.generate_music.return_value.audios[0]["params"].update(caption="idea", audio_codes="codes")

    def test_missing_lm_and_unsupported_mode_fail_closed(self):
        self.lm.initialize.return_value = ("missing", False)
        with self.assertRaises(RuntimeError):
            self.run_adapter()
        self.api.generate_music.assert_not_called()
        self.args.task_type = "cover"
        with self.assertRaises(ValueError):
            self.run_adapter()
