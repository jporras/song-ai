import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from application.ace_step_configuration import EditAceStepConfiguration
from core.storage import StorageManager
from adapters.ace_step_source_audio import AceStepSourceAudio
from tests.test_sample_audio_evidence import write_audio


class ConfigurationTest(unittest.TestCase):
    def test_duration_criterion_requires_explicit_save_and_new_confirmation(self):
        editor = EditAceStepConfiguration(self.store)
        for value in (-1, True, float("nan"), 601):
            with self.subTest(value=value), self.assertRaises(ValueError):
                editor.execute(self.song_id, {**self.request, "values": {**self.request["values"], "duration_tolerance_seconds": value}})
        saved = editor.execute(self.song_id, {**self.request, "values": {**self.request["values"], "duration_tolerance_seconds": 0}})
        self.assertEqual(saved["json_spec"]["duration_tolerance_seconds"], 0)
        self.assertEqual(saved["revision"]["user_confirmation_status"], "pending")
        cleared = editor.execute(self.song_id, {"revision_id": saved["revision"]["revision_id"],
                                                "values": {"duration_tolerance_seconds": None}})
        self.assertNotIn("duration_tolerance_seconds", cleared["json_spec"])
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.addCleanup(self.folder.cleanup)
        self.store = StorageManager(Path(self.folder.name))
        self.project = self.store.create_song_project("Idea original")
        self.song_id = self.project["id"]
        self.record = self.store.upsert_song_spec(self.song_id, {"emotion": "tierna", "instruments": ["piano"]},
                                                 True, [], user_confirmation_status="confirmed")
        self.request = {"revision_id": self.record["revision"]["revision_id"],
                        "values": {"task_type": "text2music", "ace_step_config": "acestep-v15-base"}}

    def test_edit_preserves_intent_requires_confirmation_and_rejects_old_revision(self):
        result = EditAceStepConfiguration(self.store).execute(self.song_id, self.request)
        self.assertEqual(result["json_spec"]["emotion"], "tierna")
        self.assertEqual(result["json_spec"]["instruments"], ["piano"])
        self.assertEqual(result["revision"]["user_confirmation_status"], "pending")
        self.assertEqual(result["json_spec"]["_provenance"]["task_type"]["source"], "explicit_user_control")
        reloaded = StorageManager(Path(self.folder.name)).get_song_project(self.song_id)
        self.assertEqual(reloaded["spec"]["revision"]["revision_id"], result["revision"]["revision_id"])
        with self.assertRaisesRegex(ValueError, "revision cambio"):
            EditAceStepConfiguration(self.store).execute(self.song_id, self.request)
        with self.assertRaisesRegex(ValueError, "revision cambio"):
            self.store.upsert_song_spec(self.song_id, {}, True, [], expected_revision_id=self.request["revision_id"])
        self.assertEqual(self.store.get_song_project(self.song_id)["spec"]["json_spec"], result["json_spec"])

    def test_invalid_task_source_types_and_protected_fields_do_not_write(self):
        for values in ({"emotion": "triste"}, {"src_audio": "outside.wav"},
                       {"task_type": "cover", "ace_step_config": "acestep-v15-base", "source_artifact_id": "foreign"},
                       {"task_type": "unknown", "ace_step_config": "acestep-v15-base"},
                       {"task_type": "text2music", "ace_step_config": "acestep-v15-base", "audio_cover_strength": True},
                       {"task_type": "text2music", "ace_step_config": "acestep-v15-base", "target_tracks": ["unknown"]}):
            with self.subTest(values=values), self.assertRaises(ValueError):
                EditAceStepConfiguration(self.store).execute(self.song_id, {**self.request, "values": values})
        self.assertEqual(self.store.get_song_project(self.song_id)["spec"]["revision"]["revision_id"], self.request["revision_id"])

    def test_source_resolved_from_artifact_and_interval_checked_before_save(self):
        directory = self.store.data_dir / "projects" / self.song_id
        directory.mkdir(parents=True)
        audio = directory / "source.wav"
        write_audio(audio)
        self.store.create_song_artifact(artifact_id="source", song_id=self.song_id, phase="INSTRUMENTAL_GENERATION",
                                       artifact_type="source_audio", file_path=str(audio), metadata={})
        edits = {"task_type": "repaint", "ace_step_config": "acestep-v15-base", "source_artifact_id": "source",
                 "repainting_start": 0, "repainting_end": 1}
        editor = EditAceStepConfiguration(self.store, AceStepSourceAudio(self.store.data_dir))
        with self.assertRaisesRegex(ValueError, "duracion"):
            editor.execute(self.song_id, {**self.request, "values": edits})
        edits["repainting_end"] = -1
        record = editor.execute(self.song_id, {**self.request, "values": edits})
        self.assertEqual(record["json_spec"]["src_audio"], str(audio))
