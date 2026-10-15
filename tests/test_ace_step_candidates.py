import sys
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path
from unittest.mock import Mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from application.ace_step_candidate_service import AceStepCandidateService
from audio.execution_lock import exclusive_audio


class CandidateTest(unittest.TestCase):
    def test_linked_set_fingerprint_is_recorded_and_rechecked(self):
        with tempfile.TemporaryDirectory() as folder:
            store = Mock(data_dir=Path(folder))
            store.get_song_project.return_value = {"id": "song", "user_id": "set:s1"}
            store.set_generation_fingerprint.return_value = "fingerprint1"
            review = Mock()
            review.latest.return_value = {"plan_id": "p1", "effective_status": "approved", "plan": {
                "plan_sha256": "hash", "spec_revision_id": "r1", "retained_spec": {"ace_step_config": "acestep-v15-base"},
                "payload": {"task_type": "text2music"}}}
            runner = Mock()
            runner.run.side_effect = lambda project, item, profile, directory, output, revalidate: revalidate()
            action = AceStepCandidateService(store, review, runner, Mock(return_value={"sha256": "audiohash"}))
            request = {"plan_sha256": "hash", "exploratory_audio_authorized": True}
            action.execute("song", request)
            metadata = store.create_song_artifact.call_args.kwargs["metadata"]
            self.assertEqual(metadata["set_id"], "s1")
            self.assertEqual(metadata["set_fingerprint"], "fingerprint1")
            store.create_song_artifact.reset_mock()
            store.set_generation_fingerprint.side_effect = ["fingerprint1", "fingerprint1", "changed"]
            with self.assertRaisesRegex(ValueError, "set cambio"):
                action.execute("song", request)
            store.create_song_artifact.assert_not_called()

    def test_project_relinking_blocks_candidate_registration(self):
        with tempfile.TemporaryDirectory() as folder:
            store = Mock(data_dir=Path(folder))
            store.get_song_project.side_effect = [{"id": "song", "user_id": "set:s1"}, {"id": "song", "user_id": "set:s2"}]
            review = Mock()
            review.latest.return_value = {"plan_id": "p", "effective_status": "approved", "plan": {
                "plan_sha256": "hash", "spec_revision_id": "r", "retained_spec": {"ace_step_config": "acestep-v15-base"},
                "payload": {"task_type": "text2music"}}}
            runner = Mock()
            runner.run.side_effect = lambda project, item, profile, directory, output, revalidate: revalidate()
            action = AceStepCandidateService(store, review, runner, Mock())
            with self.assertRaisesRegex(ValueError, "proyecto cambio de set"):
                action.execute("song", {"plan_sha256": "hash", "exploratory_audio_authorized": True})
            store.create_song_artifact.assert_not_called()

    def test_six_modes_preserve_candidate_semantics_and_originals(self):
        with tempfile.TemporaryDirectory() as folder:
            for task in ("text2music", "cover", "repaint", "lego", "extract", "complete"):
                with self.subTest(task=task):
                    store = Mock(data_dir=Path(folder))
                    store.get_song_project.return_value = {"id": "song"}
                    review = Mock()
                    review.latest.return_value = {"plan_id": "p1", "effective_status": "approved",
                        "plan": {"plan_sha256": "hash", "spec_revision_id": "r1",
                                 "retained_spec": {"ace_step_config": "acestep-v15-base"}, "payload": {"task_type": task}}}
                    runner = Mock()
                    def run(project, item, profile, directory, output, revalidate):
                        revalidate()
                        directory.mkdir(parents=True)
                        output.write_bytes(b"audio")
                    runner.run.side_effect = run
                    inspector = Mock(return_value={"sha256": "audiohash"})
                    service = AceStepCandidateService(store, review, runner, inspector)
                    result = service.execute("song", {"plan_sha256": "hash", "exploratory_audio_authorized": True})
                    self.assertFalse(result["sample_approved"])
                    metadata = store.create_song_artifact.call_args.kwargs["metadata"]
                    self.assertEqual(metadata["task_type"], task)
                    self.assertFalse(metadata["musical_quality_verified"])
                    store.update_song_project_phase.assert_not_called()
                    self.assertIn("candidates", store.create_song_artifact.call_args.kwargs["file_path"])

    def test_authorization_exclusivity_and_changed_inputs_block_registration(self):
        with tempfile.TemporaryDirectory() as folder:
            store = Mock(data_dir=Path(folder))
            review = Mock()
            original = {"plan_id": "p1", "effective_status": "approved", "plan": {"plan_sha256": "hash",
                "spec_revision_id": "r1", "retained_spec": {"ace_step_config": "acestep-v15-base"}, "payload": {"task_type": "cover"}}}
            review.latest.return_value = original
            runner = Mock()
            service = AceStepCandidateService(store, review, runner, Mock(return_value={}))
            request = {"plan_sha256": "hash", "exploratory_audio_authorized": True}
            with self.assertRaises(ValueError):
                service.execute("song", {})
            with exclusive_audio(), self.assertRaisesRegex(ValueError, "en curso"):
                service.execute("song", request)
            stale = deepcopy(original)
            stale["effective_status"] = "stale"
            review.latest.side_effect = [original, stale]
            with self.assertRaisesRegex(ValueError, "inputs cambiaron"):
                service.execute("song", request)
            store.create_song_artifact.assert_not_called()
