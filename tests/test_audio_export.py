from dataclasses import replace
from pathlib import Path
import math
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
import wave
from unittest.mock import patch


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = PROJECT_ROOT / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from application.song_service import SongService
from config.settings import Settings
from config.model_settings import LocalModelSettings
from core.storage import StorageManager
from providers.registry import ProviderRegistry
from bootstrap import docker_bootstrap


class AudioExportTest(unittest.TestCase):
    def write_tone_wav(self, path: Path, frequency: float = 220.0, seconds: int = 1) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        sample_rate = 44100
        with wave.open(str(path), "wb") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(sample_rate)
            for frame in range(sample_rate * seconds):
                value = int(7000 * math.sin(2 * math.pi * frequency * frame / sample_rate))
                wav_file.writeframesraw(value.to_bytes(2, byteorder="little", signed=True))

    def test_provider_registry_is_local_only_without_pro_placeholders(self) -> None:
        registry = ProviderRegistry()
        summary = registry.summary()
        names = [
            str(provider["name"])
            for providers in summary.values()
            for provider in providers
        ]

        self.assertFalse(any(name.startswith("pro-") for name in names))
        self.assertIn("local-soundtrack-command", names)
        self.assertIn("local-singing-voice-command", names)
        self.assertEqual(registry.studio_status()["mode"], "local_only")

    def test_docker_bootstrap_creates_named_volume_directories_without_downloads(self) -> None:
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temp_dir:
            temp_path = Path(temp_dir)
            with patch.object(docker_bootstrap, "MODEL_ROOT", temp_path / "models"), patch.object(
                docker_bootstrap,
                "PROVIDER_ROOT",
                temp_path / "providers",
            ), patch.object(docker_bootstrap, "CACHE_ROOT", temp_path / "provider-cache"), patch.object(
                docker_bootstrap,
                "PYTHON_TARGET",
                temp_path / "provider-cache" / "python",
            ), patch.object(docker_bootstrap, "PIP_CACHE", temp_path / "provider-cache" / "pip"), patch.dict(
                os.environ,
                {"SONG_AI_BOOTSTRAP_ON_START": "false"},
                clear=False,
            ):
                summary = docker_bootstrap.run_bootstrap()

            self.assertFalse(summary["enabled"])
            self.assertTrue((temp_path / "models" / "llm").exists())
            self.assertTrue((temp_path / "models" / "huggingface").exists())
            self.assertTrue((temp_path / "providers").exists())
            self.assertTrue((temp_path / "provider-cache" / "python").exists())

    def test_local_tool_wrappers_are_available(self) -> None:
        for tool_name in (
            "musicgen_generate.py",
            "singing_voice_generate.py",
            "check_local_audio_stack.py",
            "use_audio_file.py",
        ):
            result = subprocess.run(
                [sys.executable, str(PROJECT_ROOT / "tools" / tool_name), "--help"],
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)

    def test_legacy_set_json_is_synced_to_sqlite(self) -> None:
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temp_dir:
            storage = StorageManager(Path(temp_dir))
            storage.ensure_project_layout()
            set_dir = Path(temp_dir) / "sets" / "set-legacy"
            set_dir.mkdir(parents=True, exist_ok=True)
            (set_dir / "set.json").write_text(
                """
{
  "set_id": "set-legacy",
  "instrumental_id": "instrumental-legacy",
  "melody_id": "melody-legacy",
  "lyrics_id": "lyrics-legacy",
  "compatibility_data": {"status": "mock_validated"}
}
""".strip()
                + "\n",
                encoding="utf-8",
            )

            result = storage.sync_legacy_sets_to_sqlite()
            indexed = storage.list_indexed_sets()

            self.assertEqual(result["synced_count"], 1)
            self.assertEqual(indexed[0]["set_id"], "set-legacy")
            self.assertEqual(indexed[0]["project_name"], "set-legacy")

    def test_audio_export_contains_song_mock_context_and_stems(self) -> None:
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temp_dir:
            storage = StorageManager(Path(temp_dir))
            service = SongService(storage, Settings.load())
            service.bootstrap()

            pipeline = service.local_pipeline_status()
            system = service.system_status({"status": "idle", "message": "test"})
            phases = service.project_phase_status()
            self.assertFalse(pipeline["ready"])
            self.assertIn("full_song", pipeline["missing"])
            self.assertIn("soundtrack/singing_voice", pipeline["missing"])
            self.assertTrue(system["components"])
            self.assertTrue(phases["phases"])

            result = service.create_default_lullaby_mp3()
            exports_path = Path(str(result["exports_path"]))
            wav_path = exports_path / "final_mix.wav"
            lyrics_path = exports_path / "lyrics.md"
            manifest = storage.read_json(exports_path / "audio_export_manifest.json")

            self.assertTrue(wav_path.exists())
            self.assertTrue((exports_path.parent / "stems" / "instrumental.wav").exists())
            self.assertTrue((exports_path.parent / "stems" / "melody_guide.wav").exists())
            self.assertIn("Duerme suave", lyrics_path.read_text(encoding="utf-8"))
            self.assertEqual(manifest["mode"], "mock_vocal_guide_audio")
            self.assertGreaterEqual(int(manifest["duration_seconds"]), 18)

            with wave.open(str(wav_path), "rb") as wav_file:
                duration = wav_file.getnframes() / wav_file.getframerate()
            self.assertGreaterEqual(duration, 18)

            download_path, filename = service.latest_audio_export_file("wav")
            self.assertEqual(download_path, wav_path)
            self.assertTrue(filename.endswith(".wav"))

    @unittest.skipIf(os.name == "nt" and not shutil.which("ffmpeg"), "ffmpeg no esta disponible en este entorno")
    def test_local_final_song_uses_configured_local_audio_commands(self) -> None:
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temp_dir:
            temp_path = Path(temp_dir)
            instrumental_source = temp_path / "source_instrumental.wav"
            vocals_source = temp_path / "source_vocals.wav"
            self.write_tone_wav(instrumental_source, 220.0)
            self.write_tone_wav(vocals_source, 330.0)

            base_settings = Settings.load()
            local_settings = replace(
                base_settings.local_models,
                soundtrack_command=(
                    f'"{sys.executable}" "{PROJECT_ROOT / "tools" / "use_audio_file.py"}" '
                    f'--input "{instrumental_source}" --output "{{output_path}}"'
                ),
                singing_voice_command=(
                    f'"{sys.executable}" "{PROJECT_ROOT / "tools" / "use_audio_file.py"}" '
                    f'--input "{vocals_source}" --output "{{output_path}}"'
                ),
            )
            settings = replace(base_settings, data_dir=temp_path, local_models=local_settings)
            storage = StorageManager(temp_path)
            service = SongService(storage, settings)
            service.bootstrap()
            service.create_default_lullaby_mp3()

            result = service.generate_local_final_song()

            self.assertEqual(result["mode"], "local_final_song")
            self.assertTrue(Path(str(result["mp3"])).exists())
            self.assertTrue(Path(str(result["wav"])).exists())


if __name__ == "__main__":
    unittest.main()
