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
import importlib.util
from types import SimpleNamespace
from unittest.mock import patch


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = PROJECT_ROOT / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from application.song_service import SongService
from application.professional_full_song_service import ProfessionalFullSongService
from audio.ace_step_profiles import BASE_PROFILE, TURBO_PROFILE
from audio.local_song_pipeline import LocalSongPipeline
from audio.mock_song_renderer import MockSongRenderContext
from config.resource_settings import ResourceMonitorSettings
from config.settings import Settings
from config.model_settings import LocalModelSettings
from core.storage import StorageManager
from providers.registry import ProviderRegistry
from bootstrap import provider_bootstrap


ACESTEP_GENERATE_SPEC = importlib.util.spec_from_file_location(
    "acestep_generate",
    PROJECT_ROOT / "tools" / "acestep_generate.py",
)
acestep_generate = importlib.util.module_from_spec(ACESTEP_GENERATE_SPEC)
assert ACESTEP_GENERATE_SPEC.loader is not None
ACESTEP_GENERATE_SPEC.loader.exec_module(acestep_generate)


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

    def confirm_current_spec(self, service: SongService, song_id: str) -> dict[str, object]:
        current = service.get_professional_specification(song_id)
        return service.confirm_professional_specification(
            song_id,
            {"revision_id": current["spec"]["revision"]["revision_id"]},
        )

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
            self.assertEqual(second["progress"]["current"], 1)
            self.assertEqual(second["spec"]["json_spec"]["duration_seconds"], 120)
            self.assertTrue((Path(temp_dir) / "projects" / song_id / "song_spec.json").exists())
            self.assertTrue((Path(temp_dir) / "projects" / song_id / "song_spec.md").exists())
            self.assertEqual(second["qwen"]["validation_basis"], "deterministic_rules")
            self.assertFalse(second["qwen"]["model_review_executed"])
            self.assertEqual(second["spec"]["revision"]["revision_number"], 2)
            self.assertIn(second["spec"]["revision"]["technical_review_mode"], {"mock_handoff", "mock_handoff_after_provider_error", "provider_review"})
            self.assertEqual(second["spec"]["revision"]["user_confirmation_status"], "pending")
            self.assertTrue(second["qwen"]["handoff_task_id"])

            specification = service.get_professional_specification(song_id)
            self.assertEqual(len(specification["revisions"]), 2)
            self.assertGreater(specification["catalog"]["summary"]["total"], 20)
            self.assertEqual(
                specification["catalog"]["summary"]["required_decided"],
                specification["catalog"]["summary"]["required"],
            )
            idea_group = next(group for group in specification["catalog"]["groups"] if group["id"] == "idea")
            recipient = next(field for field in idea_group["fields"] if field["id"] == "recipient_name")
            self.assertEqual(recipient["value"], "Isabella")
            self.assertEqual(recipient["coverage_status"], "decided")
            self.assertEqual(recipient["source"], "extracted_from_user_message")

            with self.assertRaisesRegex(ValueError, "confirma la ficha completa"):
                service.generate_professional_lyrics(song_id)

            confirmed = service.confirm_professional_specification(
                song_id,
                {"revision_id": second["spec"]["revision"]["revision_id"]},
            )
            self.assertEqual(confirmed["spec"]["revision"]["revision_number"], 3)
            self.assertEqual(confirmed["spec"]["revision"]["user_confirmation_status"], "confirmed")
            self.assertEqual(len(confirmed["revisions"]), 3)
            self.assertEqual(confirmed["progress"]["current"], 2)

            with self.assertRaisesRegex(ValueError, "revision cambio"):
                service.confirm_professional_specification(
                    song_id,
                    {"revision_id": second["spec"]["revision"]["revision_id"]},
                )

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

            self.confirm_current_spec(service, song_id)
            generated = service.generate_professional_lyrics(song_id)
            lyrics = service.get_professional_lyrics(song_id)

            self.assertEqual(generated["progress"]["current"], 3)
            self.assertIn("## Intro", lyrics["markdown"])
            self.assertIn("Isabella", lyrics["markdown"])
            self.assertNotIn("tender", lyrics["markdown"].lower())
            self.assertNotIn("love, care", lyrics["markdown"].lower())
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
            self.confirm_current_spec(service, song_id)
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
            self.confirm_current_spec(service, song_id)
            service.generate_professional_lyrics(song_id)
            service.update_professional_lyrics(song_id, {"content": "# Borrador\n\n## Verse 1\nUna linea sola\n"})

            reviewed = service.review_professional_lyrics(song_id)

            self.assertEqual(reviewed["review"]["status"], "needs_revision")
            self.assertEqual(reviewed["progress"]["current"], 2)
            self.assertIn("too_few_sections", [issue["code"] for issue in reviewed["review"]["issues"]])

    def test_professional_lyrics_review_rejects_technical_tokens(self) -> None:
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
            self.confirm_current_spec(service, song_id)
            service.generate_professional_lyrics(song_id)
            service.update_professional_lyrics(
                song_id,
                {
                    "content": (
                        "# Borrador\n\n"
                        "## Intro\nDuerme suave, Isabella\nla noche empieza a cantar\n\n"
                        "## Verse 1\nIsabella, respira despacito\nmi cancion te cuida en tender\nlove, care para sonar\notra linea dulce\n\n"
                        "## Chorus\nIsabella mi luz pequena\ncada estrella te acompana\ncada latido es amor\ncoro suave\n\n"
                        "## Verse 2\nIsabella, respira despacito\nmi cancion te cuida en tender\nlove, care para sonar\notra linea dulce\n\n"
                        "## Bridge\nSi la sombra se despierta\nmi voz te vuelve a abrazar\ncon ternura y calma abierta\ntodo vuelve a descansar\n"
                    )
                },
            )

            reviewed = service.review_professional_lyrics(song_id)

            self.assertEqual(reviewed["review"]["status"], "needs_revision")
            self.assertIn("technical_tokens_in_lyrics", [issue["code"] for issue in reviewed["review"]["issues"]])

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
            self.confirm_current_spec(service, song_id)
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

    def test_professional_midi_generation_creates_valid_mid_file(self) -> None:
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
            self.confirm_current_spec(service, song_id)
            service.generate_professional_lyrics(song_id)
            service.review_professional_lyrics(song_id)
            service.generate_professional_music_plan(song_id)

            generated = service.generate_professional_midi(song_id)
            midi = service.get_professional_midi(song_id)
            midi_path = Path(str(midi["midi"]))

            self.assertEqual(generated["progress"]["current"], 6)
            self.assertEqual(generated["project"]["current_phase"], "INSTRUMENTAL_GENERATION")
            self.assertTrue(midi_path.exists())
            self.assertEqual(midi_path.read_bytes()[:4], b"MThd")
            self.assertTrue((Path(temp_dir) / "projects" / song_id / "midi_metadata.json").exists())
            self.assertIn("vocal_melody", midi["metadata"]["tracks"])
            self.assertGreater(len(midi["metadata"]["vocal_melody"]), 0)

    def test_professional_instrumental_generation_creates_wav_from_midi_and_plan(self) -> None:
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
                        "Cancion de cuna para Isabella, 20 segundos, voz femenina suave, piano, "
                        "cuerdas y pad, muy lenta a 70 bpm en C major, estructura intro verse chorus verse bridge outro y salida mp3."
                    )
                },
            )
            self.confirm_current_spec(service, song_id)
            service.generate_professional_lyrics(song_id)
            service.review_professional_lyrics(song_id)
            service.generate_professional_music_plan(song_id)
            service.generate_professional_midi(song_id)

            generated = service.generate_professional_instrumental(song_id)
            instrumental = service.get_professional_instrumental(song_id)
            instrumental_path = Path(str(instrumental["instrumental"]))

            self.assertEqual(generated["progress"]["current"], 7)
            self.assertEqual(generated["project"]["current_phase"], "VOCAL_SYNTHESIS")
            self.assertTrue(instrumental_path.exists())
            with wave.open(str(instrumental_path), "rb") as wav_file:
                self.assertEqual(wav_file.getframerate(), 44100)
                self.assertGreater(wav_file.getnframes(), 0)
            self.assertTrue((Path(temp_dir) / "projects" / song_id / "instrumental_generation.log").exists())

    def test_professional_vocal_synthesis_creates_vocals_wav(self) -> None:
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
                        "Cancion de cuna para Isabella, 20 segundos, voz femenina suave, piano, "
                        "cuerdas y pad, muy lenta a 70 bpm en C major, estructura intro verse chorus verse bridge outro y salida mp3."
                    )
                },
            )
            self.confirm_current_spec(service, song_id)
            service.generate_professional_lyrics(song_id)
            service.review_professional_lyrics(song_id)
            service.generate_professional_music_plan(song_id)
            service.generate_professional_midi(song_id)
            service.generate_professional_instrumental(song_id)

            generated = service.generate_professional_vocals(song_id)
            vocals = service.get_professional_vocals(song_id)
            vocals_path = Path(str(vocals["vocals"]))

            self.assertEqual(generated["progress"]["current"], 8)
            self.assertEqual(generated["project"]["current_phase"], "VOICE_CONVERSION")
            self.assertTrue(vocals_path.exists())
            with wave.open(str(vocals_path), "rb") as wav_file:
                self.assertEqual(wav_file.getframerate(), 44100)
                self.assertGreater(wav_file.getnframes(), 0)
            self.assertTrue((Path(temp_dir) / "projects" / song_id / "vocal_synthesis.log").exists())

    def test_professional_voice_conversion_skips_without_provider_and_advances_to_mixing(self) -> None:
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
                        "Cancion de cuna para Isabella, 20 segundos, voz femenina suave, piano, "
                        "cuerdas y pad, muy lenta a 70 bpm en C major, estructura intro verse chorus verse bridge outro y salida mp3."
                    )
                },
            )
            self.confirm_current_spec(service, song_id)
            service.generate_professional_lyrics(song_id)
            service.review_professional_lyrics(song_id)
            service.generate_professional_music_plan(song_id)
            service.generate_professional_midi(song_id)
            service.generate_professional_instrumental(song_id)
            service.generate_professional_vocals(song_id)

            converted = service.convert_professional_voice(song_id)
            read = service.get_professional_converted_voice(song_id)
            converted_path = Path(str(read["vocals_converted"]))

            self.assertEqual(converted["progress"]["current"], 9)
            self.assertEqual(converted["project"]["current_phase"], "MIXING")
            self.assertEqual(converted["mode"], "skipped_passthrough")
            self.assertTrue(converted_path.exists())
            self.assertEqual(
                converted_path.read_bytes(),
                (Path(temp_dir) / "projects" / song_id / "vocals.wav").read_bytes(),
            )
            self.assertTrue((Path(temp_dir) / "projects" / song_id / "voice_conversion.log").exists())

    def test_professional_mixing_creates_mix_wav(self) -> None:
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
                        "Cancion de cuna para Isabella, 20 segundos, voz femenina suave, piano, "
                        "cuerdas y pad, muy lenta a 70 bpm en C major, estructura intro verse chorus verse bridge outro y salida mp3."
                    )
                },
            )
            self.confirm_current_spec(service, song_id)
            service.generate_professional_lyrics(song_id)
            service.review_professional_lyrics(song_id)
            service.generate_professional_music_plan(song_id)
            service.generate_professional_midi(song_id)
            service.generate_professional_instrumental(song_id)
            service.generate_professional_vocals(song_id)
            service.convert_professional_voice(song_id)

            mixed = service.mix_professional_song(song_id)
            read = service.get_professional_mix(song_id)
            mix_path = Path(str(read["mix"]))

            self.assertEqual(mixed["progress"]["current"], 10)
            self.assertEqual(mixed["project"]["current_phase"], "MASTERING")
            self.assertTrue(mix_path.exists())
            with wave.open(str(mix_path), "rb") as wav_file:
                self.assertEqual(wav_file.getframerate(), 44100)
                self.assertGreater(wav_file.getnframes(), 0)
            self.assertTrue((Path(temp_dir) / "projects" / song_id / "mixing.log").exists())

    @unittest.skipIf(not shutil.which("ffmpeg"), "ffmpeg no esta disponible para exportar MP3")
    # Downstream format contracts use an explicit gate stub; gate behavior has dedicated tests.
    @patch("application.sample_gate.SampleGate.require_for_project", new=lambda self, project, **kwargs: {})
    def test_professional_mastering_creates_final_wav_mp3_and_flac(self) -> None:
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
                        "Cancion de cuna para Isabella, 20 segundos, voz femenina suave, piano, "
                        "cuerdas y pad, muy lenta a 70 bpm en C major, estructura intro verse chorus verse bridge outro y salida mp3."
                    )
                },
            )
            self.confirm_current_spec(service, song_id)
            service.generate_professional_lyrics(song_id)
            service.review_professional_lyrics(song_id)
            service.generate_professional_music_plan(song_id)
            service.generate_professional_midi(song_id)
            service.generate_professional_instrumental(song_id)
            service.generate_professional_vocals(song_id)
            service.convert_professional_voice(song_id)
            service.mix_professional_song(song_id)

            mastered = service.master_professional_song(song_id)
            read = service.get_professional_master(song_id)
            final_wav_path = Path(str(read["final_wav"]))
            final_mp3_path = Path(str(read["final_mp3"]))
            final_flac_path = Path(str(read["final_flac"]))

            self.assertEqual(mastered["progress"]["current"], 11)
            self.assertEqual(mastered["project"]["current_phase"], "EXPORT")
            self.assertTrue(final_wav_path.exists())
            self.assertTrue(final_mp3_path.exists())
            self.assertTrue(final_flac_path.exists())
            self.assertGreater(final_mp3_path.stat().st_size, 0)
            self.assertGreater(final_flac_path.stat().st_size, 0)
            with wave.open(str(final_wav_path), "rb") as wav_file:
                self.assertEqual(wav_file.getframerate(), 44100)
                self.assertGreater(wav_file.getnframes(), 0)
            self.assertTrue((Path(temp_dir) / "projects" / song_id / "mastering.log").exists())

    @unittest.skipIf(not shutil.which("ffmpeg"), "ffmpeg no esta disponible para exportar MP3")
    @patch("application.sample_gate.SampleGate.require_for_project", new=lambda self, project, **kwargs: {})
    def test_professional_export_rejects_procedural_vocal_guide(self) -> None:
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
                        "Cancion de cuna para Isabella, 20 segundos, voz femenina suave, piano, "
                        "cuerdas y pad, muy lenta a 70 bpm en C major, estructura intro verse chorus verse bridge outro y salida mp3."
                    )
                },
            )
            self.confirm_current_spec(service, song_id)
            service.generate_professional_lyrics(song_id)
            service.review_professional_lyrics(song_id)
            service.generate_professional_music_plan(song_id)
            service.generate_professional_midi(song_id)
            service.generate_professional_instrumental(song_id)
            service.generate_professional_vocals(song_id)
            service.convert_professional_voice(song_id)
            service.mix_professional_song(song_id)
            service.master_professional_song(song_id)

            with self.assertRaisesRegex(ValueError, "guia vocal procedural"):
                service.export_professional_song(song_id)

            read = service.get_professional_export(song_id)
            self.assertFalse(read["quality"]["export_ready"])
            self.assertEqual(read["quality"]["vocal_mode"], "procedural_vocal_guide")
            final_mp3 = next(artifact for artifact in read["artifacts"] if artifact["type"] == "final_song_mp3")
            self.assertEqual(final_mp3["download_url"], "")
            self.assertTrue(final_mp3["metadata"]["quality_blocked"])
            with self.assertRaisesRegex(ValueError, "guia vocal procedural"):
                service.professional_artifact_download_file(song_id, "final_song_mp3")

    @unittest.skipIf(not shutil.which("ffmpeg"), "ffmpeg no esta disponible para exportar MP3")
    @patch("application.sample_gate.SampleGate.require_for_project", new=lambda self, project, **kwargs: {})
    def test_professional_export_lists_and_downloads_artifacts(self) -> None:
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temp_dir:
            temp_path = Path(temp_dir)
            vocals_source = temp_path / "source_vocals.wav"
            self.write_tone_wav(vocals_source, 330.0)
            base_settings = Settings.load()
            local_settings = replace(
                base_settings.local_models,
                full_song_command="",
                singing_voice_command=(
                    f'"{sys.executable}" "{PROJECT_ROOT / "tools" / "use_audio_file.py"}" '
                    f'--input "{vocals_source}" --output "{{output_path}}"'
                ),
            )
            settings = replace(
                base_settings,
                data_dir=temp_path,
                local_models=local_settings,
                resource_monitor=replace(base_settings.resource_monitor, enabled=False),
            )
            storage = StorageManager(temp_path)
            service = SongService(storage, settings)
            service.bootstrap()
            created = service.create_professional_project({"title": "Cancion de cuna para Isabella"})
            song_id = str(created["project"]["id"])
            service.collect_professional_spec(
                song_id,
                {
                    "message": (
                        "Cancion de cuna para Isabella, 20 segundos, voz femenina suave, piano, "
                        "cuerdas y pad, muy lenta a 70 bpm en C major, estructura intro verse chorus verse bridge outro y salida mp3."
                    )
                },
            )
            self.confirm_current_spec(service, song_id)
            service.generate_professional_lyrics(song_id)
            service.review_professional_lyrics(song_id)
            service.generate_professional_music_plan(song_id)
            service.generate_professional_midi(song_id)
            service.generate_professional_instrumental(song_id)
            service.generate_professional_vocals(song_id)
            service.convert_professional_voice(song_id)
            service.mix_professional_song(song_id)
            service.master_professional_song(song_id)

            exported = service.export_professional_song(song_id)
            read = service.get_professional_export(song_id)
            download_path, filename, media_type = service.professional_artifact_download_file(song_id, "final_song_mp3")

            self.assertEqual(exported["project"]["status"], "completed")
            self.assertTrue(exported["quality"]["export_ready"])
            self.assertTrue((Path(temp_dir) / "projects" / song_id / "export_manifest.json").exists())
            artifact_types = {str(artifact["type"]) for artifact in read["artifacts"]}
            self.assertIn("final_song_mp3", artifact_types)
            self.assertIn("final_song_flac", artifact_types)
            self.assertIn("project_zip", artifact_types)
            self.assertIn("song_spec", artifact_types)
            self.assertTrue(str(filename).endswith("-final_song_mp3.mp3"))
            self.assertEqual(media_type, "audio/mpeg")
            self.assertEqual(download_path, Path(temp_dir) / "projects" / song_id / "final_song.mp3")
            zip_path, zip_filename, zip_media_type = service.professional_artifact_download_file(song_id, "project_zip")
            self.assertTrue(zip_path.exists())
            self.assertTrue(str(zip_filename).endswith("-project_zip.zip"))
            self.assertEqual(zip_media_type, "application/zip")

    def test_professional_artifact_verification_marks_missing_file(self) -> None:
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temp_dir:
            temp_path = Path(temp_dir)
            storage = StorageManager(temp_path)
            service = SongService(storage, replace(Settings.load(), data_dir=temp_path))
            service.bootstrap()
            created = service.create_professional_project({"title": "Verificacion de artefacto"})
            song_id = str(created["project"]["id"])
            project_dir = temp_path / "projects" / song_id
            wav_path = project_dir / "probe.wav"
            self.write_tone_wav(wav_path, 220.0)
            storage.create_song_artifact(
                artifact_id=f"{song_id}_probe",
                song_id=song_id,
                phase="MASTERING",
                artifact_type="probe_wav",
                file_path=str(wav_path),
                metadata={"provider_name": "test"},
            )

            ok = service.verify_professional_artifact(song_id, "probe_wav")
            wav_path.unlink()
            missing = service.verify_professional_artifact(song_id, "probe_wav")

            self.assertEqual(ok["artifact_status"], "GENERATED")
            self.assertEqual(missing["artifact_status"], "MISSING")
            self.assertIn("no existe", missing["message"])

    @unittest.skipIf(not shutil.which("ffmpeg"), "ffmpeg no esta disponible para exportar MP3")
    @patch("application.sample_gate.SampleGate.require_for_project", new=lambda self, project, **kwargs: {})
    def test_professional_full_song_command_can_create_export_without_stem_vocals(self) -> None:
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temp_dir:
            temp_path = Path(temp_dir)
            full_song_source = temp_path / "source_full_song.wav"
            self.write_tone_wav(full_song_source, 440.0)
            base_settings = Settings.load()
            local_settings = replace(
                base_settings.local_models,
                full_song_command=(
                    f'"{sys.executable}" "{PROJECT_ROOT / "tools" / "use_audio_file.py"}" '
                    f'--input "{full_song_source}" --output "{{output_path}}"'
                ),
                singing_voice_command="",
            )
            settings = replace(
                base_settings,
                data_dir=temp_path,
                local_models=local_settings,
                resource_monitor=replace(base_settings.resource_monitor, enabled=False),
            )
            storage = StorageManager(temp_path)
            service = SongService(storage, settings)
            service.bootstrap()
            created = service.create_professional_project({"title": "Cancion full song"})
            song_id = str(created["project"]["id"])
            service.collect_professional_spec(
                song_id,
                {
                    "message": (
                        "Cancion de cuna para Isabella, 20 segundos, voz femenina suave, piano, "
                        "cuerdas y pad, muy lenta a 70 bpm en C major, estructura intro verse chorus verse bridge outro y salida mp3."
                    )
                },
            )
            self.confirm_current_spec(service, song_id)
            service.generate_professional_lyrics(song_id)
            service.review_professional_lyrics(song_id)
            service.generate_professional_music_plan(song_id)
            service.generate_professional_midi(song_id)

            mastered = service.master_professional_song(song_id)
            exported = service.export_professional_song(song_id)
            read = service.get_professional_export(song_id)
            final_wav = next(artifact for artifact in read["artifacts"] if artifact["type"] == "final_song_wav")

            self.assertEqual(mastered["generation_mode"], "local_full_song_command")
            self.assertTrue(exported["quality"]["export_ready"])
            self.assertEqual(exported["quality"]["vocal_mode"], "full_song_provider")
            self.assertEqual(final_wav["metadata"]["generation_mode"], "local_full_song_command")
            self.assertTrue(Path(str(mastered["final_mp3"])).exists())

    def test_professional_full_song_command_formats_ace_step_profile_tokens(self) -> None:
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temp_dir:
            temp_path = Path(temp_dir)
            storage = StorageManager(temp_path)
            service = ProfessionalFullSongService(
                storage,
                command_template=(
                    "python tools/acestep_generate.py --checkpoint-path data/models/music/acestep-1.5-{model_type} "
                    "--infer-step {infer_steps} --torch-threads {threads} --device {device} --duration {duration_seconds} "
                    "--prompt {prompt_path} --lyrics {lyrics_path} --output {output_path}"
                ),
            )
            project = {
                "id": "song-test",
                "title": "Perfil ACE",
                "spec": {"json_spec": {"duration_seconds": 30}},
            }

            command = service._format_command(
                project,
                temp_path,
                temp_path / "prompt.txt",
                temp_path / "lyrics.md",
                temp_path / "out.wav",
                temp_path / "run.log",
                temp_path / "diag.json",
                TURBO_PROFILE,
            )

            self.assertIn("acestep-1.5-2b-turbo", command)
            self.assertIn("--infer-step 8", command)
            self.assertIn("--torch-threads 4", command)
            self.assertIn("--device xpu", command)
            base_command = service._format_command(
                project,
                temp_path,
                temp_path / "prompt.txt",
                temp_path / "lyrics.md",
                temp_path / "out.wav",
                temp_path / "run.log",
                temp_path / "diag.json",
                BASE_PROFILE,
            )
            self.assertIn("acestep-1.5-2b-turbo", base_command)
            self.assertIn("--config-path acestep-v15-base", base_command)
            self.assertIn("--infer-step 32", base_command)
            self.assertIn("--torch-threads 14", base_command)
            self.assertIn("--device cpu", base_command)
            self.assertEqual(service._command_env(TURBO_PROFILE)["ACESTEP_MODEL_REPO"], "ACE-Step/Ace-Step1.5")
            self.assertEqual(service._command_env(BASE_PROFILE)["ACESTEP_MODEL_REPO"], "ACE-Step/acestep-v15-base")

    def test_professional_full_song_command_reports_missing_format_token(self) -> None:
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temp_dir:
            temp_path = Path(temp_dir)
            service = ProfessionalFullSongService(
                StorageManager(temp_path),
                command_template="python provider.py --unknown {missing_token}",
            )

            with self.assertRaisesRegex(ValueError, "missing_token"):
                service._format_command(
                    {"id": "song-test", "spec": {"json_spec": {"duration_seconds": 30}}},
                    temp_path,
                    temp_path / "prompt.txt",
                    temp_path / "lyrics.md",
                    temp_path / "out.wav",
                    temp_path / "run.log",
                    temp_path / "diag.json",
                    BASE_PROFILE,
                )

    def test_resource_monitor_default_audio_ram_threshold_is_local_friendly(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(ResourceMonitorSettings.load().min_free_ram_mb_for_audio, 3500)

    def test_provider_bootstrap_creates_local_directories_without_downloads(self) -> None:
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temp_dir:
            temp_path = Path(temp_dir)
            with patch.object(provider_bootstrap, "MODEL_ROOT", temp_path / "models"), patch.object(
                provider_bootstrap,
                "PROVIDER_ROOT",
                temp_path / "providers",
            ), patch.object(provider_bootstrap, "BOOTSTRAP_STATE_ROOT", temp_path / ".bootstrap"), patch.dict(
                os.environ,
                {"SONG_AI_BOOTSTRAP_ON_START": "false"},
                clear=False,
            ):
                summary = provider_bootstrap.run_bootstrap()

            self.assertFalse(summary["enabled"])
            self.assertTrue((temp_path / "models" / "llm").exists())
            self.assertTrue((temp_path / "models" / "huggingface").exists())
            self.assertTrue((temp_path / "providers").exists())
            self.assertTrue((temp_path / ".bootstrap").exists())

    def test_provider_bootstrap_downloads_gguf_models_to_configured_paths(self) -> None:
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temp_dir:
            temp_path = Path(temp_dir)
            source = temp_path / "source.gguf"
            source.write_text("fake gguf", encoding="utf-8")
            gemma_path = temp_path / "models" / "llm" / "gemma" / "gemma.gguf"
            qwen_path = temp_path / "models" / "llm" / "qwen" / "qwen.gguf"
            with patch.object(provider_bootstrap, "MODEL_ROOT", temp_path / "models"), patch.dict(
                os.environ,
                {
                    "SONG_AI_GEMMA_GGUF_URL": source.as_uri(),
                    "SONG_AI_QWEN_GGUF_URL": source.as_uri(),
                    "SONG_AI_GEMMA_GGUF_PATH": str(gemma_path),
                    "SONG_AI_QWEN_GGUF_PATH": str(qwen_path),
                },
                clear=False,
            ):
                summary = {"downloads": []}
                provider_bootstrap.download_url_models(summary)

            self.assertTrue(gemma_path.exists())
            self.assertTrue(qwen_path.exists())
            self.assertEqual(len(summary["downloads"]), 2)

    def test_provider_bootstrap_markers_skip_existing_installs(self) -> None:
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temp_dir:
            temp_path = Path(temp_dir)
            marker = temp_path / ".bootstrap" / ".ace-step.installed"
            package = "git+https://github.com/ace-step/ACE-Step.git"
            marker.parent.mkdir(parents=True, exist_ok=True)
            marker.write_text(f"{package}\npython={sys.version.split()[0]}\n", encoding="utf-8")
            with patch.object(provider_bootstrap, "ACE_STEP_MARKER", marker), patch.dict(
                os.environ,
                {
                    "SONG_AI_BOOTSTRAP_UPGRADE": "false",
                    "SONG_AI_ACE_STEP_PACKAGE": package,
                },
                clear=False,
            ), patch.object(provider_bootstrap, "ace_step_ready", return_value=True), patch("subprocess.run") as run:
                installed = provider_bootstrap.install_ace_step(upgrade=False)

            self.assertFalse(installed)
            run.assert_not_called()

    def test_provider_bootstrap_marker_reinstalls_when_modules_are_missing(self) -> None:
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temp_dir:
            temp_path = Path(temp_dir)
            marker = temp_path / ".bootstrap" / ".ace-step.installed"
            package = "git+https://github.com/ace-step/ACE-Step.git"
            marker.parent.mkdir(parents=True, exist_ok=True)
            marker.write_text(f"{package}\npython={sys.version.split()[0]}\n", encoding="utf-8")
            with patch.object(provider_bootstrap, "ACE_STEP_MARKER", marker), patch.dict(
                os.environ,
                {
                    "SONG_AI_BOOTSTRAP_UPGRADE": "false",
                    "SONG_AI_ACE_STEP_PACKAGE": package,
                },
                clear=False,
            ), patch.object(provider_bootstrap, "modules_available", return_value=False), patch.object(
                provider_bootstrap,
                "ace_step_ready",
                return_value=False,
            ), patch("subprocess.run") as run:
                installed = provider_bootstrap.install_ace_step(upgrade=False)

            self.assertTrue(installed)
            run.assert_called_once()
            self.assertNotIn("--target", run.call_args.args[0])

    def test_provider_bootstrap_existing_modules_create_marker_without_reinstall(self) -> None:
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temp_dir:
            temp_path = Path(temp_dir)
            marker = temp_path / ".bootstrap" / ".ace-step.installed"
            package = "git+https://github.com/ace-step/ACE-Step.git"
            with patch.object(provider_bootstrap, "ACE_STEP_MARKER", marker), patch.dict(
                os.environ,
                {
                    "SONG_AI_BOOTSTRAP_UPGRADE": "false",
                    "SONG_AI_ACE_STEP_PACKAGE": package,
                },
                clear=False,
            ), patch.object(provider_bootstrap, "ace_step_ready", return_value=True), patch("subprocess.run") as run:
                installed = provider_bootstrap.install_ace_step(upgrade=False)

            self.assertFalse(installed)
            self.assertTrue(marker.exists())
            self.assertIn(package, marker.read_text(encoding="utf-8"))
            run.assert_not_called()

    def test_provider_bootstrap_repairs_local_audio_deps_when_compatibility_probe_fails(self) -> None:
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temp_dir:
            temp_path = Path(temp_dir)
            marker = temp_path / ".bootstrap" / ".local-audio-deps.installed"
            marker.parent.mkdir(parents=True, exist_ok=True)
            requirements = temp_path / "requirements-local-audio.txt"
            requirements.write_text("huggingface_hub>=0.34.0,<1.0\n", encoding="utf-8")
            marker.write_text(f"{requirements.read_text(encoding='utf-8')}\npython={sys.version.split()[0]}\n", encoding="utf-8")
            with patch.object(provider_bootstrap, "LOCAL_AUDIO_MARKER", marker), patch("pathlib.Path.exists", return_value=True), patch(
                "pathlib.Path.read_text",
                return_value=requirements.read_text(encoding="utf-8"),
            ), patch.object(provider_bootstrap, "modules_available", return_value=True), patch.object(
                provider_bootstrap,
                "local_audio_deps_ready",
                return_value=False,
            ), patch("subprocess.run") as run:
                installed = provider_bootstrap.install_local_audio_deps(upgrade=False)

            self.assertTrue(installed)
            self.assertIn("--upgrade", run.call_args.args[0])
            self.assertIn("huggingface_hub>=0.34.0,<1.0", run.call_args.args[0])
            self.assertNotIn("-r", run.call_args.args[0])
            self.assertNotIn("--target", run.call_args.args[0])

    def test_provider_bootstrap_upgrade_ignores_existing_markers(self) -> None:
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temp_dir:
            temp_path = Path(temp_dir)
            marker = temp_path / ".bootstrap" / ".ace-step.installed"
            package = "git+https://github.com/ace-step/ACE-Step.git"
            marker.parent.mkdir(parents=True, exist_ok=True)
            marker.write_text(package, encoding="utf-8")
            with patch.object(provider_bootstrap, "ACE_STEP_MARKER", marker), patch.dict(
                os.environ,
                {"SONG_AI_ACE_STEP_PACKAGE": package},
                clear=False,
            ), patch("subprocess.run") as run:
                installed = provider_bootstrap.install_ace_step(upgrade=True)

            self.assertTrue(installed)
            self.assertIn("--upgrade", run.call_args.args[0])
            self.assertNotIn("--target", run.call_args.args[0])

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

    def test_acestep_diagnostics_preserve_spanish_lyrics_and_sections(self) -> None:
        args = SimpleNamespace(
            prompt="prompt.txt",
            lyrics="lyrics.md",
            duration=8,
            infer_step=4,
            guidance_scale=15.0,
            scheduler_type="euler",
            cfg_type="apg",
            omega_scale=10.0,
            seed=42,
            output_type="full_song_with_vocals",
            oss_steps="16,96",
        )
        lyrics = "[es]\n[verse]\nDuerme mi cielo\ncierra los ojos\n\n[chorus]\nAquí estoy contigo\nguardando tu sueño\n"
        diagnostics = acestep_generate.build_diagnostics(
            args,
            "tender Spanish lullaby, soft female vocal, acoustic guitar",
            lyrics,
            Path("out.wav"),
            Path("models/ace-step"),
        )

        self.assertEqual(diagnostics["input"]["lyrics"], lyrics)
        self.assertEqual(diagnostics["input"]["detected_language"], "Spanish")
        self.assertTrue(diagnostics["input"]["has_spanish_language_tag"])
        self.assertTrue(diagnostics["input"]["contains_accents"])
        self.assertIn("verse", [section["label"] for section in diagnostics["input"]["sections"]])
        self.assertIn("chorus", [section["label"] for section in diagnostics["input"]["sections"]])
        self.assertFalse(diagnostics["parameters"]["instrumental_mode"])
        self.assertTrue(diagnostics["parameters"]["sung_vocal_requested"])

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

    def test_local_full_song_command_receives_all_documented_tokens(self) -> None:
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temp_dir:
            root = Path(temp_dir)
            local_settings = replace(
                Settings.load().local_models,
                full_song_command=(
                    "{python_executable} {prompt_path} {lyrics_path} {output_path} "
                    "{diagnostics_path} {duration_seconds} {model_type} {infer_steps} {device} {threads}"
                ),
            )
            pipeline = LocalSongPipeline(local_settings)
            context = MockSongRenderContext(
                project_name="Tokens",
                description="Prueba",
                instrumental_intent={"bpm": 90, "key": "C major"},
                melody_intent={},
                lyrics_intent={},
                lyrics_markdown="# Verso\nLinea uno\nLinea dos\n",
            )

            def create_output(_template, values, _profile=None):
                Path(str(values["output_path"])).write_bytes(b"wav")

            with (
                patch.object(pipeline, "_full_song_command_available", return_value=True),
                patch("audio.local_song_pipeline.shutil.which", return_value="ffmpeg"),
                patch.object(pipeline, "_run_template", side_effect=create_output) as run_template,
                patch.object(pipeline, "_export_mp3", side_effect=lambda _wav, mp3: Path(mp3).write_bytes(b"mp3")),
            ):
                pipeline.generate(context, root / "song")

            values = run_template.call_args.args[1]
            self.assertEqual(
                {"python_executable", "diagnostics_path", "duration_seconds"} - set(values),
                set(),
            )
            self.assertGreaterEqual(int(values["duration_seconds"]), 18)

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

    def test_project_phase_data_is_persisted_without_generation(self) -> None:
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temp_dir:
            storage = StorageManager(Path(temp_dir))
            settings = Settings.load()
            settings = replace(
                settings,
                local_models=replace(
                    settings.local_models,
                    full_song_command="",
                    soundtrack_command="",
                    singing_voice_command="",
                ),
            )
            service = SongService(storage, settings)
            service.bootstrap()
            service.create_instrumental({"genre": "lullaby", "mood": "warm"})
            service.create_melody({"vocal_style": "soft", "structure": "verse, chorus"})
            service.create_lyrics({"theme": "sleep", "structure": "verse, chorus"})
            created = service.create_set({"project_name": "Proyecto fase", "description": "Descripcion inicial"})
            set_id = str(created["id"])

            saved = service.save_project_phase_data(
                set_id,
                "intent",
                {"data": {"intent": {"recipient": "Isabella", "bpm": 72}}},
            )
            loaded = service.get_project(set_id)

            self.assertEqual(saved["saved"]["status"], "intent_saved")
            self.assertEqual(saved["saved"]["phase_status"], "COMPLETED")
            self.assertEqual(saved["saved"]["change_source"], "USER")
            self.assertEqual(loaded["phase_data"]["intent"]["data"]["intent"]["recipient"], "Isabella")
            self.assertEqual(loaded["phases"]["intent"]["phase_status"], "COMPLETED")
            self.assertEqual(loaded["phases"]["intent"]["change_source"], "USER")
            phase_events = storage.list_project_phase_events(set_id)
            self.assertTrue(any(event["event_type"] == "PHASE_SAVED" for event in phase_events))

    def test_project_phase_ai_suggestion_stays_draft_until_saved(self) -> None:
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temp_dir:
            storage = StorageManager(Path(temp_dir))
            service = SongService(storage, Settings.load())
            service.bootstrap()
            service.create_instrumental({"genre": "lullaby", "mood": "warm"})
            service.create_melody({"vocal_style": "soft", "structure": "verse, chorus"})
            service.create_lyrics({"theme": "sleep", "structure": "verse, chorus"})
            created = service.create_set({"project_name": "Proyecto IA", "description": "Sugerencia"})
            set_id = str(created["id"])

            suggested = service.ai_suggest_project_phase(
                set_id,
                "music-plan",
                {"data": {"musicPlan": {"bpm": 72}}},
            )
            saved = service.save_project_phase_data(
                set_id,
                "music-plan",
                {"data": {"musicPlan": {"bpm": 72}}, "change_source": "MIXED"},
            )

            self.assertEqual(suggested["saved"]["phase_status"], "DRAFT")
            self.assertEqual(suggested["saved"]["change_source"], "AI")
            self.assertEqual(saved["saved"]["phase_status"], "COMPLETED")
            self.assertEqual(saved["saved"]["change_source"], "MIXED")
            events = storage.list_project_phase_events(set_id)
            self.assertTrue(any(event["event_type"] == "AI_SUGGESTED" for event in events))

    def test_project_ui_state_persists_last_active_phase(self) -> None:
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temp_dir:
            storage = StorageManager(Path(temp_dir))
            settings = Settings.load()
            settings = replace(
                settings,
                local_models=replace(
                    settings.local_models,
                    full_song_command="",
                    soundtrack_command="",
                    singing_voice_command="",
                ),
            )
            service = SongService(storage, settings)
            service.bootstrap()
            service.create_instrumental({"genre": "lullaby", "mood": "warm"})
            service.create_melody({"vocal_style": "soft", "structure": "intro, verse, chorus"})
            service.create_lyrics({"theme": "sleep", "structure": "intro, verse, chorus"})
            created = service.create_set({"project_name": "Proyecto rehidratable", "description": "Estado completo"})
            set_id = str(created["id"])

            saved = service.save_project_active_phase(set_id, {"phase": "music-plan"})
            loaded = service.get_project(set_id)

            self.assertEqual(saved["ui_state"]["last_active_phase"], "music-plan")
            self.assertEqual(loaded["ui_state"]["last_active_phase"], "music-plan")

    def test_gemma_assistant_sees_saved_editor_phases_before_production(self) -> None:
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temp_dir:
            storage = StorageManager(Path(temp_dir))
            service = SongService(storage, Settings.load())
            service.bootstrap()
            service.create_instrumental({"genre": "lullaby", "mood": "warm"})
            service.create_melody({"vocal_style": "soft", "structure": "intro, verse, chorus"})
            service.create_lyrics({"theme": "sleep", "structure": "intro, verse, chorus"})
            created = service.create_set({"project_name": "Cancion faseada", "description": "Cancion lista para Production"})
            set_id = str(created["id"])

            for phase in ("intent", "lyrics", "music-plan", "midi", "instrumental", "voice"):
                service.save_project_phase_data(set_id, phase, {"data": {phase: {"saved": True}}})

            answer = service.gemma_assistant(
                {
                    "set_id": set_id,
                    "question": "Que sigue para terminar esta cancion?",
                    "active_phase": "voice",
                }
            )

            self.assertTrue(answer["readiness"]["editor_ready_for_production"])
            self.assertIn("Intent", answer["message"])
            self.assertIn("Voice", answer["message"])
            self.assertIn("revision tecnica", answer["message"])
            self.assertIn("lyrics.content", answer["message"])
            self.assertIn("technical_validation", answer)
            self.assertNotIn("Crea o carga un proyecto desde Biblioteca", answer["message"])

    def test_gemma_assistant_distinguishes_editor_set_from_professional_project(self) -> None:
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temp_dir:
            storage = StorageManager(Path(temp_dir))
            service = SongService(storage, Settings.load())
            service.bootstrap()
            service.create_instrumental({"genre": "lullaby", "mood": "warm"})
            service.create_melody({"vocal_style": "soft", "structure": "intro, verse, chorus"})
            service.create_lyrics({"theme": "sleep", "structure": "intro, verse, chorus"})
            created = service.create_set({"project_name": "Cancion faseada", "description": "Cancion lista para Production"})
            set_id = str(created["id"])

            answer = service.gemma_assistant(
                {
                    "set_id": set_id,
                    "question": "no estoy en un proyecto activo?",
                    "active_phase": "voice",
                    "editor_phase_statuses": {
                        "intent": "READY",
                        "lyrics": "READY",
                        "music-plan": "READY",
                        "midi": "READY",
                        "instrumental": "READY",
                        "voice": "READY",
                    },
                }
            )

            self.assertFalse(answer["readiness"]["editor_ready_for_production"])
            self.assertEqual(answer["mode"], "sqlite_guidance")
            self.assertIn("Si: estas en el proyecto activo", answer["message"])
            self.assertIn("revision tecnica", answer["message"])
            self.assertIn("guardar fase:intent", answer["message"])
            self.assertEqual(answer["technical_validation"]["source_of_truth"], "sqlite")

    def test_production_project_created_from_active_set_is_prepared_for_export_tasks(self) -> None:
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temp_dir:
            storage = StorageManager(Path(temp_dir))
            service = SongService(storage, Settings.load())
            service.bootstrap()
            service.create_instrumental({"genre": "lullaby", "mood": "warm", "instruments": ["acoustic guitar"]})
            service.create_melody({"vocal_style": "soft female vocal", "structure": "verse, chorus"})
            service.create_lyrics({"theme": "sleep", "structure": "verse, chorus"})
            created_set = service.create_set({"project_name": "Cancion de cuna", "description": "Cancion completa suave y cantada."})
            set_id = str(created_set["id"])

            service.save_project_phase_data(
                set_id,
                "intent",
                {
                    "data": {
                        "intent": {
                            "recipient": "Isabella",
                            "language": "Spanish",
                            "mood": "tender",
                            "bpm": 72,
                        }
                    }
                },
            )
            service.save_project_phase_data(
                set_id,
                "lyrics",
                {
                    "data": {
                        "lyricSections": [
                            {"type": "Verse 1", "text": "Duerme mi cielo\ncierra los ojos"},
                            {"type": "Chorus", "text": "Aqui estoy contigo\nguardando tu sueno"},
                            {"type": "Bridge", "text": "La noche respira\ncon dulce calma"},
                            {"type": "Outro", "text": "Descansa mi vida\nmanana habra sol"},
                        ]
                    }
                },
            )
            service.save_project_phase_data(
                set_id,
                "music-plan",
                {
                    "data": {
                        "musicPlan": {
                            "bpm": 72,
                            "key": "C major",
                            "sections": [
                                {"name": "Verse 1", "duration": 24},
                                {"name": "Chorus", "duration": 28},
                                {"name": "Bridge", "duration": 22},
                                {"name": "Outro", "duration": 18},
                            ],
                        }
                    }
                },
            )
            for phase in ("midi", "instrumental", "voice"):
                service.save_project_phase_data(set_id, phase, {"data": {phase: {"saved": True}}})

            created_pro = service.create_professional_project(
                {
                    "title": "Cancion de cuna",
                    "user_id": f"set:{set_id}",
                    "source_set_id": set_id,
                }
            )
            song_id = str(created_pro["project"]["id"])
            project_dir = Path(temp_dir) / "projects" / song_id

            self.assertEqual(created_pro["project"]["current_phase"], "MIDI_GENERATION")
            self.assertTrue(created_pro["project"]["spec"]["approved_by_qwen"])
            self.assertTrue((project_dir / "song_spec.json").exists())
            self.assertTrue((project_dir / "lyrics.md").exists())
            self.assertTrue((project_dir / "lyrics_approved.json").exists())
            self.assertTrue((project_dir / "music_plan.json").exists())
            self.assertIn("Duerme mi cielo", (project_dir / "lyrics.md").read_text(encoding="utf-8"))

            generated_plan = service.get_professional_music_plan(song_id)

            self.assertEqual(generated_plan["music_plan"]["bpm"], 72)

    def test_existing_linked_production_project_is_repaired_from_active_set(self) -> None:
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temp_dir:
            storage = StorageManager(Path(temp_dir))
            service = SongService(storage, Settings.load())
            service.bootstrap()
            service.create_instrumental({"genre": "lullaby", "mood": "warm"})
            service.create_melody({"vocal_style": "soft female vocal", "structure": "verse, chorus"})
            service.create_lyrics({"theme": "sleep", "structure": "verse, chorus"})
            created_set = service.create_set({"project_name": "Cancion de cuna", "description": "Cancion lista."})
            set_id = str(created_set["id"])
            service.save_project_phase_data(set_id, "intent", {"data": {"intent": {"language": "Spanish", "bpm": 72}}})
            service.save_project_phase_data(
                set_id,
                "lyrics",
                {
                    "data": {
                        "lyricSections": [
                            {"type": "Verse", "text": "Duerme mi cielo"},
                            {"type": "Chorus", "text": "Aqui estoy contigo"},
                        ]
                    }
                },
            )
            legacy = service.create_professional_project({"title": "Cancion de cuna", "user_id": f"set:{set_id}"})
            song_id = str(legacy["project"]["id"])

            self.assertIsNone(legacy["project"].get("spec"))

            listed = service.list_professional_projects()
            repaired = next(project for project in listed["projects"] if project["id"] == song_id)
            generated_plan = service.generate_professional_music_plan(song_id)

            self.assertTrue(repaired["spec"]["approved_by_qwen"])
            self.assertEqual(generated_plan["music_plan"]["bpm"], 72)

    def test_audio_export_contains_song_mock_context_and_local_pipeline_status(self) -> None:
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temp_dir:
            storage = StorageManager(Path(temp_dir))
            settings = Settings.load()
            settings = replace(
                settings,
                local_models=replace(
                    settings.local_models,
                    full_song_command="",
                    soundtrack_command="",
                    singing_voice_command="",
                ),
            )
            service = SongService(storage, settings)
            service.bootstrap()

            pipeline = service.local_pipeline_status()
            system = service.system_status({"status": "idle", "message": "test"})
            phases = service.project_phase_status()
            self.assertFalse(pipeline["ready"])
            self.assertIn("full_song", pipeline["missing"])
            self.assertEqual("mix_and_export" in pipeline["missing"], shutil.which("ffmpeg") is None)
            self.assertTrue(system["components"])
            self.assertTrue(phases["phases"])

            result = service.create_default_lullaby_mp3(approved_mock_fixture=True)
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
                full_song_command="",
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
            service.local_song_pipeline.resource_monitor = None
            service.create_default_lullaby_mp3(approved_mock_fixture=True)

            result = service.generate_local_final_song()

            self.assertEqual(result["mode"], "local_final_song")
            self.assertTrue(Path(str(result["mp3"])).exists())
            self.assertTrue(Path(str(result["wav"])).exists())
            download_path, filename = service.latest_audio_export_file("mp3")
            self.assertEqual(download_path, Path(str(result["mp3"])))
            self.assertTrue(filename.endswith(".mp3"))


if __name__ == "__main__":
    unittest.main()
