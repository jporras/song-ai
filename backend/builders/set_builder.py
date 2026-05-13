from datetime import datetime, timezone
from pathlib import Path

from core.storage import StorageManager
from models import AssetType, SongSet
from utils.ids import generate_id


class SetBuilder:
    def __init__(self, storage: StorageManager) -> None:
        self.storage = storage

    def create_first_valid_set(
        self,
        project_name: str = "Proyecto automatico",
        description: str = "Proyecto creado con los primeros drafts disponibles para validar instrumental, melodia y letra.",
    ) -> Path:
        instrumentals = self.storage.list_asset_drafts_by_type(AssetType.INSTRUMENTAL)
        melodies = self.storage.list_asset_drafts_by_type(AssetType.MELODY)
        lyrics = self.storage.list_asset_drafts_by_type(AssetType.LYRICS)

        if not instrumentals or not melodies or not lyrics:
            raise ValueError("Se necesita al menos un instrumental, una melodia y una letra para crear un set.")

        song_set = SongSet(
            set_id=generate_id("set"),
            project_name=project_name,
            description=description,
            created_at=datetime.now(timezone.utc).isoformat(),
            instrumental_id=instrumentals[0]["asset_id"],
            melody_id=melodies[0]["asset_id"],
            lyrics_id=lyrics[0]["asset_id"],
            compatibility_data={
                "status": "mock_validated",
                "rule": "first_available_assets",
            },
        )
        return self.storage.save_song_set(song_set)
