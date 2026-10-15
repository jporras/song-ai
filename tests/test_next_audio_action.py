import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from application.next_audio_action import NextAudioAction
from application.song_service import SongService


class NextAudioActionTest(unittest.TestCase):
    def test_current_correction_is_guided_to_controls_without_authorizing_generation(self):
        result = NextAudioAction().choose({"status": "reviewed", "review": {"inputs_current": True,
            "decision": "changes_requested"}, "correction": {"inputs_current": True}}, {"status": "sample_pending"})
        self.assertEqual(result["code"], "review_correction_controls")
        self.assertFalse(result["final_generation_ready"])
    def test_candidate_feedback_selects_safe_next_step(self):
        for candidate, code in (
            ({"status": "listening_pending"}, "listen_candidate"),
            ({"status": "audio_unavailable"}, "replace_candidate"),
            ({"status": "reviewed", "review": {"inputs_current": False, "decision": "accepted"}}, "review_plan"),
            ({"status": "reviewed", "review": {"inputs_current": True, "decision": "changes_requested"}}, "review_changes"),
            ({"status": "reviewed", "review": {"inputs_current": True, "decision": "accepted"}}, "create_sample")):
            result = NextAudioAction().choose(candidate, {"status": "sample_pending"})
            self.assertEqual(result["code"], code)
            self.assertFalse(result["final_generation_ready"])

    def test_sample_steps_take_precedence_and_never_authorize_final(self):
        for sample, code in (({"status": "evaluation_pending", "approval_status": "pending"}, "listen_sample"),
            ({"status": "evaluation_pending", "approval_status": "approved"}, "evaluate_sample"),
            ({"status": "historical_evaluation"}, "reevaluate_sample"),
            ({"status": "evaluated", "approval_status": "approved", "report": {"configuration_matches": False}}, "update_candidate"),
            ({"status": "evaluated", "approval_status": "approved", "report": {"configuration_matches": True}}, "complete_sample_evidence")):
            result = NextAudioAction().choose({"status": "listening_pending"}, sample)
            self.assertEqual(result["code"], code)
            self.assertFalse(result["final_generation_ready"])

    def test_missing_set_is_required_and_no_audio_keeps_existing_guidance(self):
        self.assertEqual(NextAudioAction().choose({"status": "listening_pending"}, {"status": "set_pending"})["code"], "prepare_set")
        self.assertIsNone(NextAudioAction().choose({}, {}))

    def test_gemma_grounded_guidance_prioritizes_sample_over_old_technical_advice(self):
        action = NextAudioAction().choose({"status": "listening_pending"}, {"status": "evaluation_pending", "approval_status": "pending"})
        message = SongService._deterministic_gemma_guidance(None, {"audio_next_action": action},
            {"gemma_instruction": "Ejecuta Mastering y Export", "next_action": "Genera el final"})
        self.assertIn("Escucha el sample", message)
        self.assertNotIn("Genera el final", message)
        self.assertNotIn("Mastering", message)

    def test_historical_sample_opinion_never_offers_approval(self):
        result = NextAudioAction().choose({}, {"status": "evaluated", "approval_status": "approved",
            "listening_review": {"decision": "accepted", "review_current": False}})
        self.assertEqual(result["code"], "listen_updated_sample")
        self.assertFalse(result["final_generation_ready"])
