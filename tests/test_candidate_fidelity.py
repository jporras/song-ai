import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from application.candidate_fidelity import CandidateFidelityReport


class FidelityTest(unittest.TestCase):
    def test_editing_modes_have_specific_pending_checks_without_invented_measurements(self):
        expected = {"cover": {"source_preservation"}, "repaint": {"edited_interval", "exterior_preservation"},
                    "lego": {"target_tracks", "task_instruction", "context_coherence"},
                    "extract": {"target_tracks", "task_instruction", "extraction_leakage"},
                    "complete": {"target_tracks", "task_instruction", "context_coherence"}}
        for task, ids in expected.items():
            plan = {"spec_revision_id": "r", "plan_sha256": "p", "payload": {"task_type": task,
                "audio_duration": 30, "repainting_start": 2, "repainting_end": 5, "instruction": "guitar"},
                "retained_spec": {"target_tracks": ["guitar"]}}
            report = CandidateFidelityReport().build(plan, {"duration_seconds": 30, "sha256": "audio"})
            checks = {c["id"]: c for c in report["checks"]}
            self.assertEqual(report["task_type"], task)
            for key in ids:
                self.assertIsNone(checks[key]["observed"])
                self.assertEqual(checks[key]["method"], "not_measured")
            self.assertFalse(report["final_quality_verified"])
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
