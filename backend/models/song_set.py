from dataclasses import dataclass, field


@dataclass(frozen=True)
class SongSet:
    set_id: str
    project_name: str
    description: str
    created_at: str
    instrumental_id: str
    melody_id: str
    lyrics_id: str
    compatibility_data: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, object]:
        return {
            "set_id": self.set_id,
            "project_name": self.project_name,
            "description": self.description,
            "created_at": self.created_at,
            "instrumental_id": self.instrumental_id,
            "melody_id": self.melody_id,
            "lyrics_id": self.lyrics_id,
            "compatibility_data": self.compatibility_data,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> "SongSet":
        return cls(
            set_id=str(payload["set_id"]),
            project_name=str(payload.get("project_name", payload["set_id"])),
            description=str(payload.get("description", "")),
            created_at=str(payload.get("created_at", "")),
            instrumental_id=str(payload["instrumental_id"]),
            melody_id=str(payload["melody_id"]),
            lyrics_id=str(payload["lyrics_id"]),
            compatibility_data={
                str(key): str(value) for key, value in dict(payload.get("compatibility_data", {})).items()
            },
        )
