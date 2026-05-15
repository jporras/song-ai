from __future__ import annotations

from array import array
import math
from pathlib import Path
import subprocess
import wave

from core.storage import StorageManager
from models.song_workflow import SongPhase, SongPhaseStatus


class InstrumentalGenerationService:
    SAMPLE_RATE = 44100
    ROOT_FREQUENCIES = {
        "C": 261.63,
        "D": 293.66,
        "E": 329.63,
        "F": 349.23,
        "G": 392.00,
        "A": 440.00,
        "B": 493.88,
    }
    MAJOR_INTERVALS = {
        "I": (0, 4, 7),
        "ii": (2, 5, 9),
        "iii": (4, 7, 11),
        "IV": (5, 9, 12),
        "V": (7, 11, 14),
        "vi": (9, 12, 16),
    }
    MINOR_INTERVALS = {
        "i": (0, 3, 7),
        "III": (3, 7, 10),
        "iv": (5, 8, 12),
        "V": (7, 11, 14),
        "VI": (8, 12, 15),
        "VII": (10, 14, 17),
    }

    def __init__(self, storage: StorageManager, command_template: str = "", timeout_seconds: int = 3600) -> None:
        self.storage = storage
        self.command_template = command_template.strip()
        self.timeout_seconds = timeout_seconds

    def generate(self, song_id: str, music_plan: dict[str, object], midi_path: str) -> dict[str, object]:
        project_dir = self.storage.data_dir / "projects" / song_id
        instrumental_path = project_dir / "instrumental.wav"
        prompt_path = project_dir / "instrumental_prompt.txt"
        log_path = project_dir / "instrumental_generation.log"
        prompt_path.write_text(str(music_plan.get("instrumentation_prompt", "")), encoding="utf-8")

        if self.command_template:
            mode = "local_command"
            self._run_command(music_plan, midi_path, prompt_path, instrumental_path, log_path)
        else:
            mode = "procedural_local"
            self._render_procedural(music_plan, instrumental_path)
            log_path.write_text(
                "Instrumental procedural local generado desde music_plan.json y song_base.mid.\n",
                encoding="utf-8",
            )

        artifact = self.storage.create_song_artifact(
            artifact_id=f"{song_id}_instrumental_wav",
            song_id=song_id,
            phase=SongPhase.INSTRUMENTAL_GENERATION.value,
            artifact_type="instrumental_wav",
            file_path=str(Path(instrumental_path)),
            metadata={
                "mode": mode,
                "bpm": int(music_plan.get("bpm", 80)),
                "key": str(music_plan.get("key", "C major")),
                "midi_path": midi_path,
                "log_path": str(log_path),
            },
        )
        self.storage.create_song_event(
            song_id=song_id,
            phase=SongPhase.INSTRUMENTAL_GENERATION.value,
            status=SongPhaseStatus.COMPLETED.value,
            progress=100,
            message="Instrumental generado desde el plan musical y el MIDI base.",
            active_model="musicgen" if self.command_template else "local-procedural",
            payload={"instrumental": str(instrumental_path), "mode": mode, "log": str(log_path)},
            artifact_id=str(artifact["artifact_id"]),
        )
        project = self.storage.update_song_project_phase(
            song_id,
            SongPhase.VOCAL_SYNTHESIS.value,
            SongPhaseStatus.READY.value,
        )
        return {
            "project": project,
            "instrumental": str(instrumental_path),
            "mode": mode,
            "artifact": artifact,
            "log": str(log_path),
        }

    def get(self, song_id: str) -> dict[str, object]:
        path = self.storage.data_dir / "projects" / song_id / "instrumental.wav"
        if not path.exists():
            raise ValueError("Este proyecto aun no tiene instrumental.wav.")
        return {
            "song_id": song_id,
            "instrumental": str(path),
            "size_bytes": path.stat().st_size,
        }

    def _run_command(
        self,
        music_plan: dict[str, object],
        midi_path: str,
        prompt_path: Path,
        instrumental_path: Path,
        log_path: Path,
    ) -> None:
        command = self.command_template.format(
            prompt_path=str(prompt_path),
            output_path=str(instrumental_path),
            midi_path=midi_path,
            music_plan_path=str(prompt_path.parent / "music_plan.json"),
            work_dir=str(prompt_path.parent),
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
            raise ValueError(f"El provider local de instrumental fallo: {(result.stderr or result.stdout).strip()}")
        if not instrumental_path.exists() or instrumental_path.stat().st_size == 0:
            raise ValueError("El provider local de instrumental no genero instrumental.wav.")

    def _render_procedural(self, music_plan: dict[str, object], output_path: Path) -> None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        bpm = int(music_plan.get("bpm", 80))
        key = str(music_plan.get("key", "C major"))
        root = self._root_frequency(key) / 2
        progression = [str(item) for item in list(music_plan.get("chord_progression", ["I", "V", "vi", "IV"]))]
        timeline = [dict(item) for item in list(music_plan.get("structure_timeline", []))]
        duration_seconds = int(music_plan.get("duration_seconds", 60))
        total_frames = max(1, duration_seconds * self.SAMPLE_RATE)
        beat_seconds = 60 / bpm
        bar_seconds = beat_seconds * 4
        frames = array("h")

        for frame in range(total_frames):
            time = frame / self.SAMPLE_RATE
            section = self._section_at(timeline, time)
            intensity = self._intensity_gain(section)
            chord_name = progression[int(time / bar_seconds) % len(progression)]
            chord = self._chord_frequencies(root, chord_name, key)
            pad = sum(math.sin(2 * math.pi * freq * time) * 0.09 for freq in chord)
            bass = math.sin(2 * math.pi * (chord[0] / 2) * time) * 0.11
            pulse = 0.0
            beat_position = time % beat_seconds
            if beat_position < 0.12:
                pulse = math.sin(2 * math.pi * chord[-1] * 2 * time) * self._decay(beat_position, 0.12) * 0.16
            value = (pad + bass + pulse) * intensity * 10500
            frames.append(self._clip(value))

        with wave.open(str(output_path), "wb") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(self.SAMPLE_RATE)
            wav_file.writeframes(frames.tobytes())

    def _section_at(self, timeline: list[dict[str, object]], time: float) -> str:
        for item in timeline:
            if float(item.get("start_seconds", 0)) <= time < float(item.get("end_seconds", 0)):
                return str(item.get("section", "section"))
        return str(timeline[-1].get("section", "section")) if timeline else "section"

    def _intensity_gain(self, section: str) -> float:
        lower = section.lower()
        if "chorus" in lower:
            return 1.0
        if "bridge" in lower:
            return 0.82
        if "intro" in lower or "outro" in lower:
            return 0.58
        return 0.74

    def _chord_frequencies(self, root: float, chord_name: str, key: str) -> list[float]:
        intervals = self.MINOR_INTERVALS.get(chord_name) if "minor" in key.lower() else self.MAJOR_INTERVALS.get(chord_name)
        intervals = intervals or self.MAJOR_INTERVALS.get(chord_name, (0, 4, 7))
        return [root * (2 ** (interval / 12)) for interval in intervals]

    def _root_frequency(self, key: str) -> float:
        token = key.split()[0][:1].upper()
        return self.ROOT_FREQUENCIES.get(token, self.ROOT_FREQUENCIES["C"])

    def _decay(self, time: float, length: float) -> float:
        position = min(1.0, max(0.0, time / max(length, 0.001)))
        return max(0.0, 1 - position * position)

    def _clip(self, value: float) -> int:
        return max(-32767, min(32767, int(value)))
