import sys
import unittest
from pathlib import Path
from unittest.mock import Mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from application.candidate_correction_review import ReviewCandidateCorrection


class CorrectionReviewTest(unittest.TestCase):
    def setUp(self):
        self.store, self.corrections, self.orchestrator, self.context = Mock(), Mock(), Mock(), Mock()
        self.proposal = {"inputs_current": True, "created_at": "date", "notes": "Cambiar guitarra", "artifact_id": "a"}
        self.corrections.latest.return_value = {"proposal": self.proposal}
        self.store.get_song_project.return_value = {"user_id": "set:set1", "spec": {"revision": "r"}}
        self.context.return_value = {"project": {"project_id": "set1", "project_name": "Idea", "description": "Pop"},
            "set": {"set_id": "set1"}, "assets": {k: {"intent": {"kind": k}, "manifest": {"asset": k}}
                                                       for k in ("instrumental", "melody", "lyrics")}}
        self.orchestrator.run_handoff.return_value = {"summary": "Propuesta", "result": {"mode": "mock_handoff", "provider_executed": False}}
        self.action = ReviewCandidateCorrection(self.store, self.corrections, self.orchestrator, self.context)
        self.request = {"review_requested": True, "proposal_created_at": "date"}

    def test_review_uses_persisted_context_and_orchestrator_without_applying_output(self):
        self.proposal["technical_review"] = {"handoff": "previous"}
        result = self.action.execute("song", "task", self.request)["review"]
        context = self.orchestrator.run_handoff.call_args.args[0]["context"]
        self.assertEqual(context["vocal_intent"], {"kind": "melody"})
        self.assertEqual(context["lyrical_intent"], {"kind": "lyrics"})
        self.assertEqual(context["instrumental_intent"], {"kind": "instrumental"})
        self.assertEqual(context["correction"]["notes"], self.proposal["notes"])
        self.assertNotIn("technical_review", context["correction"])
        self.assertFalse(context["apply_changes"])
        self.assertFalse(result["changes_applied"])
        self.assertTrue(result["inputs_current_at_completion"])
        self.context.assert_called_once_with("set1")
        self.store.upsert_song_spec.assert_not_called()

    def test_explicit_request_current_proposal_and_valid_set_are_required(self):
        for request in ({}, {**self.request, "proposal_created_at": "old"}):
            with self.assertRaises(ValueError): self.action.execute("s", "t", request)
        self.store.get_song_project.return_value = {"user_id": "user"}
        with self.assertRaises(ValueError): self.action.execute("s", "t", self.request)
        self.orchestrator.run_handoff.assert_not_called()
        self.store.create_song_event.assert_not_called()

    def test_inputs_changing_during_handoff_mark_result_historical(self):
        self.corrections.latest.side_effect = [{"proposal": self.proposal},
            {"proposal": {**self.proposal, "inputs_current": False}}]
        result = self.action.execute("s", "t", self.request)["review"]
        self.assertFalse(result["inputs_current_at_completion"])
        self.assertFalse(result["changes_applied"])
