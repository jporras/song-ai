import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from application.candidate_fidelity import CandidateFidelityReport


class FidelityTest(unittest.TestCase):
    def test_measurements_are_not_musical_acceptance_or_guessed_scores(self):
        plan = {"spec_revision_id": "r1", "plan_sha256": "p1", "retained_spec": {},
                "payload": {"task_type": "text2music", "audio_duration": 10, "bpm": 72}}
        evidence = {"duration_seconds": 11, "sha256": "a1"}
        report = CandidateFidelityReport().build(plan, evidence)
        self.assertEqual(report["checks"][0]["status"], "tolerance_pending")
        self.assertEqual(report["checks"][1]["observed"], None)
        self.assertFalse(report["final_quality_verified"])
        plan["retained_spec"]["duration_tolerance_seconds"] = 2
        self.assertEqual(CandidateFidelityReport().build(plan, evidence)["checks"][0]["status"], "within_tolerance")
        plan["retained_spec"]["duration_tolerance_seconds"] = .5
        self.assertEqual(CandidateFidelityReport().build(plan, evidence)["checks"][0]["status"], "outside_tolerance")
        plan["payload"]["task_type"] = "repaint"
        self.assertEqual(CandidateFidelityReport().build(plan, evidence)["checks"][0]["status"], "not_evaluated")
