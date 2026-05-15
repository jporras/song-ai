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
from audio.local_song_pipeline import LocalSongPipeline
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

    def test_professional_song_project_starts_in_spec_collection(self) -> None:
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temp_dir:
            storage = StorageManager(Path(temp_dir))
            service = SongService(storage)
            service.bootstrap()

            created = service.create_professional_project({"title": "Cancion de cuna para Isabella"})
            project = created["project"]

            self.assertEqual(created["progress"]["current"], 1)
            self.assertEqual(created["progress"]["total"], 11)
            self.assertEqual(project["current_phase"], "SONG_SPEC_COLLECTION")
            self.assertEqual(project["status"], "waiting_user_input")
            self.assertEqual(len(project["events"]), 1)
            self.assertIn("Gemma", project["events"][0]["message"])

    def test_professional_spec_collection_routes_gemma_to_qwen(self) -> None:
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temp_dir:
            storage = StorageManager(Path(temp_dir))
            service = SongService(storage)
            service.bootstrap()
            created = service.create_professional_project({"title": "Cancion de cuna para Isabella"})
            song_id = str(created["project"]["id"])

            first = service.collect_professional_spec(
                song_id,
                {"message": "Quiero una cancion de cuna dulce para Isabella."},
            )

            self.assertEqual(first["qwen"]["status"], "missing_information")
            self.assertIn("duration_seconds", first["qwen"]["missing_fields"])
            self.assertIn("voice_style", first["qwen"]["missing_fields"])
            self.assertIn("Gemma", first["project"]["events"][0]["message"])

            second = service.collect_professional_spec(
                song_id,
                {
                    "message": (
                        "Que dure 120 segundos, voz femenina suave, piano, cuerdas y pad, "
                        "muy lenta a 70 bpm en C major, estructura intro verso coro puente outro y salida mp3."
                    )
                },
            )

            self.assertEqual(second["qwen"]["status"], "ready_for_generation")
            self.assertEqual(second["progress"]["current"], 2)
            self.assertEqual(second["spec"]["json_spec"]["duration_seconds"], 120)
            self.assertTrue((Path(temp_dir) / "projects" / song_id / "song_spec.json").exists())

    def test_professional_lyrics_generation_creates_editable_artifacts(self) -> None:
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temp_dir:
            storage = StorageManager(Path(temp_dir))
            service = SongService(storage)
            service.bootstrap()
            created = service.create_professional_project({"title": "Cancion de cuna para Isabella"})
            song_id = str(created["project"]["id"])
            service.collect_professional_spec(
                song_id,
                {
                    "message": (
                        "Cancion de cuna para Isabella, 120 segundos, voz femenina suave, piano, "
                        "cuerdas y pad, muy lenta a 70 bpm en C major, estructura intro verso coro puente outro y salida mp3."
                    )
                },
            )

            generated = service.generate_professional_lyrics(song_id)
            lyrics = service.get_professional_lyrics(song_id)

            self.assertEqual(generated["progress"]["current"], 3)
            self.assertIn("## Intro", lyrics["markdown"])
            self.assertIn("Isabella", lyrics["markdown"])
            self.assertTrue((Path(temp_dir) / "projects" / song_id / "lyrics.json").exists())
            self.assertTrue((Path(temp_dir) / "projects" / song_id / "lyrics.md").exists())

            edited = service.update_professional_lyrics(
                song_id,
                {"content": "# Cancion editada\n\n## Verse 1\nIsabella, duerme con calma\n"},
            )

            self.assertEqual(edited["lyrics"]["title"], "Cancion editada")
            self.assertIn("duerme con calma", service.get_professional_lyrics(song_id)["markdown"])

    def test_professional_lyrics_review_approves_complete_lyrics(self) -> None:
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temp_dir:
            storage = StorageManager(Path(temp_dir))
            service = SongService(storage)
            service.bootstrap()
            created = service.create_professional_project({"title": "Cancion de cuna para Isabella"})
            song_id = str(created["project"]["id"])
            service.collect_professional_spec(
                song_id,
                {
                    "message": (
                        "Cancion de cuna para Isabella, 120 segundos, voz femenina suave, piano, "
                        "cuerdas y pad, muy lenta a 70 bpm en C major, estructura intro verse chorus verse bridge outro y salida mp3."
                    )
                },
            )
            service.generate_professional_lyrics(song_id)

            reviewed = service.review_professional_lyrics(song_id)

            self.assertEqual(reviewed["review"]["status"], "approved")
            self.assertEqual(reviewed["progress"]["current"], 4)
            self.assertTrue((Path(temp_dir) / "projects" / song_id / "lyrics_approved.json").exists())

    def test_professional_lyrics_review_returns_to_editing_when_too_short(self) -> None:
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temp_dir:
            storage = StorageManager(Path(temp_dir))
            service = SongService(storage)
            service.bootstrap()
            created = service.create_professional_project({"title": "Cancion de cuna para Isabella"})
            song_id = str(created["project"]["id"])
            service.collect_professional_spec(
                song_id,
                {
                    "message": (
                        "Cancion de cuna para Isabella, 120 segundos, voz femenina suave, piano, "
                        "cuerdas y pad, muy lenta a 70 bpm en C major, estructura intro verse chorus bridge outro y salida mp3."
                    )
                },
            )
            service.generate_professional_lyrics(song_id)
            service.update_professional_lyrics(song_id, {"content": "# Borrador\n\n## Verse 1\nUna linea sola\n"})

            reviewed = service.review_professional_lyrics(song_id)

            self.assertEqual(reviewed["review"]["status"], "needs_revision")
            self.assertEqual(reviewed["progress"]["current"], 2)
            self.assertIn("too_few_sections", [issue["code"] for issue in reviewed["review"]["issues"]])

    def test_professional_music_plan_generation_prepares_midi_requirements(self) -> None:
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temp_dir:
            storage = StorageManager(Path(temp_dir))
            service = SongService(storage)
            service.bootstrap()
            created = service.create_professional_project({"title": "Cancion de cuna para Isabella"})
            song_id = str(created["project"]["id"])
            service.collect_professional_spec(
                song_id,
                {
                    "message": (
                        "Cancion de cuna para Isabella, 120 segundos, voz femenina suave, piano, "
                        "cuerdas y pad, muy lenta a 70 bpm en C major, estructura intro verse chorus verse bridge outro y salida mp3."
                    )
                },
            )
            service.generate_professional_lyrics(song_id)
            service.review_professional_lyrics(song_id)

            generated = service.generate_professional_music_plan(song_id)
            plan = service.get_professional_music_plan(song_id)

            self.assertEqual(generated["progress"]["current"], 5)
            self.assertEqual(generated["project"]["current_phase"], "MIDI_GENERATION")
            self.assertEqual(plan["music_plan"]["bpm"], 70)
            self.assertEqual(plan["music_plan"]["key"], "C major")
            self.assertTrue(plan["music_plan"]["midi_requirements"]["must_include_vocal_melody"])
            self.assertGreaterEqual(len(plan["music_plan"]["structure_timeline"]), 5)
            self.assertTrue((Path(temp_dir) / "projects" / song_id / "music_plan.json").exists())

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

    def test_docker_bootstrap_markers_skip_existing_installs(self) -> None:
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temp_dir:
            temp_path = Path(temp_dir)
            marker = temp_path / "provider-cache" / ".ace-step.installed"
            package = "git+https://github.com/ace-step/ACE-Step.git"
            marker.parent.mkdir(parents=True, exist_ok=True)
            marker.write_text(f"{package}\npython={sys.version.split()[0]}\n", encoding="utf-8")
            with patch.object(docker_bootstrap, "CACHE_ROOT", temp_path / "provider-cache"), patch.object(
                docker_bootstrap,
                "ACE_STEP_MARKER",
                marker,
            ), patch.dict(
                os.environ,
                {
                    "SONG_AI_BOOTSTRAP_UPGRADE": "false",
                    "SONG_AI_ACE_STEP_PACKAGE": package,
                },
                clear=False,
            ), patch.object(docker_bootstrap, "ace_step_ready", return_value=True), patch("subprocess.run") as run:
                installed = docker_bootstrap.install_ace_step(upgrade=False)

            self.assertFalse(installed)
            run.assert_not_called()

    def test_docker_bootstrap_marker_reinstalls_when_modules_are_missing(self) -> None:
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temp_dir:
            temp_path = Path(temp_dir)
            marker = temp_path / "provider-cache" / ".ace-step.installed"
            package = "git+https://github.com/ace-step/ACE-Step.git"
            marker.parent.mkdir(parents=True, exist_ok=True)
            marker.write_text(f"{package}\npython={sys.version.split()[0]}\n", encoding="utf-8")
            with patch.object(docker_bootstrap, "PIP_CACHE", temp_path / "provider-cache" / "pip"), patch.object(
                docker_bootstrap,
                "PYTHON_TARGET",
                temp_path / "provider-cache" / "python",
            ), patch.object(
                docker_bootstrap,
                "ACE_STEP_MARKER",
                marker,
            ), patch.dict(
                os.environ,
                {
                    "SONG_AI_BOOTSTRAP_UPGRADE": "false",
                    "SONG_AI_ACE_STEP_PACKAGE": package,
                },
                clear=False,
            ), patch.object(docker_bootstrap, "modules_available", return_value=False), patch.object(
                docker_bootstrap,
                "ace_step_ready",
                return_value=False,
            ), patch("subprocess.run") as run:
                installed = docker_bootstrap.install_ace_step(upgrade=False)

            self.assertTrue(installed)
            run.assert_called_once()

    def test_docker_bootstrap_existing_modules_create_marker_without_reinstall(self) -> None:
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temp_dir:
            temp_path = Path(temp_dir)
            marker = temp_path / "provider-cache" / ".ace-step.installed"
            package = "git+https://github.com/ace-step/ACE-Step.git"
            with patch.object(docker_bootstrap, "ACE_STEP_MARKER", marker), patch.dict(
                os.environ,
                {
                    "SONG_AI_BOOTSTRAP_UPGRADE": "false",
                    "SONG_AI_ACE_STEP_PACKAGE": package,
                },
                clear=False,
            ), patch.object(docker_bootstrap, "ace_step_ready", return_value=True), patch("subprocess.run") as run:
                installed = docker_bootstrap.install_ace_step(upgrade=False)

            self.assertFalse(installed)
            self.assertTrue(marker.exists())
            self.assertIn(package, marker.read_text(encoding="utf-8"))
            run.assert_not_called()

    def test_docker_bootstrap_repairs_local_audio_deps_when_compatibility_probe_fails(self) -> None:
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temp_dir:
            temp_path = Path(temp_dir)
            marker = temp_path / "provider-cache" / ".local-audio-deps.installed"
            marker.parent.mkdir(parents=True, exist_ok=True)
            requirements = temp_path / "requirements-local-audio.txt"
            requirements.write_text("huggingface_hub>=0.34.0,<1.0\n", encoding="utf-8")
            marker.write_text(f"{requirements.read_text(encoding='utf-8')}\npython={sys.version.split()[0]}\n", encoding="utf-8")
            with patch.object(docker_bootstrap, "LOCAL_AUDIO_MARKER", marker), patch.object(
                docker_bootstrap,
                "PIP_CACHE",
                temp_path / "provider-cache" / "pip",
            ), patch.object(
                docker_bootstrap,
                "PYTHON_TARGET",
                temp_path / "provider-cache" / "python",
            ), patch("pathlib.Path.exists", return_value=True), patch(
                "pathlib.Path.read_text",
                return_value=requirements.read_text(encoding="utf-8"),
            ), patch.object(docker_bootstrap, "modules_available", return_value=True), patch.object(
                docker_bootstrap,
                "local_audio_deps_ready",
                return_value=False,
            ), patch("subprocess.run") as run:
                installed = docker_bootstrap.install_local_audio_deps(upgrade=False)

            self.assertTrue(installed)
            self.assertIn("--upgrade", run.call_args.args[0])
            self.assertIn("huggingface_hub>=0.34.0,<1.0", run.call_args.args[0])
            self.assertNotIn("-r", run.call_args.args[0])

    def test_docker_bootstrap_upgrade_ignores_existing_markers(self) -> None:
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temp_dir:
            temp_path = Path(temp_dir)
            marker = temp_path / "provider-cache" / ".ace-step.installed"
            package = "git+https://github.com/ace-step/ACE-Step.git"
            marker.parent.mkdir(parents=True, exist_ok=True)
            marker.write_text(package, encoding="utf-8")
            with patch.object(docker_bootstrap, "CACHE_ROOT", temp_path / "provider-cache"), patch.object(
                docker_bootstrap,
                "PIP_CACHE",
                temp_path / "provider-cache" / "pip",
            ), patch.object(
                docker_bootstrap,
                "PYTHON_TARGET",
                temp_path / "provider-cache" / "python",
            ), patch.object(
                docker_bootstrap,
                "ACE_STEP_MARKER",
                marker,
            ), patch.dict(
                os.environ,
                {"SONG_AI_ACE_STEP_PACKAGE": package},
                clear=False,
            ), patch("subprocess.run") as run:
                installed = docker_bootstrap.install_ace_step(upgrade=True)

            self.assertTrue(installed)
            self.assertIn("--upgrade", run.call_args.args[0])

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

    def test_local_pipeline_does_not_report_ace_step_ready_when_module_is_missing(self) -> None:
        base_settings = Settings.load()
        local_settings = replace(
            base_settings.local_models,
            full_song_command="python tools/acestep_generate.py --output {output_path}",
            soundtrack_command="",
            singing_voice_command="",
        )
        pipeline = LocalSongPipeline(local_settings)

        with patch.object(pipeline, "_full_song_command_available", return_value=False):
            status = pipeline.status()

        full_song = next(item for item in status.requirements if item["role"] == "full_song")
        self.assertFalse(status.ready)
        self.assertFalse(full_song["configured"])
        self.assertIn("ACE-Step", str(full_song["detail"]))

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

            with self.assertRaisesRegex(ValueError, "maqueta tecnica"):
                service.latest_audio_export_file("wav")

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
            download_path, filename = service.latest_audio_export_file("mp3")
            self.assertEqual(download_path, Path(str(result["mp3"])))
            self.assertTrue(filename.endswith(".mp3"))


if __name__ == "__main__":
    unittest.main()
