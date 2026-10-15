import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from application.runtime_correspondence import RuntimeCorrespondence


class RuntimeCorrespondenceTest(unittest.TestCase):
    def test_requested_lm_cannot_match_direct_or_unused_report(self):
        self.plan["payload"]["generation_api"] = "high_level_lm"
        for observation in ({"api": "direct", "lm_used": False},
                            {"api": "high_level_lm", "lm_used": False}, {}):
            report = RuntimeCorrespondence().build({**self.runtime, "generation_api": observation}, self.plan, "a")
            self.assertFalse(report["matches"])
        self.assertTrue(RuntimeCorrespondence().build({**self.runtime, "generation_api": {
            "api": "high_level_lm", "lm_used": True}}, self.plan, "a")["matches"])

    def setUp(self):
        self.plan = {"retained_spec": {"ace_step_config": "acestep-v15-base"}, "payload": {"task_type": "text2music"}}
        self.runtime = {"status": "reported_completion", "source": "wrapper_diagnostics", "audio_sha256": "a",
                        "reported_config": "acestep-v15-base", "infer_steps": 32, "task_type": "text2music"}

    def test_complete_matching_report_does_not_certify_quality(self):
        report = RuntimeCorrespondence().build(self.runtime, self.plan, "a")
        self.assertTrue(report["matches"])
        self.assertFalse(report["quality_verified"])

    def test_each_execution_difference_is_visible(self):
        for key, changed in (("audio_sha256", "b"), ("reported_config", "acestep-v15-turbo"),
                             ("infer_steps", 8), ("infer_steps", True), ("task_type", "cover")):
            result = RuntimeCorrespondence().build({**self.runtime, key: changed}, self.plan, "a")
            self.assertFalse(result["matches"])
            self.assertIn("mismatch", [c["status"] for c in result["checks"]])

    def test_missing_report_or_unknown_profile_stays_pending(self):
        for runtime, plan in (({}, self.plan), ({**self.runtime, "source": "mock"}, self.plan),
                              (self.runtime, {"retained_spec": {"ace_step_config": "unknown"}})):
            result = RuntimeCorrespondence().build(runtime, plan, "a")
            self.assertFalse(result["matches"])
            self.assertIn("pending", [c["status"] for c in result["checks"]])
