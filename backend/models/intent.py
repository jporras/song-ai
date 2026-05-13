from dataclasses import dataclass, field


@dataclass(frozen=True)
class MusicalIntent:
    bpm: int
    key: str
    mood: str
    instruments: list[str]
    energy: str
    vocal_style: str
    lyrics_context: str
    placeholders: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, object]:
        return {
            "bpm": self.bpm,
            "key": self.key,
            "mood": self.mood,
            "instruments": self.instruments,
            "energy": self.energy,
            "vocal_style": self.vocal_style,
            "lyrics_context": self.lyrics_context,
            "placeholders": self.placeholders,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> "MusicalIntent":
        return cls(
            bpm=int(payload["bpm"]),
            key=str(payload["key"]),
            mood=str(payload["mood"]),
            instruments=[str(item) for item in payload["instruments"]],
            energy=str(payload["energy"]),
            vocal_style=str(payload["vocal_style"]),
            lyrics_context=str(payload["lyrics_context"]),
            placeholders={str(key): str(value) for key, value in dict(payload.get("placeholders", {})).items()},
        )
