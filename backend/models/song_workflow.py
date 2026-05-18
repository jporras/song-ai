from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from uuid import uuid4


class SongPhase(str, Enum):
    SONG_SPEC_COLLECTION = "SONG_SPEC_COLLECTION"
    LYRICS_GENERATION = "LYRICS_GENERATION"
    LYRICS_TECHNICAL_REVIEW = "LYRICS_TECHNICAL_REVIEW"
    MUSIC_PLAN_GENERATION = "MUSIC_PLAN_GENERATION"
    MIDI_GENERATION = "MIDI_GENERATION"
    INSTRUMENTAL_GENERATION = "INSTRUMENTAL_GENERATION"
    VOCAL_SYNTHESIS = "VOCAL_SYNTHESIS"
    VOICE_CONVERSION = "VOICE_CONVERSION"
    MIXING = "MIXING"
    MASTERING = "MASTERING"
    EXPORT = "EXPORT"


class SongPhaseStatus(str, Enum):
    PENDING = "pending"
    WAITING_USER_INPUT = "waiting_user_input"
    READY = "ready"
    LOADING_MODEL = "loading_model"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


PHASE_SEQUENCE: list[SongPhase] = [
    SongPhase.SONG_SPEC_COLLECTION,
    SongPhase.LYRICS_GENERATION,
    SongPhase.LYRICS_TECHNICAL_REVIEW,
    SongPhase.MUSIC_PLAN_GENERATION,
    SongPhase.MIDI_GENERATION,
    SongPhase.INSTRUMENTAL_GENERATION,
    SongPhase.VOCAL_SYNTHESIS,
    SongPhase.VOICE_CONVERSION,
    SongPhase.MIXING,
    SongPhase.MASTERING,
    SongPhase.EXPORT,
]


PHASE_LABELS: dict[SongPhase, str] = {
    SongPhase.SONG_SPEC_COLLECTION: "1. Especificacion con Gemma y director tecnico",
    SongPhase.LYRICS_GENERATION: "2. Letra cantable",
    SongPhase.LYRICS_TECHNICAL_REVIEW: "3. Revision tecnica de letra",
    SongPhase.MUSIC_PLAN_GENERATION: "4. Plan musical tecnico",
    SongPhase.MIDI_GENERATION: "5. MIDI base obligatorio",
    SongPhase.INSTRUMENTAL_GENERATION: "6. Instrumental",
    SongPhase.VOCAL_SYNTHESIS: "7. Voz cantada",
    SongPhase.VOICE_CONVERSION: "8. Conversion de voz opcional",
    SongPhase.MIXING: "9. Mezcla",
    SongPhase.MASTERING: "10. Mastering",
    SongPhase.EXPORT: "11. Export",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def new_song_id() -> str:
    return f"song_{uuid4().hex[:12]}"


@dataclass(frozen=True)
class SongProject:
    id: str
    title: str
    user_id: str = "local-user"
    status: str = SongPhaseStatus.WAITING_USER_INPUT.value
    current_phase: str = SongPhase.SONG_SPEC_COLLECTION.value
    created_at: str = field(default_factory=utc_now)
    updated_at: str = field(default_factory=utc_now)

    @classmethod
    def create(cls, title: str, user_id: str = "local-user") -> "SongProject":
        return cls(id=new_song_id(), title=title.strip() or "Nueva cancion", user_id=user_id)

    def to_dict(self) -> dict[str, object]:
        return {
            "id": self.id,
            "title": self.title,
            "user_id": self.user_id,
            "status": self.status,
            "current_phase": self.current_phase,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
