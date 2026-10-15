import sys
import unittest
import tempfile
import json
from pathlib import Path
from unittest.mock import Mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from application.sample_gate import SampleGate
from application.professional_full_song_service import ProfessionalFullSongService
from application.mastering_service import MasteringService
from application.professional_export_service import ProfessionalExportService


class SampleGateTest(unittest.TestCase):
    def setUp(self):
        self.store = Mock()
        self.store.get_indexed_set.return_value = dict(instrumental_id="i", melody_id="m", lyrics_id="l")
        self.store.set_generation_fingerprint.return_value = "current"
        self.sample = dict(sample_id="s", set_id="set1", approval_status="approved",
                           approved_set_fingerprint="current", provider="mock-local")
        self.store.list_samples_for_set.return_value = [self.sample]
        self.gate = SampleGate(self.store)
        self.project = {"user_id": "set:set1", "spec": {"missing_fields": [],
                        "revision": {"user_confirmation_status": "confirmed", "deterministic_valid": True}}}

    def test_unlinked_project_cannot_skip_gate(self):
        with self.assertRaisesRegex(ValueError, "Vincula"):
            self.gate.require_for_project({"user_id": "user"})

    def test_change_request_blocks_even_inconsistent_approved_record(self):
        self.sample["listening_review"] = {"decision": "changes_requested"}
        with self.assertRaisesRegex(ValueError, "cambios solicitados"):
            self.gate.require_for_set("set1", real_output=False)
        self.store.verify_sample_audio.assert_not_called()

    def test_mock_approval_does_not_accredit_real_sample_evidence(self):
        self.assertEqual(self.gate.require_for_set("set1", real_output=False), self.sample)
        with self.assertRaisesRegex(ValueError, "audio real"):
            self.gate.require_for_set("set1", real_output=True)

    def test_full_production_does_not_depend_on_optional_sample(self):
        for sample in ([], [self.sample], [{**self.sample, "approved_set_fingerprint": "old"}],
                       [{**self.sample, "listening_review": {"decision": "changes_requested"}}]):
            with self.subTest(sample=sample):
                self.store.list_samples_for_set.return_value = sample
                self.assertEqual(self.gate.require_for_project(self.project), self.store.get_indexed_set.return_value)
        self.store.list_samples_for_set.assert_not_called()
        self.store.verify_sample_audio.assert_not_called()

    def test_full_production_requires_confirmed_valid_spec_and_valid_assets(self):
        for revision in ({"user_confirmation_status": "pending", "deterministic_valid": True},
                         {"user_confirmation_status": "confirmed", "deterministic_valid": False}):
            with self.subTest(revision=revision), self.assertRaises(ValueError):
                self.gate.require_for_project({**self.project, "spec": {"revision": revision}})
        self.store.validate_song_set_assets.side_effect = ValueError("Falta melodia")
        with self.assertRaisesRegex(ValueError, "melodia"):
            self.gate.require_for_project(self.project)

    def test_master_and_download_without_sample_keep_file_checks(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as folder:
            self.store.data_dir = Path(folder)
            self.store.get_song_project.return_value = {**self.project, "artifacts": []}
            self.store.list_samples_for_set.return_value = []
            with self.assertRaisesRegex(ValueError, "mix.wav"):
                MasteringService(self.store).master("song1")
            with self.assertRaisesRegex(ValueError, "vocals.wav"):
                ProfessionalExportService(self.store).download_file("song1", "final_song_wav")
            self.store.list_samples_for_set.assert_not_called()
            self.store.create_song_artifact.assert_not_called()

    def test_absent_foreign_stale_and_unapproved_samples_are_rejected(self):
        for changes in ({"set_id": "other"}, {"approved_set_fingerprint": "old"},
                        {"approval_status": "pending"}, {"sample_id": "other"}):
            with self.subTest(changes=changes):
                self.store.list_samples_for_set.return_value = [{**self.sample, **changes}]
                with self.assertRaises(ValueError):
                    self.gate.require_for_set("set1", real_output=False, sample_id="s")
        self.store.list_samples_for_set.return_value = []
        with self.assertRaises(ValueError):
            self.gate.require_for_set("set1", real_output=False)

    def test_missing_set_is_rejected_before_sample_lookup(self):
        self.store.get_indexed_set.return_value = None
        with self.assertRaises(ValueError):
            self.gate.require_for_set("set1", real_output=False)
        self.store.list_samples_for_set.assert_not_called()

    def test_direct_full_song_call_is_blocked_before_command_or_file_creation(self):
        service = ProfessionalFullSongService.__new__(ProfessionalFullSongService)
        service.command_template = "configured"
        service.storage = self.store
        self.store.get_song_project.return_value = {"user_id": "set:set1"}
        with self.assertRaisesRegex(ValueError, "ficha"):
            service.generate("song1")
        self.store.create_song_artifact.assert_not_called()

    def test_direct_master_and_export_reject_unconfirmed_and_unlinked_projects(self):
        for owner in ("set:set1", "user"):
            for service_type, action in ((MasteringService, "master"),
                                         (ProfessionalExportService, "export")):
                with self.subTest(owner=owner, action=action):
                    self.store.get_song_project.return_value = {"user_id": owner}
                    service = service_type(self.store)
                    with self.assertRaises(ValueError):
                        getattr(service, action)("song1")
                    self.store.create_song_artifact.assert_not_called()
                    self.store.update_song_project_phase.assert_not_called()

    def test_direct_master_and_export_reject_missing_project(self):
        self.store.get_song_project.return_value = None
        for service_type, action in ((MasteringService, "master"),
                                     (ProfessionalExportService, "export")):
            with self.subTest(action=action), self.assertRaisesRegex(ValueError, "no encontrado"):
                getattr(service_type(self.store), action)("missing")

    def test_final_downloads_cannot_bypass_spec_confirmation(self):
        self.store.get_song_project.return_value = {"user_id": "set:set1"}
        service = ProfessionalExportService(self.store)
        for kind in ("final_song_mp3", "final_song_wav", "final_song_flac", "project_zip"):
            with self.subTest(kind=kind), self.assertRaisesRegex(ValueError, "ficha"):
                service.download_file("song1", kind)
        self.store.verify_song_artifact.assert_not_called()

    def test_old_manifest_does_not_override_current_input_readiness(self):
        with tempfile.TemporaryDirectory() as folder:
            self.store.data_dir = Path(folder)
            directory = Path(folder) / "projects" / "song1"
            directory.mkdir(parents=True)
            manifest = directory / "export_manifest.json"
            original = json.dumps({"quality": {"export_ready": True}, "artifacts": []})
            manifest.write_text(original, encoding="utf-8")
            self.store.get_song_project.return_value = {"user_id": "set:set1", "artifacts": []}
            result = ProfessionalExportService(self.store).get("song1")
            self.assertFalse(result["quality"]["export_ready"])
            self.assertIn("ficha", result["quality"]["message"])
            self.assertEqual(manifest.read_text(encoding="utf-8"), original)
