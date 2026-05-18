from __future__ import annotations

from pathlib import Path

from core.storage import StorageManager
from models.song_workflow import SongPhase, SongPhaseStatus


class MusicPlanService:
    def __init__(self, storage: StorageManager) -> None:
        self.storage = storage

    def generate(
        self,
        song_id: str,
        spec: dict[str, object],
        lyrics_approved: dict[str, object],
    ) -> dict[str, object]:
        duration_seconds = int(spec.get("duration_seconds", 120))
        structure = self._structure(spec, lyrics_approved)
        timeline = self._timeline(structure, duration_seconds)
        plan = {
            "song_id": song_id,
            "title": str(spec.get("title", "Nueva cancion")),
            "bpm": int(spec.get("bpm", 80)),
            "key": str(spec.get("key", "C major")),
            "time_signature": "4/4",
            "chord_progression": self._chord_progression(str(spec.get("key", "C major"))),
            "duration_seconds": duration_seconds,
            "structure_timeline": timeline,
            "section_intensity": self._intensity_map(timeline),
            "instrumentation_prompt": self._instrumentation_prompt(spec),
            "midi_requirements": {
                "must_include_vocal_melody": True,
                "must_include_chords": True,
                "must_include_section_markers": True,
                "tempo_bpm": int(spec.get("bpm", 80)),
                "key": str(spec.get("key", "C major")),
            },
        }
        path = self.storage.data_dir / "projects" / song_id / "music_plan.json"
        self.storage.write_json(path, plan)
        artifact = self.storage.create_song_artifact(
            artifact_id=f"{song_id}_music_plan",
            song_id=song_id,
            phase=SongPhase.MUSIC_PLAN_GENERATION.value,
            artifact_type="music_plan_json",
            file_path=str(Path(path)),
            metadata={
                "bpm": plan["bpm"],
                "key": plan["key"],
                "duration_seconds": duration_seconds,
                "section_count": len(timeline),
            },
        )
        self.storage.create_song_event(
            song_id=song_id,
            phase=SongPhase.MUSIC_PLAN_GENERATION.value,
            status=SongPhaseStatus.COMPLETED.value,
            progress=100,
            message="El director tecnico genero el plan musical tecnico: tempo, tonalidad, acordes, estructura por segundos e intensidad.",
            active_model="qwen",
            payload={"music_plan": str(path), "section_count": len(timeline)},
            artifact_id=str(artifact["artifact_id"]),
        )
        project = self.storage.update_song_project_phase(
            song_id,
            SongPhase.MIDI_GENERATION.value,
            SongPhaseStatus.READY.value,
        )
        return {
            "project": project,
            "music_plan": plan,
            "artifact": artifact,
        }

    def get(self, song_id: str) -> dict[str, object]:
        path = self.storage.data_dir / "projects" / song_id / "music_plan.json"
        if not path.exists():
            raise ValueError("Este proyecto aun no tiene music_plan.json.")
        return {
            "song_id": song_id,
            "music_plan": self.storage.read_json(path),
            "path": str(path),
        }

    def _structure(self, spec: dict[str, object], lyrics_approved: dict[str, object]) -> list[str]:
        lyrics = dict(lyrics_approved.get("lyrics") or {})
        structure = [str(item) for item in list(lyrics.get("structure", []))]
        if structure:
            return structure
        return [str(item) for item in list(spec.get("structure", []))] or [
            "intro",
            "verse_1",
            "chorus",
            "verse_2",
            "bridge",
            "final_chorus",
            "outro",
        ]

    def _timeline(self, structure: list[str], duration_seconds: int) -> list[dict[str, object]]:
        weights = [self._section_weight(section) for section in structure]
        total_weight = sum(weights) or 1
        cursor = 0
        timeline: list[dict[str, object]] = []
        for index, section in enumerate(structure):
            if index == len(structure) - 1:
                section_duration = max(4, duration_seconds - cursor)
            else:
                section_duration = max(4, round(duration_seconds * weights[index] / total_weight))
            start = cursor
            end = min(duration_seconds, start + section_duration)
            timeline.append(
                {
                    "section": section,
                    "start_seconds": start,
                    "end_seconds": end,
                    "duration_seconds": end - start,
                }
            )
            cursor = end
        return timeline

    def _section_weight(self, section: str) -> int:
        section = section.lower()
        if "intro" in section or "outro" in section:
            return 1
        if "chorus" in section:
            return 3
        if "bridge" in section:
            return 2
        return 3

    def _intensity_map(self, timeline: list[dict[str, object]]) -> dict[str, str]:
        intensity = {}
        for item in timeline:
            section = str(item["section"])
            lower = section.lower()
            if "intro" in lower or "outro" in lower:
                intensity[section] = "low"
            elif "chorus" in lower:
                intensity[section] = "medium"
            elif "bridge" in lower:
                intensity[section] = "medium-low"
            else:
                intensity[section] = "low-medium"
        return intensity

    def _chord_progression(self, key: str) -> list[str]:
        if "minor" in key.lower() or "minor" in key.lower():
            return ["i", "VI", "III", "VII"]
        return ["I", "V", "vi", "IV"]

    def _instrumentation_prompt(self, spec: dict[str, object]) -> str:
        instruments = ", ".join(str(item) for item in list(spec.get("instruments", [])))
        emotion = str(spec.get("emotion", "warm"))
        song_type = str(spec.get("song_type", "personal_song"))
        return (
            f"{song_type} arrangement with {instruments}; emotional color: {emotion}; "
            "support a clear sung vocal melody, gentle dynamics, no harsh tones."
        )
