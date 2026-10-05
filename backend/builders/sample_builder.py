from pathlib import Path

from datetime import datetime, timezone

from core.storage import StorageManager
from utils.ids import generate_id


class SampleBuilder:
    def __init__(self, storage: StorageManager) -> None:
        self.storage = storage

    def create_from_latest_set(self) -> Path:
        indexed_sets = self.storage.list_indexed_sets()
        if not indexed_sets:
            raise ValueError("No hay sets validos. Crea un set antes de generar sample.")
        return self.create_for_set(str(indexed_sets[0]["set_id"]))

    def create_for_set(self, set_id: str) -> Path:
        indexed_set = self.storage.get_indexed_set(set_id)
        if indexed_set is None:
            raise ValueError("No existe el set activo solicitado para generar el sample.")
        self.storage.validate_song_set_assets(
            str(indexed_set["instrumental_id"]),
            str(indexed_set["melody_id"]),
            str(indexed_set["lyrics_id"]),
        )

        sample_id = generate_id("sample")
        sample_dir = self.storage.data_dir / "samples" / sample_id
        sample_dir.mkdir(parents=True, exist_ok=True)
        self.storage.save_legacy_sample(
            {
                "sample_id": sample_id,
                "set_id": indexed_set["set_id"],
                "provider": "mock-local",
                "status": "mock_quality_checkpoint",
                "purpose": "quality checkpoint before full soundtrack, sung voice and mix",
                "approval_status": "pending",
                "set_fingerprint": self.storage.set_generation_fingerprint(set_id),
                "not_a_short": True,
                "created_at": datetime.now(timezone.utc).isoformat(),
            },
            sample_dir / "sample.json",
        )
        (sample_dir / "preview.txt").write_text(
            "Mock quality checkpoint placeholder.\n"
            f"Set: {indexed_set['set_id']}\n"
            "This validates the set before generating the complete song pipeline.\n"
            "It is not a 20-second Short format and not the final song.\n",
            encoding="utf-8",
        )
        return sample_dir

