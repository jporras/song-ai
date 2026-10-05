import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from audio.ace_step_profiles import BASE_PROFILE, TURBO_PROFILE, apply_ace_step_profile_env
from audio.ace_step_commands import normalize_ace_step_template


class AceStepProfilesTest(unittest.TestCase):
    def test_historical_templates_use_shared_root_and_explicit_profile(self):
        old = "python tools/acestep_generate.py --checkpoint-path data/models/music/acestep-1.5-{model_type}"
        converted = normalize_ace_step_template(old)
        self.assertIn("{checkpoint_root}", converted)
        self.assertIn("--config-path {config_path}", converted)
        self.assertEqual(normalize_ace_step_template(converted), converted)
        custom = "python custom_provider.py --checkpoint-path custom"
        self.assertEqual(normalize_ace_step_template(custom), custom)
    def test_base_selects_v15_explicitly_and_reuses_shared_components(self):
        values = BASE_PROFILE.format_values()
        self.assertEqual(values["config_path"], "acestep-v15-base")
        self.assertEqual(values["checkpoint_root"], TURBO_PROFILE.checkpoint_root)
        self.assertEqual(BASE_PROFILE.infer_steps, 32)
        self.assertEqual(BASE_PROFILE.model_type, "2b-base")

    def test_profile_overrides_conflicting_environment_configuration(self):
        for profile in (BASE_PROFILE, TURBO_PROFILE):
            env = apply_ace_step_profile_env({"ACESTEP_CONFIG_PATH": "wrong", "UNRELATED": "keep"}, profile)
            self.assertEqual(env["ACESTEP_CONFIG_PATH"], profile.config_path)
            self.assertEqual(env["ACESTEP_CHECKPOINTS_DIR"], profile.checkpoint_root)
            self.assertEqual(env["UNRELATED"], "keep")
