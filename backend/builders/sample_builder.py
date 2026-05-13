from pathlib import Path

from core.storage import StorageManager
from utils.ids import generate_id


class SampleBuilder:
    def __init__(self, storage: StorageManager) -> None:
        self.storage = storage

    def create_from_latest_set(self) -> Path:
        latest_set = self.storage.get_latest_song_set()
        if latest_set is None:
            raise ValueError("No hay sets validos. Crea un set antes de generar sample.")

        sample_id = generate_id("sample")
        sample_dir = self.storage.data_dir / "samples" / sample_id
        sample_dir.mkdir(parents=True, exist_ok=True)
        self.storage.write_json(
            sample_dir / "sample.json",
            {
                "sample_id": sample_id,
                "set_id": latest_set["set_id"],
                "provider": "mock-local",
                "status": "mock_quality_checkpoint",
                "purpose": "quality checkpoint before full soundtrack, sung voice and mix",
                "not_a_short": True,
            },
        )
        (sample_dir / "preview.txt").write_text(
            "Mock quality checkpoint placeholder.\n"
            f"Set: {latest_set['set_id']}\n"
            "This validates the set before generating the complete song pipeline.\n"
            "It is not a 20-second Short format and not the final song.\n",
            encoding="utf-8",
        )
        return sample_dir

