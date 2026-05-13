from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path

from models.intent import MusicalIntent
from models.manifest import Manifest


class AssetType(StrEnum):
    INSTRUMENTAL = "instrumental"
    MELODY = "melody"
    LYRICS = "lyrics"


@dataclass(frozen=True)
class AssetDraft:
    asset_id: str
    asset_type: AssetType
    manifest: Manifest
    intent: MusicalIntent
    files: list[Path] = field(default_factory=list)
    metadata: dict[str, str] = field(default_factory=dict)

