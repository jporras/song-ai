import sys
import tempfile
import unittest
import wave
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from adapters.sample_audio_evidence import inspect_sample_wav
from application.song_service import SongService
from application.sample_gate import SampleGate
from core.storage import StorageManager
from tests import test_set_validation


def write_audio(path, value=0):
    with wave.open(str(path), "wb") as audio:
        audio.setnchannels(1)
        audio.setsampwidth(2)
        audio.setframerate(8000)
        audio.writeframes(value.to_bytes(2, "little", signed=True) * 800)


class SampleAudioEvidenceTest(unittest.TestCase):
    def test_wav_integrity_and_directory_isolation(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            directory = root / "sample"
            directory.mkdir()
            audio = directory / "preview.wav"
            write_audio(audio)
            self.assertEqual(inspect_sample_wav(audio, directory)["frames"], 800)
            with self.assertRaises(ValueError):
                inspect_sample_wav(audio, root / "other")
            audio.write_bytes(audio.read_bytes()[:-2])
            with self.assertRaisesRegex(ValueError, "incompleto"):
                inspect_sample_wav(audio, directory)

    def test_registered_audio_approval_and_replacement_require_new_review(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as folder:
            storage = StorageManager(Path(folder))
            service = SongService(storage)
            service.bootstrap()
            set_id = test_set_validation.SetValidationTest().create_valid_set(service).name
            sample_dir = service.sample_builder.create_for_set(set_id)
            audio = sample_dir / "preview.wav"
            write_audio(audio)
            storage.register_sample_audio(set_id, sample_dir.name, audio)
            checksum = storage.legacy_song_repository.get_sample(sample_dir.name)["audio_evidence"]["sha256"]
            with self.assertRaisesRegex(ValueError, "Escucha"):
                storage.approve_sample(set_id, sample_dir.name)
            with self.assertRaises(ValueError):
                storage.approve_sample(set_id, sample_dir.name, listened=True, audio_sha256="old")
            approved = storage.approve_sample(set_id, sample_dir.name, listened=True, audio_sha256=checksum)
            self.assertEqual(service.sample_audio_file(set_id, sample_dir.name, checksum), audio)
            with self.assertRaises(ValueError):
                service.sample_audio_file("other", sample_dir.name, checksum)
            with self.assertRaisesRegex(ValueError, "recarga"):
                service.sample_audio_file(set_id, sample_dir.name, "old")
            self.assertEqual(approved["approved_audio_sha256"], approved["audio_evidence"]["sha256"])
            SampleGate(storage).require_for_set(set_id, real_output=False)
            write_audio(audio, 100)
            with self.assertRaisesRegex(ValueError, "audio del sample cambio"):
                SampleGate(storage).require_for_set(set_id, real_output=False)
            with self.assertRaises(ValueError):
                storage.approve_sample(set_id, sample_dir.name)
            replaced = storage.register_sample_audio(set_id, sample_dir.name, audio)
            self.assertEqual(replaced["approval_status"], "pending")
            self.assertNotIn("approved_audio_sha256", replaced)
            self.assertNotIn("listening_confirmed_at", replaced)
            restarted = StorageManager(Path(folder))
            persisted = restarted.legacy_song_repository.get_sample(sample_dir.name)
            self.assertEqual(persisted["audio_evidence"], replaced["audio_evidence"])
