from __future__ import annotations

from pathlib import Path
import struct

from core.storage import StorageManager
from models.song_workflow import SongPhase, SongPhaseStatus


class MidiGenerationService:
    TICKS_PER_BEAT = 480
    NOTE_NAMES = {
        "C": 60,
        "C#": 61,
        "Db": 61,
        "D": 62,
        "D#": 63,
        "Eb": 63,
        "E": 64,
        "F": 65,
        "F#": 66,
        "Gb": 66,
        "G": 67,
        "G#": 68,
        "Ab": 68,
        "A": 69,
        "A#": 70,
        "Bb": 70,
        "B": 71,
    }

    MAJOR_DEGREES = {
        "I": [0, 4, 7],
        "ii": [2, 5, 9],
        "iii": [4, 7, 11],
        "IV": [5, 9, 12],
        "V": [7, 11, 14],
        "vi": [9, 12, 16],
        "vii": [11, 14, 17],
    }
    MINOR_DEGREES = {
        "i": [0, 3, 7],
        "III": [3, 7, 10],
        "iv": [5, 8, 12],
        "V": [7, 11, 14],
        "VI": [8, 12, 15],
        "VII": [10, 14, 17],
    }

    def __init__(self, storage: StorageManager) -> None:
        self.storage = storage

    def generate(self, song_id: str, music_plan: dict[str, object]) -> dict[str, object]:
        project_dir = self.storage.data_dir / "projects" / song_id
        midi_path = project_dir / "song_base.mid"
        metadata_path = project_dir / "midi_metadata.json"
        project_dir.mkdir(parents=True, exist_ok=True)

        metadata = self._metadata(song_id, music_plan)
        midi_bytes = self._build_midi(metadata)
        midi_path.write_bytes(midi_bytes)
        self.storage.write_json(metadata_path, metadata)

        midi_artifact = self.storage.create_song_artifact(
            artifact_id=f"{song_id}_song_base_mid",
            song_id=song_id,
            phase=SongPhase.MIDI_GENERATION.value,
            artifact_type="midi",
            file_path=str(Path(midi_path)),
            metadata={
                "bpm": metadata["bpm"],
                "key": metadata["key"],
                "duration_seconds": metadata["duration_seconds"],
                "tracks": metadata["tracks"],
            },
        )
        metadata_artifact = self.storage.create_song_artifact(
            artifact_id=f"{song_id}_midi_metadata",
            song_id=song_id,
            phase=SongPhase.MIDI_GENERATION.value,
            artifact_type="midi_metadata_json",
            file_path=str(Path(metadata_path)),
            metadata={"midi_path": str(midi_path)},
        )
        self.storage.create_song_event(
            song_id=song_id,
            phase=SongPhase.MIDI_GENERATION.value,
            status=SongPhaseStatus.COMPLETED.value,
            progress=100,
            message="El director tecnico coordino la creacion del MIDI base con acordes, melodia vocal guia y marcadores de seccion.",
            active_model="qwen",
            payload={"midi": str(midi_path), "metadata": str(metadata_path)},
            artifact_id=str(midi_artifact["artifact_id"]),
        )
        project = self.storage.update_song_project_phase(
            song_id,
            SongPhase.INSTRUMENTAL_GENERATION.value,
            SongPhaseStatus.READY.value,
        )
        return {
            "project": project,
            "midi": str(midi_path),
            "metadata": metadata,
            "artifacts": [midi_artifact, metadata_artifact],
        }

    def get(self, song_id: str) -> dict[str, object]:
        project_dir = self.storage.data_dir / "projects" / song_id
        midi_path = project_dir / "song_base.mid"
        metadata_path = project_dir / "midi_metadata.json"
        if not midi_path.exists() or not metadata_path.exists():
            raise ValueError("Este proyecto aun no tiene song_base.mid y midi_metadata.json.")
        return {
            "song_id": song_id,
            "midi": str(midi_path),
            "metadata": self.storage.read_json(metadata_path),
        }

    def _metadata(self, song_id: str, music_plan: dict[str, object]) -> dict[str, object]:
        bpm = int(music_plan.get("bpm", 80))
        key = str(music_plan.get("key", "C major"))
        timeline = [dict(item) for item in list(music_plan.get("structure_timeline", []))]
        progression = [str(item) for item in list(music_plan.get("chord_progression", ["I", "V", "vi", "IV"]))]
        duration_seconds = int(music_plan.get("duration_seconds", 120))
        return {
            "song_id": song_id,
            "bpm": bpm,
            "key": key,
            "time_signature": str(music_plan.get("time_signature", "4/4")),
            "duration_seconds": duration_seconds,
            "ticks_per_beat": self.TICKS_PER_BEAT,
            "tracks": ["section_markers", "chords", "vocal_melody"],
            "section_markers": timeline,
            "chord_progression": progression,
            "vocal_melody": self._vocal_melody(timeline, key),
        }

    def _build_midi(self, metadata: dict[str, object]) -> bytes:
        bpm = int(metadata["bpm"])
        header = b"MThd" + struct.pack(">IHHH", 6, 1, 3, self.TICKS_PER_BEAT)
        tracks = [
            self._track_chunk(self._meta_track_events(bpm, metadata)),
            self._track_chunk(self._chord_track_events(metadata)),
            self._track_chunk(self._melody_track_events(metadata)),
        ]
        return header + b"".join(tracks)

    def _track_chunk(self, events: bytes) -> bytes:
        return b"MTrk" + struct.pack(">I", len(events)) + events

    def _meta_track_events(self, bpm: int, metadata: dict[str, object]) -> bytes:
        events = bytearray()
        events.extend(self._delta(0) + b"\xff\x03" + self._text("Song AI sections"))
        microseconds_per_beat = round(60_000_000 / bpm)
        events.extend(self._delta(0) + b"\xff\x51\x03" + microseconds_per_beat.to_bytes(3, "big"))
        events.extend(self._delta(0) + b"\xff\x58\x04\x04\x02\x18\x08")
        previous_tick = 0
        for marker in list(metadata.get("section_markers", [])):
            marker_dict = dict(marker)
            tick = self._seconds_to_ticks(int(marker_dict.get("start_seconds", 0)), bpm)
            events.extend(self._delta(max(0, tick - previous_tick)) + b"\xff\x06" + self._text(str(marker_dict.get("section", "section"))))
            previous_tick = tick
        events.extend(self._delta(0) + b"\xff\x2f\x00")
        return bytes(events)

    def _chord_track_events(self, metadata: dict[str, object]) -> bytes:
        bpm = int(metadata["bpm"])
        root = self._key_root(str(metadata["key"])) - 12
        progression = [str(item) for item in list(metadata.get("chord_progression", []))] or ["I", "V", "vi", "IV"]
        events = bytearray()
        events.extend(self._delta(0) + bytes([0xC0, 0]))
        previous_tick = 0
        for index, marker in enumerate(list(metadata.get("section_markers", []))):
            marker_dict = dict(marker)
            start_tick = self._seconds_to_ticks(int(marker_dict.get("start_seconds", 0)), bpm)
            duration_tick = max(self.TICKS_PER_BEAT, self._seconds_to_ticks(int(marker_dict.get("duration_seconds", 4)), bpm))
            chord = progression[index % len(progression)]
            notes = self._chord_notes(root, chord, str(metadata["key"]))
            events.extend(self._delta(max(0, start_tick - previous_tick)))
            for note in notes:
                events.extend(bytes([0x90, note, 72]))
            events.extend(self._delta(duration_tick))
            for note in notes:
                events.extend(bytes([0x80, note, 0]))
            previous_tick = start_tick + duration_tick
        events.extend(self._delta(0) + b"\xff\x2f\x00")
        return bytes(events)

    def _melody_track_events(self, metadata: dict[str, object]) -> bytes:
        bpm = int(metadata["bpm"])
        events = bytearray()
        events.extend(self._delta(0) + bytes([0xC1, 53]))
        previous_tick = 0
        for item in list(metadata.get("vocal_melody", [])):
            note_event = dict(item)
            start_tick = self._seconds_to_ticks(int(note_event["start_seconds"]), bpm)
            duration_tick = max(self.TICKS_PER_BEAT // 2, self._seconds_to_ticks(int(note_event["duration_seconds"]), bpm))
            note = int(note_event["midi_note"])
            events.extend(self._delta(max(0, start_tick - previous_tick)) + bytes([0x91, note, 88]))
            events.extend(self._delta(duration_tick) + bytes([0x81, note, 0]))
            previous_tick = start_tick + duration_tick
        events.extend(self._delta(0) + b"\xff\x2f\x00")
        return bytes(events)

    def _vocal_melody(self, timeline: list[dict[str, object]], key: str) -> list[dict[str, object]]:
        root = self._key_root(key)
        contour = [0, 2, 4, 7, 5, 4, 2, 0]
        events: list[dict[str, object]] = []
        for marker in timeline:
            section = str(marker.get("section", "section"))
            start = int(marker.get("start_seconds", 0))
            duration = max(4, int(marker.get("duration_seconds", 4)))
            note_duration = max(2, duration // 4)
            for index in range(max(1, duration // note_duration)):
                events.append(
                    {
                        "section": section,
                        "start_seconds": start + index * note_duration,
                        "duration_seconds": note_duration,
                        "midi_note": root + contour[index % len(contour)],
                    }
                )
        return events

    def _chord_notes(self, root: int, chord: str, key: str) -> list[int]:
        degrees = self.MINOR_DEGREES if "minor" in key.lower() else self.MAJOR_DEGREES
        intervals = degrees.get(chord, self.MAJOR_DEGREES.get(chord, [0, 4, 7]))
        return [root + interval for interval in intervals]

    def _key_root(self, key: str) -> int:
        token = key.split()[0]
        return self.NOTE_NAMES.get(token, 60)

    def _seconds_to_ticks(self, seconds: int, bpm: int) -> int:
        beats = seconds * bpm / 60
        return round(beats * self.TICKS_PER_BEAT)

    def _delta(self, value: int) -> bytes:
        value = max(0, int(value))
        buffer = value & 0x7F
        while value >> 7:
            value >>= 7
            buffer <<= 8
            buffer |= ((value & 0x7F) | 0x80)
        output = bytearray()
        while True:
            output.append(buffer & 0xFF)
            if buffer & 0x80:
                buffer >>= 8
            else:
                break
        return bytes(output)

    def _text(self, value: str) -> bytes:
        encoded = value.encode("utf-8")
        return self._delta(len(encoded)) + encoded
