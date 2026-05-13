from pathlib import Path

from core.storage import StorageManager
from utils.ids import generate_id


class TemplateBuilder:
    def __init__(self, storage: StorageManager) -> None:
        self.storage = storage

    def save_latest_set_template(self) -> Path:
        latest_set = self.storage.get_latest_song_set()
        if latest_set is None:
            raise ValueError("No hay set valido para guardar como plantilla.")

        template_id = generate_id("template")
        template_dir = self.storage.data_dir / "templates" / template_id
        template_dir.mkdir(parents=True, exist_ok=True)
        self.storage.write_json(
            template_dir / "template.json",
            {
                "template_id": template_id,
                "source_type": "song_set",
                "source_set_id": latest_set["set_id"],
                "instrumental_id": latest_set["instrumental_id"],
                "melody_id": latest_set["melody_id"],
                "lyrics_id": latest_set["lyrics_id"],
                "compatibility_data": latest_set.get("compatibility_data", {}),
            },
        )
        return template_dir
