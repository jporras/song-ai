import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from application.ace_step_candidate_jobs import AceStepCandidateJobs
from core.storage import StorageManager
from application.song_service import SongService
from application.audio_cancellation import AudioCancelled
from application.model_orchestrator import ModelOrchestrator
from providers.registry import ProviderRegistry
from audio.execution_lock import exclusive_audio
from adapters.sample_audio_evidence import inspect_sample_wav
from tests.test_sample_audio_evidence import write_audio


class CandidateJobsTest(unittest.TestCase):
    def test_direct_registry_calls_obey_audio_guard_and_resume_after_cancel(self):
        registry = ProviderRegistry()
        orchestrator = ModelOrchestrator(self.store, registry)
        registry.inference_guard = orchestrator.require_planning_available
        provider = Mock()
        provider.interpret.return_value = {"summary": "Propuesta"}
        registry.interpreter_providers = [provider]
        registry.technical_providers = [provider]
        task = self.jobs.start("song", self.request)
        for method in (registry.interpret_with_active_provider, registry.technical_with_active_provider):
            with self.assertRaisesRegex(ValueError, "audio activo"):
                method("idea", "song")
        provider.interpret.assert_not_called()
        self.jobs.cancel("song", task["task_id"])
        with exclusive_audio(), self.assertRaisesRegex(ValueError, "audio activo"):
            registry.technical_with_active_provider("idea", "song")
        self.assertEqual(registry.interpret_with_active_provider("idea", "song")["summary"], "Propuesta")
    def test_orchestrator_pauses_and_resumes_from_persisted_job_state(self):
        registry = Mock()
        registry.active_providers.return_value = {}
        orchestrator = ModelOrchestrator(self.store, registry)
        jobs = AceStepCandidateJobs(self.store, self.generate, self.review, self.dispatcher, orchestrator=orchestrator)
        task = jobs.start("song", self.request)
        self.assertEqual(orchestrator.status()["assistant_state"], "suspended_for_audio")
        self.assertIsNone(orchestrator.status()["active_model"])
        with self.assertRaisesRegex(ValueError, "audio activo"):
            orchestrator.run_handoff({"model_role": "technical"})
        self.dispatcher.submit.call_args.args[0]()
        self.assertIsNone(orchestrator.active_audio_task())
        events = self.store.list_project_events("song")
        self.assertEqual({event["status"] for event in events}, {"suspended", "resumed"})
        self.assertTrue(all(event["task_id"] == task["task_id"] for event in events))

    def test_gemma_does_not_invoke_model_while_audio_is_active(self):
        self.jobs.start("song", self.request)
        facade = SimpleNamespace(model_orchestrator=ModelOrchestrator(self.store, Mock()))
        response = SongService.gemma_assistant(facade, {"question": "Que sigue?"})
        self.assertEqual(response["status"], "suspended_for_audio")
        self.assertEqual(response["mode"], "sqlite_guidance")
    def test_preflight_failure_does_not_create_job_or_dispatch(self):
        check = Mock(side_effect=ValueError("Faltan archivos"))
        jobs = AceStepCandidateJobs(self.store, self.generate, self.review, self.dispatcher, preflight=check)
        with self.assertRaisesRegex(ValueError, "Faltan archivos"):
            jobs.start("song", self.request)
        self.assertEqual(self.store.list_tasks(), [])
        self.dispatcher.submit.assert_not_called()
    def test_pending_cancel_does_not_start_model_and_cannot_cross_projects(self):
        task = self.jobs.start("song", self.request)
        with self.assertRaises(ValueError):
            self.jobs.cancel("other", task["task_id"])
        self.assertEqual(self.jobs.cancel("song", task["task_id"])["status"], "cancelled")
        self.dispatcher.submit.call_args.args[0]()
        self.generate.assert_not_called()
        self.assertEqual(self.jobs.get("song", task["task_id"])["status"], "cancelled")
        self.assertEqual(self.store.list_model_runs(), [])

    def test_running_cancellation_is_distinct_from_provider_failure(self):
        task = self.jobs.start("song", self.request)
        def generate(song_id, request, cancellation_check):
            self.assertEqual(self.jobs.cancel(song_id, task["task_id"])["status"], "cancelling")
            cancellation_check()
        self.generate.side_effect = generate
        self.dispatcher.submit.call_args.args[0]()
        self.assertEqual(self.jobs.get("song", task["task_id"])["status"], "cancelled")
        self.assertEqual(self.store.list_model_runs()[0]["status"], "cancelled")
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.addCleanup(self.folder.cleanup)
        self.store = StorageManager(Path(self.folder.name))
        self.review = Mock()
        self.review.latest.return_value = {"plan_id": "p1", "effective_status": "approved", "plan": {"plan_sha256": "hash"}}
        self.generate = Mock(return_value={"quality_status": "exploratory_candidate", "sample_approved": False})
        self.dispatcher = Mock()
        self.jobs = AceStepCandidateJobs(self.store, self.generate, self.review, self.dispatcher)
        self.request = {"plan_sha256": "hash", "exploratory_audio_authorized": True}

    def test_job_is_persisted_before_dispatch_and_isolated_by_project(self):
        task = self.jobs.start("song", self.request)
        self.assertEqual(task["status"], "pending")
        self.generate.assert_not_called()
        with self.assertRaisesRegex(ValueError, "en curso"):
            self.jobs.start("song", self.request)
        with self.assertRaises(ValueError):
            self.jobs.get("other", task["task_id"])
        self.dispatcher.submit.call_args.args[0]()
        completed = self.jobs.get("song", task["task_id"])
        self.assertEqual(completed["status"], "completed")
        self.assertFalse(completed["result"]["sample_approved"])
        self.assertEqual(self.generate.call_args.args[1]["plan_id"], "p1")
        self.assertEqual(self.store.list_model_runs()[0]["status"], "completed")
        restored = StorageManager(Path(self.folder.name)).list_tasks()[0]
        self.assertEqual(restored["task_id"], task["task_id"])

    def test_failures_and_restart_are_observable(self):
        task = self.jobs.start("song", self.request)
        self.generate.side_effect = ValueError("El plan cambio")
        self.dispatcher.submit.call_args.args[0]()
        failed = self.jobs.get("song", task["task_id"])
        self.assertEqual(failed["status"], "failed")
        self.assertEqual(failed["result"]["error"], "El plan cambio")
        pending = self.jobs.start("song", self.request)
        self.jobs.recover_interrupted()
        self.assertTrue(self.jobs.get("song", pending["task_id"])["result"]["interrupted"])
        self.assertEqual(self.store.list_model_runs()[0]["status"], "failed")

    def test_playback_checks_project_and_recorded_audio_checksum(self):
        directory = self.store.data_dir / "projects" / "song" / "candidates" / "candidate1"
        directory.mkdir(parents=True)
        audio = directory / "candidate.wav"
        write_audio(audio)
        evidence = inspect_sample_wav(audio, directory)
        artifact = {"artifact_id": "candidate1", "song_id": "song", "type": "ace_step_candidate_wav",
                    "file_path": str(audio), "metadata": {"audio_evidence": evidence}}
        task = self.jobs.start("song", self.request)
        self.store.update_task(task["task_id"], "completed", 100, "Borrador creado", {"artifact": artifact})
        facade = SimpleNamespace(storage=self.store, ace_candidate_jobs=self.jobs)
        self.assertEqual(SongService.ace_candidate_audio_file(facade, "song", task["task_id"], evidence["sha256"]), audio)
        with self.assertRaises(ValueError):
            SongService.ace_candidate_audio_file(facade, "other", task["task_id"], evidence["sha256"])
        with self.assertRaises(ValueError):
            SongService.ace_candidate_audio_file(facade, "song", task["task_id"], "old")
        write_audio(audio, 1)
        with self.assertRaisesRegex(ValueError, "cambio"):
            SongService.ace_candidate_audio_file(facade, "song", task["task_id"], evidence["sha256"])
