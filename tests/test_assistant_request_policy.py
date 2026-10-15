import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from application.assistant_request_policy import conversation_state, needs_technical_review


class AssistantRequestPolicyTest(unittest.TestCase):
    def test_creative_request_does_not_require_qwen_but_review_and_patch_do(self):
        self.assertFalse(needs_technical_review("Propone cuatro lineas sobre una tarde tranquila", {}))
        self.assertTrue(needs_technical_review("Valida la compatibilidad con ACE-Step", {}))
        self.assertTrue(needs_technical_review("Cambia la velocidad", {"available": True}))

    def test_current_spec_constraints_and_gates_survive_without_execution_history(self):
        original = {"missing": ["sample"], "sample_evaluation": {"approved": False},
            "professional_project": {"id": "s1", "spec": {"required_phrase": "hogar", "revision": "r1"},
                                     "events": [{"message": "x" * 100000}], "artifacts": ["duplicate"]}}
        state = conversation_state(original)
        self.assertEqual(state["professional_project"]["spec"], original["professional_project"]["spec"])
        self.assertEqual(state["sample_evaluation"], {"approved": False})
        self.assertEqual(state["missing"], ["sample"])
        self.assertNotIn("events", state["professional_project"])
        self.assertIn("events", original["professional_project"])
