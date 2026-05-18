from __future__ import annotations

from array import array
import math
from pathlib import Path
import re
import subprocess
import wave

from core.storage import StorageManager
from models.song_workflow import SongPhase, SongPhaseStatus


class VocalSynthesisService:
    SAMPLE_RATE = 44100
    VOWELS = ("a", "e", "i", "o", "u")

    def __init__(self, storage: StorageManager, command_template: str = "", timeout_seconds: int = 3600) -> None:
        self.storage = storage
        self.command_template = command_template.strip()
        self.timeout_seconds = timeout_seconds

    def generate(
        self,
        song_id: str,
        lyrics_approved: dict[str, object],
        midi_metadata: dict[str, object],
        voice_style: str,
    ) -> dict[str, object]:
        project_dir = self.storage.data_dir / "projects" / song_id
        vocals_path = project_dir / "vocals.wav"
        prompt_path = project_dir / "vocal_prompt.txt"
        log_path = project_dir / "vocal_synthesis.log"
        prompt_path.write_text(self._prompt(lyrics_approved, voice_style), encoding="utf-8")

        if self.command_template:
            mode = "local_command"
            quality_status = "final_candidate"
            self._run_command(project_dir, prompt_path, vocals_path, log_path)
        else:
            mode = "procedural_vocal_guide"
            quality_status = "preview_only"
            self._render_procedural(lyrics_approved, midi_metadata, vocals_path)
            log_path.write_text(
                "Voz guia procedural generada desde lyrics_approved.json y midi_metadata.json.\n",
                encoding="utf-8",
            )

        artifact = self.storage.create_song_artifact(
            artifact_id=f"{song_id}_vocals_wav",
            song_id=song_id,
            phase=SongPhase.VOCAL_SYNTHESIS.value,
            artifact_type="vocals_wav",
            file_path=str(Path(vocals_path)),
            metadata={
                "mode": mode,
                "quality_status": quality_status,
                "voice_style": voice_style,
                "log_path": str(log_path),
            },
        )
        self.storage.create_song_event(
            song_id=song_id,
            phase=SongPhase.VOCAL_SYNTHESIS.value,
            status=SongPhaseStatus.COMPLETED.value,
            progress=100,
            message="Voz cantada/guia generada desde letra aprobada y melodia vocal MIDI.",
            active_model="singing-voice-provider" if self.command_template else "local-vocal-guide",
            payload={"vocals": str(vocals_path), "mode": mode, "quality_status": quality_status, "log": str(log_path)},
            artifact_id=str(artifact["artifact_id"]),
        )
        project = self.storage.update_song_project_phase(
            song_id,
            SongPhase.VOICE_CONVERSION.value,
            SongPhaseStatus.READY.value,
        )
        return {
            "project": project,
            "vocals": str(vocals_path),
            "mode": mode,
            "quality_status": quality_status,
            "artifact": artifact,
            "log": str(log_path),
        }

    def get(self, song_id: str) -> dict[str, object]:
        path = self.storage.data_dir / "projects" / song_id / "vocals.wav"
        if not path.exists():
            raise ValueError("Este proyecto aun no tiene vocals.wav.")
        return {
            "song_id": song_id,
            "vocals": str(path),
            "size_bytes": path.stat().st_size,
            "quality": self._quality_metadata(song_id),
        }

    def _quality_metadata(self, song_id: str) -> dict[str, object]:
        project = self.storage.get_song_project(song_id) or {}
        artifacts = [dict(item) for item in list(project.get("artifacts", []))]
        matches = [artifact for artifact in artifacts if str(artifact.get("type", "")) == "vocals_wav"]
        if not matches:
            return {"mode": "", "quality_status": "unknown"}
        metadata = dict(matches[-1].get("metadata", {}))
        return {
            "mode": str(metadata.get("mode", "")),
            "quality_status": str(metadata.get("quality_status", "unknown")),
        }

    def _run_command(self, project_dir: Path, prompt_path: Path, vocals_path: Path, log_path: Path) -> None:
        command = self.command_template.format(
            prompt_path=str(prompt_path),
            lyrics_path=str(project_dir / "lyrics_approved.json"),
            midi_path=str(project_dir / "song_base.mid"),
            midi_metadata_path=str(project_dir / "midi_metadata.json"),
            output_path=str(vocals_path),
            instrumental_path=str(project_dir / "instrumental.wav"),
            work_dir=str(project_dir),
        )
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=self.timeout_seconds,
        )
        log_path.write_text(
            f"$ {command}\n\nSTDOUT:\n{result.stdout or ''}\n\nSTDERR:\n{result.stderr or ''}",
            encoding="utf-8",
        )
        if result.returncode != 0:
            raise ValueError(f"El provider local de voz cantada fallo: {(result.stderr or result.stdout).strip()}")
        if not vocals_path.exists() or vocals_path.stat().st_size == 0:
            raise ValueError("El provider local de voz cantada no genero vocals.wav.")

    def _render_procedural(
        self,
        lyrics_approved: dict[str, object],
        midi_metadata: dict[str, object],
        output_path: Path,
    ) -> None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        bpm = int(midi_metadata.get("bpm", 80))
        duration_seconds = int(midi_metadata.get("duration_seconds", 60))
        melody = [dict(item) for item in list(midi_metadata.get("vocal_melody", []))]
        words = self._words(lyrics_approved)
        frames = array("h", [0] * (duration_seconds * self.SAMPLE_RATE))
        for index, note in enumerate(melody):
            start = int(float(note.get("start_seconds", 0)) * self.SAMPLE_RATE)
            length = max(1, int(float(note.get("duration_seconds", 1)) * self.SAMPLE_RATE))
            frequency = self._midi_to_frequency(int(note.get("midi_note", 60)))
            word = words[index % len(words)]
            vowel = self._dominant_vowel(word)
            for offset in range(length):
                frame_index = start + offset
                if frame_index >= len(frames):
                    break
                time = frame_index / self.SAMPLE_RATE
                note_time = offset / self.SAMPLE_RATE
                envelope = self._adsr(note_time, length / self.SAMPLE_RATE, 0.04, 0.12)
                vibrato = 1 + 0.008 * math.sin(2 * math.pi * 4.7 * time)
                base = math.sin(2 * math.pi * frequency * vibrato * time) * 0.62
                harmonic = math.sin(2 * math.pi * frequency * 2 * vibrato * time) * 0.18
                color = self._vowel_color(vowel, frequency, time) * 0.36
                breath = math.sin(2 * math.pi * frequency * 0.5 * time) * 0.05
                frames[frame_index] = self._clip(frames[frame_index] + (base + harmonic + color + breath) * envelope * 12000)

        with wave.open(str(output_path), "wb") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(self.SAMPLE_RATE)
            wav_file.writeframes(frames.tobytes())

    def _prompt(self, lyrics_approved: dict[str, object], voice_style: str) -> str:
        title = str(lyrics_approved.get("lyrics", {}).get("title", "song"))
        return f"Synthesize sung vocals for {title}. Voice style: {voice_style}. Follow song_base.mid vocal_melody."

    def _words(self, lyrics_approved: dict[str, object]) -> list[str]:
        lyrics = dict(lyrics_approved.get("lyrics") or {})
        lines: list[str] = []
        for section in list(lyrics.get("sections", [])):
            lines.extend(str(line) for line in list(dict(section).get("lines", [])))
        words = re.findall(r"[A-Za-zÁÉÍÓÚáéíóúÑñ]+", " ".join(lines).lower())
        return words or ["canta", "suave", "amor"]

    def _dominant_vowel(self, word: str) -> str:
        for letter in word:
            normalized = self._normalize_vowel(letter)
            if normalized in self.VOWELS:
                return normalized
        return "a"

    def _normalize_vowel(self, letter: str) -> str:
        return {
            "á": "a",
            "é": "e",
            "í": "i",
            "ó": "o",
            "ú": "u",
        }.get(letter.lower(), letter.lower())

    def _vowel_color(self, vowel: str, frequency: float, time: float) -> float:
        formants = {
            "a": (2.0, 3.0, 4.0),
            "e": (2.4, 3.6, 5.0),
            "i": (3.0, 4.4, 6.0),
            "o": (1.6, 2.4, 3.4),
            "u": (1.3, 2.0, 2.8),
        }[vowel]
        return sum(
            math.sin(2 * math.pi * frequency * ratio * time) * (0.24 / (index + 1))
            for index, ratio in enumerate(formants)
        )

    def _midi_to_frequency(self, midi_note: int) -> float:
        return 440.0 * (2 ** ((midi_note - 69) / 12))

    def _adsr(self, time: float, length: float, attack: float, release: float) -> float:
        if time < attack:
            return time / max(attack, 0.001)
        if time > length - release:
            return max(0.0, (length - time) / max(release, 0.001))
        return 1.0

    def _clip(self, value: float) -> int:
        return max(-32767, min(32767, int(value)))
