from pathlib import Path

from audio.formats import planned_final_mix_exports, planned_stem_exports
from core.storage import StorageManager


class ExportBuilder:
    def __init__(self, storage: StorageManager) -> None:
        self.storage = storage

    def prepare_latest_song_exports(self) -> Path:
        latest_song = self.storage.get_latest_song()
        if latest_song is None:
            raise ValueError("No hay cancion completa para exportar.")

        song_dir = Path(str(latest_song["path"]))
        exports_dir = song_dir / "exports"
        stems_dir = song_dir / "stems"
        exports_dir.mkdir(parents=True, exist_ok=True)
        stems_dir.mkdir(parents=True, exist_ok=True)

        self.storage.write_json(
            exports_dir / "manifest.json",
            {
                "song_id": latest_song["song_id"],
                "mode": "mock_export",
                "final_mix_formats": planned_final_mix_exports(),
                "stem_formats": planned_stem_exports(),
            },
        )
        (exports_dir / "lyrics.md").write_text(
            "# Lyrics export placeholder\n\nLa letra final se copiara aqui cuando el builder use assets reales.\n",
            encoding="utf-8",
        )
        return exports_dir
