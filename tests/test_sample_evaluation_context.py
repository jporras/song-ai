import sys
import unittest
from pathlib import Path
from unittest.mock import Mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from application.sample_evaluation_context import SampleEvaluationContext


class SampleContextTest(unittest.TestCase):
    def test_selected_project_receives_report_and_never_final_authorization(self):
        store, read = Mock(), Mock()
        store.list_samples_for_set.return_value = [{"sample_id": "s1", "source_song_id": "song1", "approval_status": "approved"}]
        read.return_value = {"report": {"assessment_current": True, "configuration_matches": True}}
        context = SampleEvaluationContext(store, read).build({"id": "song1", "user_id": "set:set1"})
        read.assert_called_once_with("song1", "s1")
        store.list_samples_for_set.assert_called_once_with("set1")
        self.assertEqual(context["status"], "evaluated")
        self.assertFalse(context["final_generation_ready"])
        read.return_value = {"report": {"assessment_current": False}}
        self.assertEqual(SampleEvaluationContext(store, read).build({"id": "song1", "user_id": "set:set1"})["status"], "historical_evaluation")

    def test_another_project_sample_is_not_given_to_assistant(self):
        store, read = Mock(), Mock()
        store.list_samples_for_set.return_value = [{"sample_id": "s", "source_song_id": "other"}]
        context = SampleEvaluationContext(store, read).build({"id": "song1", "user_id": "set:set1"})
        self.assertEqual(context["status"], "project_sample_pending")
        read.assert_not_called()

    def test_missing_set_sample_and_evaluation_remain_pending(self):
        store, read = Mock(), Mock()
        action = SampleEvaluationContext(store, read)
        self.assertEqual(action.build(None)["status"], "set_pending")
        store.list_samples_for_set.assert_not_called()
        store.list_samples_for_set.return_value = []
        project = {"id": "song1", "user_id": "set:set1"}
        self.assertEqual(action.build(project)["status"], "sample_pending")
        store.list_samples_for_set.return_value = [{"sample_id": "s", "source_song_id": "song1"}]
        read.return_value = {"report": None}
        self.assertEqual(action.build(project)["status"], "evaluation_pending")
