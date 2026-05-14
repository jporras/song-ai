from __future__ import annotations

from dataclasses import dataclass
import importlib.util
from pathlib import Path
import shutil
import subprocess

from audio.mock_song_renderer import MockSongRenderContext
from config.model_settings import LocalModelSettings


@dataclass(frozen=True)
class LocalPipelineStatus:
    ready: bool
    missing: list[str]
    requirements: list[dict[str, object]]


class LocalSongPipeline:
    def __init__(self, settings: LocalModelSettings) -> None:
        self.settings = settings

    def status(self) -> LocalPipelineStatus:
        full_song_configured = bool(self.settings.full_song_command.strip())
        full_song_available = self._full_song_command_available()
        requirements = [
            {
                "role": "full_song",
                "engine": "ACE-Step or compatible local command",
                "configured": full_song_configured and full_song_available,
                "detail": self._full_song_detail(full_song_configured, full_song_available),
                "path": "preferred",
            },
            {
                "role": "soundtrack",
                "engine": self.settings.soundtrack_model,
                "configured": bool(self.settings.soundtrack_command.strip()),
                "detail": "Configura SONG_AI_SOUNDTRACK_COMMAND para generar instrumental.wav localmente.",
                "path": "stems",
            },
            {
                "role": "singing_voice",
                "engine": self.settings.singing_voice_engine,
                "configured": bool(self.settings.singing_voice_command.strip()),
                "detail": "Configura SONG_AI_SINGING_VOICE_COMMAND para generar vocals.wav localmente.",
                "path": "stems",
            },
            {
                "role": "mix_and_export",
                "engine": self.settings.mixer_engine,
                "configured": shutil.which("ffmpeg") is not None,
                "detail": "ffmpeg debe estar disponible para mezclar y exportar MP3.",
            },
        ]
        ffmpeg_ready = bool(requirements[-1]["configured"])
        full_song_ready = bool(requirements[0]["configured"]) and ffmpeg_ready
        stems_ready = bool(requirements[1]["configured"]) and bool(requirements[2]["configured"]) and ffmpeg_ready
        missing = self._missing(requirements, full_song_ready, stems_ready)
        return LocalPipelineStatus(ready=full_song_ready or stems_ready, missing=missing, requirements=requirements)

    def generate(self, context: MockSongRenderContext, song_dir: Path) -> dict[str, object]:
        status = self.status()
        if not status.ready:
            raise ValueError(
                "No se puede generar una cancion final local todavia. Falta: "
                + ", ".join(status.missing)
                + ". Revisa /api/local-pipeline/status."
            )

        work_dir = song_dir / "local_pipeline"
        exports_dir = song_dir / "exports"
        stems_dir = song_dir / "stems"
        work_dir.mkdir(parents=True, exist_ok=True)
        exports_dir.mkdir(parents=True, exist_ok=True)
        stems_dir.mkdir(parents=True, exist_ok=True)

        prompt_path = work_dir / "music_prompt.txt"
        lyrics_path = exports_dir / "lyrics.md"
        instrumental_path = stems_dir / "instrumental.wav"
        vocals_path = stems_dir / "vocals.wav"
        final_wav_path = exports_dir / "final_mix.wav"
        final_mp3_path = exports_dir / "final_mix.mp3"

        prompt_path.write_text(self._build_music_prompt(context), encoding="utf-8")
        lyrics_path.write_text(context.lyrics_markdown.rstrip() + "\n", encoding="utf-8")

        if self.settings.full_song_command.strip() and self._full_song_command_available():
            self._run_template(
                self.settings.full_song_command,
                {
                    "prompt_path": prompt_path,
                    "lyrics_path": lyrics_path,
                    "output_path": final_wav_path,
                    "work_dir": work_dir,
                },
            )
            self._assert_file(final_wav_path, "El comando local de cancion completa no genero final_mix.wav.")
            self._export_mp3(final_wav_path, final_mp3_path)
            return {
                "mode": "local_final_song",
                "wav": str(final_wav_path),
                "mp3": str(final_mp3_path),
                "stems": {},
                "prompt": str(prompt_path),
                "note": "Cancion final generada con un comando local completo; no usa modo pro.",
            }

        self._run_template(
            self.settings.soundtrack_command,
            {
                "prompt_path": prompt_path,
                "lyrics_path": lyrics_path,
                "output_path": instrumental_path,
                "work_dir": work_dir,
            },
        )
        self._assert_file(instrumental_path, "El comando local de soundtrack no genero instrumental.wav.")

        self._run_template(
            self.settings.singing_voice_command,
            {
                "prompt_path": prompt_path,
                "lyrics_path": lyrics_path,
                "instrumental_path": instrumental_path,
                "output_path": vocals_path,
                "work_dir": work_dir,
            },
        )
        self._assert_file(vocals_path, "El comando local de voz cantada no genero vocals.wav.")

        ffmpeg_path = shutil.which("ffmpeg")
        if ffmpeg_path is None:
            raise ValueError("ffmpeg no esta disponible para mezclar/exportar.")
        if final_mp3_path.exists():
            final_mp3_path.unlink()

        subprocess.run(
            [
                ffmpeg_path,
                "-y",
                "-hide_banner",
                "-loglevel",
                "error",
                "-i",
                str(instrumental_path),
                "-i",
                str(vocals_path),
                "-filter_complex",
                "amix=inputs=2:duration=longest:normalize=1",
                str(final_wav_path),
            ],
            check=True,
        )
        self._export_mp3(final_wav_path, final_mp3_path)

        return {
            "mode": "local_final_song",
            "wav": str(final_wav_path),
            "mp3": str(final_mp3_path),
            "stems": {
                "instrumental": str(instrumental_path),
                "vocals": str(vocals_path),
            },
            "prompt": str(prompt_path),
            "note": "Cancion final generada con herramientas locales configuradas; no usa modo pro.",
        }

    def _run_template(self, template: str, values: dict[str, Path]) -> None:
        command = template.format(**{key: str(value) for key, value in values.items()})
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            detail = (result.stderr or result.stdout or command).strip()
            raise ValueError(f"El comando local fallo: {detail}")

    def _full_song_command_available(self) -> bool:
        command = self.settings.full_song_command.strip()
        if not command:
            return False
        if "acestep_generate.py" in command:
            return importlib.util.find_spec("acestep.pipeline_ace_step") is not None
        return True

    def _full_song_detail(self, configured: bool, available: bool) -> str:
        if not configured:
            return "Configura SONG_AI_FULL_SONG_COMMAND para generar final_mix.wav completo localmente."
        if not available:
            return "ACE-Step esta configurado pero no instalado/importable. Ejecuta Preparar/reiniciar bootstrap o activa SONG_AI_INSTALL_ACE_STEP=true."
        return "Comando local completo disponible para generar final_mix.wav."

    def _assert_file(self, path: Path, message: str) -> None:
        if not path.exists() or path.stat().st_size == 0:
            raise ValueError(message)

    def _export_mp3(self, final_wav_path: Path, final_mp3_path: Path) -> None:
        ffmpeg_path = shutil.which("ffmpeg")
        if ffmpeg_path is None:
            raise ValueError("ffmpeg no esta disponible para exportar MP3.")
        subprocess.run(
            [
                ffmpeg_path,
                "-y",
                "-hide_banner",
                "-loglevel",
                "error",
                "-i",
                str(final_wav_path),
                str(final_mp3_path),
            ],
            check=True,
        )

    def _missing(
        self,
        requirements: list[dict[str, object]],
        full_song_ready: bool,
        stems_ready: bool,
    ) -> list[str]:
        if full_song_ready or stems_ready:
            return []
        missing: list[str] = []
        if not requirements[-1]["configured"]:
            missing.append("mix_and_export")
        if not requirements[0]["configured"]:
            missing.append("full_song")
        if not requirements[1]["configured"] or not requirements[2]["configured"]:
            missing.append("soundtrack/singing_voice")
        return missing

    def _build_music_prompt(self, context: MockSongRenderContext) -> str:
        return "\n".join(
            [
                f"Project: {context.project_name}",
                f"Description: {context.description}",
                f"Instrumental intent: {context.instrumental_intent}",
                f"Vocal intent: {context.melody_intent}",
                f"Lyrical intent: {context.lyrics_intent}",
                "Goal: complete song with coherent soundtrack, sung voice, lyrics, melody and final mix.",
            ]
        )
