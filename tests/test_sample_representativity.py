import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from application.sample_representativity import SampleRepresentativity


class SampleRepresentativityTest(unittest.TestCase):
    def setUp(self):
        self.sample = {"sample_id": "s", "set_fingerprint": "f", "plan_id": "p", "plan_sha256": "h",
                       "spec_revision_id": "r", "provider_config": "base", "task_type": "text2music", "audio_evidence": {"sha256": "a"}}
        self.plan = {"plan_id": "p", "inputs_current": True, "effective_status": "approved", "plan": {
            "plan_sha256": "h", "spec_revision_id": "r", "retained_spec": {"ace_step_config": "base"}, "payload": {"task_type": "text2music"}}}

    def test_matching_configuration_never_certifies_audio_quality(self):
        report = SampleRepresentativity().build(self.sample, self.plan, "f", {"sha256": "a"})
        self.assertTrue(report["configuration_matches"])
        self.assertFalse(report["representativity_verified"])
        self.assertFalse(report["final_generation_ready"])
        self.assertTrue({"runtime", "voice", "listening"}.issubset({c["id"] for c in report["checks"] if c["status"] == "pending"}))
        self.assertFalse(report["execution_configuration_matches"])

    def test_changed_missing_unapproved_plan_and_audio_do_not_match(self):
        for plan, fingerprint, evidence in ((None, "f", {"sha256": "a"}),
            ({**self.plan, "inputs_current": False}, "f", {"sha256": "a"}),
            ({**self.plan, "effective_status": "pending"}, "f", {"sha256": "a"}),
            (self.plan, "changed", {"sha256": "a"}), (self.plan, "f", {"sha256": "changed"})):
            with self.subTest(plan=plan):
                self.assertFalse(SampleRepresentativity().build(self.sample, plan, fingerprint, evidence)["configuration_matches"])
