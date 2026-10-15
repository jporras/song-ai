import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from application.candidate_sample import CreateCandidateSample
from application.song_service import SongService
from application.ace_step_candidate_jobs import AceStepCandidateJobs
from application.sample_gate import SampleGate
from core.storage import StorageManager
from adapters.sample_audio_evidence import inspect_sample_wav
from tests.test_sample_audio_evidence import write_audio
from tests import test_set_validation


class CandidateSampleTest(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.addCleanup(self.folder.cleanup)
        self.store = StorageManager(Path(self.folder.name))
        service = SongService(self.store)
        self.service = service
        service.bootstrap()
        self.set_id = test_set_validation.SetValidationTest().create_valid_set(service).name
        self.song_id = self.store.create_song_project("Sample", f"set:{self.set_id}")["id"]
        directory = self.store.data_dir / "projects" / self.song_id / "candidates" / "a1"
        directory.mkdir(parents=True)
        self.audio = directory / "candidate.wav"
        write_audio(self.audio, value=100)
        self.evidence = inspect_sample_wav(self.audio, directory)
        self.metadata = {"plan_id": "p1", "plan_sha256": "planhash", "spec_revision_id": "r1",
                         "set_id": self.set_id, "set_fingerprint": self.store.set_generation_fingerprint(self.set_id),
                         "task_type": "text2music", "audio_evidence": self.evidence}
        artifact = {"artifact_id": "a1", "song_id": self.song_id, "type": "ace_step_candidate_wav",
                    "file_path": str(self.audio), "metadata": self.metadata}
        self.store.create_task("t1", AceStepCandidateJobs.TASK_TYPE, "music", {"song_id": self.song_id}, "Prueba")
        self.store.update_task("t1", "completed", 100, "Listo", {"artifact": artifact})
        jobs = AceStepCandidateJobs(self.store, Mock(), Mock(), Mock())
        facade = SimpleNamespace(storage=self.store, ace_candidate_jobs=jobs)
        verifier = lambda s, t, checksum: SongService.ace_candidate_audio_file(facade, s, t, checksum)
        self.plans = Mock()
        self.plans.latest.return_value = {"plan_id": "p1", "effective_status": "approved", "plan": {
            "plan_sha256": "planhash", "retained_spec": {"ace_step_config": "acestep-v15-base"}}}
        self.action = CreateCandidateSample(self.store, jobs, self.plans, verifier, inspect_sample_wav)
        self.request = {"set_id": self.set_id, "create_sample_confirmed": True, "audio_sha256": self.evidence["sha256"]}

    def test_copy_persists_pending_sample_and_requires_separate_approval(self):
        sample = self.action.execute(self.song_id, "t1", self.request)["sample"]
        saved = StorageManager(Path(self.folder.name)).list_samples_for_set(self.set_id)[0]
        self.assertEqual(saved["sample_id"], sample["sample_id"])
        self.assertEqual(saved["source_artifact_id"], "a1")
        self.assertEqual(saved["approval_status"], "pending")
        self.assertFalse(saved["representativity_verified"])
        self.assertEqual(self.store.verify_sample_audio(saved)["sha256"], self.evidence["sha256"])
        self.assertEqual(inspect_sample_wav(self.audio, self.audio.parent), self.evidence)
        with self.assertRaises(ValueError):
            self.store.approve_sample(self.set_id, sample["sample_id"])
        self.store.approve_sample(self.set_id, sample["sample_id"], listened=True, audio_sha256=self.evidence["sha256"])
        with self.assertRaisesRegex(ValueError, "produccion real"):
            SampleGate(self.store).require_for_set(self.set_id, real_output=True)

    def test_confirmation_owner_stale_plan_and_changed_audio_block_creation(self):
        for changes in ({"create_sample_confirmed": False}, {"set_id": "other"}, {"audio_sha256": "wrong"}):
            with self.assertRaises(ValueError):
                self.action.execute(self.song_id, "t1", {**self.request, **changes})
        self.plans.latest.return_value["effective_status"] = "stale"
        with self.assertRaises(ValueError):
            self.action.execute(self.song_id, "t1", self.request)
        self.assertEqual(self.store.list_samples_for_set(self.set_id), [])

    def test_legacy_candidate_without_set_provenance_cannot_be_promoted(self):
        task = self.store.list_tasks()[0]
        task["result"]["artifact"]["metadata"].pop("set_fingerprint")
        self.store.update_task("t1", "completed", 100, "Historico", task["result"])
        with self.assertRaisesRegex(ValueError, "no acredita"):
            self.action.execute(self.song_id, "t1", self.request)
        self.assertEqual(self.store.list_samples_for_set(self.set_id), [])

    def test_set_change_during_copy_prevents_persistence(self):
        original_inspector = self.action.inspect_audio
        def inspect_and_change(path, directory):
            evidence = original_inspector(path, directory)
            self.store.save_project_phase_data(self.set_id, "music-plan", {"bpm": 123}, "pending")
            return evidence
        self.action.inspect_audio = inspect_and_change
        with self.assertRaisesRegex(ValueError, "set vigente"):
            self.action.execute(self.song_id, "t1", self.request)
        self.assertEqual(self.store.list_samples_for_set(self.set_id), [])
        self.assertEqual(inspect_sample_wav(self.audio, self.audio.parent), self.evidence)

    def test_evaluation_is_persisted_for_owner_without_approving_sample(self):
        sample = self.action.execute(self.song_id, "t1", self.request)["sample"]
        self.plans.latest.return_value.update(inputs_current=True)
        self.plans.latest.return_value["plan"].update(spec_revision_id="r1", payload={"task_type": "text2music"})
        self.service._ace_plan_review = lambda: self.plans
        report = self.service.evaluate_sample_representativity(self.song_id, sample["sample_id"])["report"]
        self.assertTrue(report["configuration_matches"])
        events = self.store.list_song_project_events(self.song_id)
        persisted = {k: v for k, v in report.items() if k != "assessment_current"}
        self.assertEqual([e["payload"]["sample_representativity"] for e in events if "sample_representativity" in e["payload"]], [persisted])
        recovered = self.service.latest_sample_representativity(self.song_id, sample["sample_id"])["report"]
        self.assertTrue(recovered["assessment_current"])
        self.assertEqual(recovered["audio_sha256"], report["audio_sha256"])
        self.plans.latest.return_value["inputs_current"] = False
        stale = self.service.latest_sample_representativity(self.song_id, sample["sample_id"])["report"]
        self.assertFalse(stale["assessment_current"])
        self.assertFalse(stale["configuration_matches"])
        write_audio(Path(self.folder.name) / "samples" / sample["sample_id"] / "preview.wav", value=1)
        self.assertFalse(self.service.latest_sample_representativity(self.song_id, sample["sample_id"])["report"]["assessment_current"])
        self.assertEqual(len([e for e in self.store.list_song_project_events(self.song_id) if "sample_representativity" in e["payload"]]), 1)
        self.assertEqual(self.store.list_samples_for_set(self.set_id)[0]["approval_status"], "pending")
        other = self.store.create_song_project("Otra produccion", f"set:{self.set_id}")["id"]
        with self.assertRaises(ValueError):
            self.service.evaluate_sample_representativity(other, sample["sample_id"])

    def test_sample_feedback_is_separate_and_changes_revoke_approval(self):
        sample = self.action.execute(self.song_id, "t1", self.request)["sample"]
        request = {"listened": True, "decision": "accepted", "audio_sha256": self.evidence["sha256"]}
        self.service.review_sample_listening(self.song_id, sample["sample_id"], request)
        self.assertTrue(self.service.latest_sample_listening_review(self.song_id, sample["sample_id"])["review"]["review_current"])
        self.assertEqual(self.store.list_samples_for_set(self.set_id)[0]["approval_status"], "pending")
        self.store.approve_sample(self.set_id, sample["sample_id"], listened=True, audio_sha256=self.evidence["sha256"])
        self.service.review_sample_listening(self.song_id, sample["sample_id"], {**request, "decision": "changes_requested", "notes": "La voz necesita mas claridad"})
        reloaded = StorageManager(Path(self.folder.name)).list_samples_for_set(self.set_id)[0]
        self.assertEqual(reloaded["approval_status"], "pending")
        self.assertEqual(reloaded["listening_review"]["notes"], "La voz necesita mas claridad")
        self.assertNotIn("approved_audio_sha256", reloaded)
        with self.assertRaisesRegex(ValueError, "Solicitaste cambios"):
            self.store.approve_sample(self.set_id, sample["sample_id"], listened=True, audio_sha256=self.evidence["sha256"])
        self.service.review_sample_listening(self.song_id, sample["sample_id"], request)
        self.assertEqual(self.store.list_samples_for_set(self.set_id)[0]["approval_status"], "pending")
        events = [e for e in self.store.list_song_project_events(self.song_id) if "sample_listening_review" in e["payload"]]
        self.assertEqual(len(events), 3)
        self.store.save_project_phase_data(self.set_id, "music-plan", {"bpm": 122}, "pending")
        historical = self.service.latest_sample_listening_review(self.song_id, sample["sample_id"])["review"]
        self.assertFalse(historical["review_current"])
        self.assertEqual(historical["decision"], "accepted")
        self.assertEqual(len([e for e in self.store.list_song_project_events(self.song_id) if "sample_listening_review" in e["payload"]]), 3)

    def test_sample_feedback_requires_listening_notes_and_exact_audio(self):
        sample = self.action.execute(self.song_id, "t1", self.request)["sample"]
        for request in ({"decision": "accepted"}, {"listened": True, "decision": "changes_requested"},
                        {"listened": True, "decision": "accepted", "audio_sha256": "wrong"}):
            with self.assertRaises(ValueError):
                self.service.review_sample_listening(self.song_id, sample["sample_id"], request)
        self.assertNotIn("listening_review", self.store.list_samples_for_set(self.set_id)[0])
