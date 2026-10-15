import sys
import unittest
import tempfile
from types import SimpleNamespace
from pathlib import Path
from unittest.mock import Mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from application.candidate_listening_review import ReviewCandidateListening, listening_review_view, CandidateListeningContext
from application.song_service import SongService
from application.ace_step_candidate_jobs import AceStepCandidateJobs
from core.storage import StorageManager
from adapters.sample_audio_evidence import inspect_sample_wav
from tests.test_sample_audio_evidence import write_audio


class ListeningReviewTest(unittest.TestCase):
    def test_review_is_bound_to_listened_artifact_and_not_final_approval(self):
        store, jobs, audio = Mock(), Mock(), Mock()
        jobs.get.return_value = {"result": {"artifact": {"artifact_id": "a1", "metadata": {"plan_id": "p1", "spec_revision_id": "r1"}}}}
        result = ReviewCandidateListening(store, jobs, audio).execute("song", "task", {
            "listened": True, "decision": "accepted", "audio_sha256": "hash"})
        audio.assert_called_once_with("song", "task", "hash")
        self.assertFalse(result["review"]["sample_approved"])
        self.assertFalse(result["review"]["final_quality_verified"])
        self.assertEqual(result["review"]["spec_revision_id"], "r1")
        store.update_song_project_phase.assert_not_called()

    def test_missing_listening_change_description_or_bad_audio_prevents_save(self):
        store, jobs, audio = Mock(), Mock(), Mock()
        action = ReviewCandidateListening(store, jobs, audio)
        for request in ({"decision": "accepted"}, {"listened": True, "decision": "changes_requested"}):
            with self.assertRaises(ValueError):
                action.execute("song", "task", request)
        audio.side_effect = ValueError("Audio cambiado")
        with self.assertRaises(ValueError):
            action.execute("song", "task", {"listened": True, "decision": "accepted", "audio_sha256": "old"})
        store.create_song_event.assert_not_called()


class ListeningReviewCurrentnessTest(unittest.TestCase):
    def test_only_same_current_plan_and_revision_matches(self):
        review = {"plan_id": "p1", "spec_revision_id": "r1", "decision": "accepted"}
        plan = {"plan_id": "p1", "inputs_current": True, "plan": {"spec_revision_id": "r1"}}
        self.assertTrue(listening_review_view(review, plan)["inputs_current"])
        for candidate in (None, {**plan, "inputs_current": False}, {**plan, "plan_id": "p2"},
                          {**plan, "plan": {"spec_revision_id": "r2"}}):
            result = listening_review_view(review, candidate)
            self.assertFalse(result["inputs_current"])
            self.assertEqual(result["decision"], "accepted")
        self.assertNotIn("inputs_current", review)
        self.assertIsNone(listening_review_view(None, plan))


class ListeningCriteriaTest(unittest.TestCase):
    def setUp(self):
        self.store, self.jobs, self.audio = Mock(), Mock(), Mock()
        self.jobs.get.return_value = {"result": {"artifact": {"artifact_id": "a1", "metadata": {
            "plan_id": "p1", "spec_revision_id": "r1"}}, "fidelity_report": {"checks": [
                {"id": "lyrics", "method": "not_measured"},
                {"id": "duration", "method": "wav_frames_sample_rate"}]}}}
        self.action = ReviewCandidateListening(self.store, self.jobs, self.audio)
        self.request = {"listened": True, "decision": "accepted", "audio_sha256": "hash"}

    def test_subjective_criteria_persist_without_changing_measurements(self):
        result = self.action.execute("s", "t", {**self.request, "criteria": {"lyrics": "unsure"}})
        self.assertEqual(result["review"]["criteria"], {"lyrics": "unsure"})
        self.assertEqual(result["review"]["criteria_method"], "user_listening")
        self.assertFalse(result["review"]["sample_approved"])
        self.assertNotIn("observed", self.jobs.get.return_value["result"]["fidelity_report"]["checks"][0])

    def test_unknown_objective_and_invalid_responses_cannot_be_saved(self):
        for criteria in ([], {"duration": "matches"}, {"invented": "matches"}, {"lyrics": True}, {"lyrics": "yes"}):
            with self.assertRaises(ValueError):
                self.action.execute("s", "t", {**self.request, "criteria": criteria})
        self.store.create_song_event.assert_not_called()

    def test_correction_requires_consistent_decision_and_notes(self):
        request = {**self.request, "criteria": {"lyrics": "needs_changes"}}
        for changes in ({}, {"decision": "changes_requested"}):
            with self.assertRaises(ValueError):
                self.action.execute("s", "t", {**request, **changes})
        result = self.action.execute("s", "t", {**request, "decision": "changes_requested", "notes": "Falta el coro"})
        self.assertEqual(result["review"]["criteria"]["lyrics"], "needs_changes")


class ListeningContextTest(unittest.TestCase):
    def test_context_includes_persisted_correction_from_selected_project(self):
        jobs, read, correction = Mock(), Mock(), Mock()
        jobs.latest.return_value = {"task_id": "t", "status": "completed"}
        read.return_value = {"review": {"decision": "changes_requested", "inputs_current": True}}
        correction.return_value = {"proposal": {"scope": "arrangement", "inputs_current": True}}
        result = CandidateListeningContext(jobs, read, correction).build("song")
        correction.assert_called_once_with("song", "t")
        self.assertEqual(result["correction"]["scope"], "arrangement")
        self.assertFalse(result["final_quality_verified"])
    def test_context_uses_only_selected_project_and_retains_historical_status(self):
        jobs, read = Mock(), Mock()
        jobs.latest.return_value = {"task_id": "t1", "status": "completed"}
        read.return_value = {"review": {"inputs_current": False, "notes": "Cambiar el coro"}}
        context = CandidateListeningContext(jobs, read).build("song1")
        jobs.latest.assert_called_once_with("song1")
        read.assert_called_once_with("song1", "t1")
        self.assertFalse(context["review"]["inputs_current"])
        self.assertFalse(context["sample_approved"])

    def test_missing_project_or_incomplete_candidate_does_not_read_opinions(self):
        jobs, read = Mock(), Mock()
        action = CandidateListeningContext(jobs, read)
        self.assertEqual(action.build("")["status"], "no_project")
        jobs.latest.assert_not_called()
        for task in (None, {"status": "running"}, {"status": "failed"}):
            jobs.latest.return_value = task
            self.assertEqual(action.build("s")["status"], "no_completed_candidate")
        read.assert_not_called()

    def test_unreviewed_audio_is_not_accepted(self):
        jobs, read = Mock(), Mock()
        jobs.latest.return_value = {"task_id": "t", "status": "completed"}
        read.return_value = {"review": None}
        result = CandidateListeningContext(jobs, read).build("s")
        self.assertEqual(result["status"], "listening_pending")
        self.assertFalse(result["final_quality_verified"])


class PersistedListeningTest(unittest.TestCase):
    def test_reload_preserves_feedback_and_detects_replaced_audio(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as folder:
            store = StorageManager(Path(folder))
            song_id = store.create_song_project("Prueba de escucha")["id"]
            root = store.data_dir / "projects" / song_id / "candidates" / "a1"
            root.mkdir(parents=True)
            audio = root / "candidate.wav"
            write_audio(audio)
            evidence = inspect_sample_wav(audio, root)
            artifact = {"artifact_id": "a1", "song_id": song_id, "type": "ace_step_candidate_wav",
                        "file_path": str(audio), "metadata": {"plan_id": "p1", "spec_revision_id": "r1", "audio_evidence": evidence}}
            store.create_task("t1", AceStepCandidateJobs.TASK_TYPE, "music", {"song_id": song_id}, "Prueba")
            store.update_task("t1", "completed", 100, "Listo", {"artifact": artifact})
            jobs = AceStepCandidateJobs(store, Mock(), Mock(), Mock())
            facade = SimpleNamespace(storage=store, ace_candidate_jobs=jobs)
            facade.ace_candidate_audio_file = lambda s, t, checksum: SongService.ace_candidate_audio_file(facade, s, t, checksum)
            ReviewCandidateListening(store, jobs, facade.ace_candidate_audio_file).execute(song_id, "t1", {
                "listened": True, "decision": "changes_requested", "notes": "Cambiar el coro", "audio_sha256": evidence["sha256"]})
            facade.storage = StorageManager(Path(folder))
            plan = Mock()
            plan.latest.return_value = {"plan_id": "p1", "inputs_current": True, "plan": {"spec_revision_id": "r1"}}
            facade._ace_plan_review = lambda: plan
            read = lambda s, t: SongService.latest_candidate_listening_review(facade, s, t)
            review = read(song_id, "t1")["review"]
            self.assertEqual(review["notes"], "Cambiar el coro")
            self.assertTrue(review["audio_current"])
            self.assertTrue(review["inputs_current"])
            write_audio(audio, value=1)
            context = CandidateListeningContext(jobs, read).build(song_id)
            self.assertEqual(context["status"], "audio_unavailable")
            self.assertFalse(context["review"]["audio_current"])
            events = facade.storage.list_song_project_events(song_id)
            saved = [e["payload"]["candidate_listening_review"] for e in events if "candidate_listening_review" in e["payload"]]
            self.assertEqual(len(saved), 1)
            self.assertEqual(saved[0]["audio_sha256"], evidence["sha256"])
            self.assertNotIn("audio_current", saved[0])
            with self.assertRaises(ValueError):
                read("another-project", "t1")
