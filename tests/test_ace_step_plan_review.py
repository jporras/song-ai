import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from adapters.sqlite.ace_step_plan_repository import AceStepPlanRepository
from application.ace_step_plan_compiler import PreviewAceStepPlan
from application.ace_step_plan_review import ReviewAceStepPlan
from core.storage import StorageManager
from adapters.ace_step_source_audio import AceStepSourceAudio
from tests.test_sample_audio_evidence import write_audio
from application.professional_full_song_service import ProfessionalFullSongService
from audio.ace_step_profiles import resolve_ace_step_profile
from tests import test_ace_step_plan_compiler


class PlanReviewTest(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.addCleanup(self.folder.cleanup)
        self.store = StorageManager(Path(self.folder.name))
        self.song_id = self.store.create_song_project("Idea")["id"]
        fixture = test_ace_step_plan_compiler.AceStepPlanCompilerTest()
        fixture.setUp()
        self.spec = fixture.record["json_spec"]
        self.store.upsert_song_spec(self.song_id, self.spec, True, [], user_confirmation_status="confirmed")
        self.repo = AceStepPlanRepository(self.store.db_path)
        self.review = ReviewAceStepPlan(PreviewAceStepPlan(self.store), self.repo)

    def test_approval_persistence_isolation_and_idempotency(self):
        item = self.review.prepare(self.song_id, "Letra aprobada")
        request = {"plan_sha256": item["plan"]["plan_sha256"], "lyrics_confirmed": True}
        with self.assertRaises(ValueError):
            self.review.approve(self.song_id, item["plan_id"], {**request, "lyrics_confirmed": False})
        with self.assertRaises(ValueError):
            self.review.approve(self.song_id, item["plan_id"], {**request, "plan_sha256": "old"})
        with self.assertRaises(ValueError):
            self.review.approve("other", item["plan_id"], request)
        approved = self.review.approve(self.song_id, item["plan_id"], request)
        self.assertEqual(approved["status"], "approved")
        self.assertEqual(self.review.approve(self.song_id, item["plan_id"], request)["approved_at"], approved["approved_at"])
        restored = AceStepPlanRepository(self.store.db_path).latest(self.song_id)
        self.assertEqual(restored["plan"], item["plan"])
        self.assertFalse(self.review.latest(self.song_id)["ready_for_execution"])

    def test_creative_changes_mark_approved_plan_stale(self):
        item = self.review.prepare(self.song_id, "Letra")
        request = {"plan_sha256": item["plan"]["plan_sha256"], "lyrics_confirmed": True}
        self.review.approve(self.song_id, item["plan_id"], request)
        self.store.upsert_song_spec(self.song_id, {**self.spec, "bpm": 80}, True, [], user_confirmation_status="confirmed")
        self.assertEqual(self.review.latest(self.song_id)["effective_status"], "stale")
        self.assertEqual(self.repo.get(self.song_id, item["plan_id"])["status"], "approved")
        with self.assertRaises(ValueError):
            self.review.approve(self.song_id, item["plan_id"], request)
        with self.assertRaises(ValueError):
            self.repo.approve(self.song_id, item["plan_id"], item["plan"]["spec_revision_id"], item["plan"]["plan_sha256"])

    def test_project_deletion_removes_only_its_plans(self):
        self.review.prepare(self.song_id, "Letra")
        other_id = self.store.create_song_project("Otro")["id"]
        self.store.upsert_song_spec(other_id, self.spec, True, [], user_confirmation_status="confirmed")
        other_plan = self.review.prepare(other_id, "Otra letra")
        self.store.song_workflow_repository.delete_project(self.song_id)
        self.assertIsNone(self.repo.latest(self.song_id))
        self.assertEqual(self.repo.latest(other_id)["plan_id"], other_plan["plan_id"])

    def test_final_command_uses_approved_plan_and_exact_project_lyrics(self):
        self.spec["ace_step_config"] = "acestep-v15-base"
        self.store.upsert_song_spec(self.song_id, self.spec, True, [], user_confirmation_status="confirmed")
        item = self.review.prepare(self.song_id, "Letra exacta")
        service = ProfessionalFullSongService(self.store, command_template="python tools/acestep_generate.py")
        directory = self.store.data_dir / "projects" / self.song_id
        directory.mkdir(parents=True)
        (directory / "lyrics.md").write_text("Letra exacta", encoding="utf-8")
        profile = resolve_ace_step_profile("base")
        with self.assertRaisesRegex(ValueError, "aprueba"):
            service._approved_execution(self.song_id, profile, directory, directory / "final.wav")
        self.review.approve(self.song_id, item["plan_id"], {"lyrics_confirmed": True, "plan_sha256": item["plan"]["plan_sha256"]})
        approved, argv = service._approved_execution(self.song_id, profile, directory, directory / "final.wav")
        self.assertEqual(approved["plan_id"], item["plan_id"])
        self.assertEqual(argv[argv.index("--bpm") + 1], str(self.spec["bpm"]))
        (directory / "lyrics.md").write_text("Otra letra", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "no coincide"):
            service._approved_execution(self.song_id, profile, directory, directory / "final.wav")

    def test_source_replacement_invalidates_plan_before_approval(self):
        directory = self.store.data_dir / "projects" / self.song_id
        directory.mkdir(parents=True, exist_ok=True)
        audio = directory / "source.wav"
        write_audio(audio)
        self.store.create_song_artifact(artifact_id="source", song_id=self.song_id, phase="INSTRUMENTAL_GENERATION",
                                       artifact_type="source_audio", file_path=str(audio), metadata={})
        self.store.upsert_song_spec(self.song_id, {**self.spec, "task_type": "cover", "ace_step_config": "acestep-v15-base",
                                  "src_audio": str(audio), "source_artifact_id": "source"}, True, [],
                                  user_confirmation_status="confirmed")
        review = ReviewAceStepPlan(PreviewAceStepPlan(self.store, AceStepSourceAudio(self.store.data_dir)), self.repo)
        item = review.prepare(self.song_id, "Letra")
        write_audio(audio, 100)
        self.assertEqual(review.latest(self.song_id)["effective_status"], "stale")
        with self.assertRaisesRegex(ValueError, "inputs"):
            review.approve(self.song_id, item["plan_id"], {"lyrics_confirmed": True, "plan_sha256": item["plan"]["plan_sha256"]})
