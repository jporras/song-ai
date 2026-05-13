from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass(frozen=True)
class Manifest:
    asset_id: str
    asset_type: str
    provider: str
    version: str = "0.1.0"
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, object]:
        return {
            "asset_id": self.asset_id,
            "asset_type": self.asset_type,
            "provider": self.provider,
            "version": self.version,
            "created_at": self.created_at,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> "Manifest":
        return cls(
            asset_id=str(payload["asset_id"]),
            asset_type=str(payload["asset_type"]),
            provider=str(payload["provider"]),
            version=str(payload.get("version", "0.1.0")),
            created_at=str(payload["created_at"]),
            metadata={str(key): str(value) for key, value in dict(payload.get("metadata", {})).items()},
        )
