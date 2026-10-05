from pathlib import Path
import re
from typing import Protocol

from core.storage import StorageManager


class ProfessionalArtifactSource(Protocol):
    def artifact_download_file(self, song_id: str, artifact_type: str) -> tuple[Path, str, str]: ...


class AudioDownloadService:
    def __init__(self, storage: StorageManager, professional_songs: ProfessionalArtifactSource) -> None:
        self.storage = storage
        self.professional_songs = professional_songs

    def project_file(self, set_id: str, extension: str = "mp3") -> tuple[Path, str]:
        safe_extension = self._extension(extension)
        song_set = self.storage.get_indexed_set(set_id)
        if song_set is None:
            raise ValueError("Proyecto no encontrado.")
        songs = self.storage.list_songs_for_set(set_id)
        if not songs:
            raise ValueError("El proyecto activo no tiene una cancion local completa para descargar.")
        return self._legacy_song_file(songs[0], song_set, safe_extension)

    def latest_file(self, extension: str = "mp3") -> tuple[Path, str]:
        safe_extension = self._extension(extension)
        artifact_type = f"final_song_{safe_extension}"
        for project in self.storage.list_song_projects():
            try:
                path, filename, _media_type = self.professional_songs.artifact_download_file(
                    str(project["id"]), artifact_type
                )
                return path, filename
            except ValueError:
                continue
        latest_song = self.storage.get_latest_song()
        if latest_song is None:
            raise ValueError("No hay cancion completa para descargar.")
        set_id = str(latest_song.get("set_id", ""))
        song_set = self.storage.get_indexed_set(set_id)
        if song_set is None:
            raise ValueError("La ultima cancion local no tiene un set valido.")
        return self._legacy_song_file(latest_song, song_set, safe_extension)

    def _legacy_song_file(
        self,
        song: dict[str, object],
        song_set: dict[str, object],
        extension: str,
    ) -> tuple[Path, str]:
        song_dir = Path(str(song["path"])).resolve()
        songs_root = (self.storage.data_dir / "songs").resolve()
        if songs_root not in song_dir.parents:
            raise ValueError("La cancion local no pertenece al almacenamiento de Song AI.")
        export_path = song_dir / "exports" / f"final_mix.{extension}"
        manifest_path = song_dir / "exports" / "local_final_manifest.json"
        if not export_path.is_file():
            if extension == "mp3" and (song_dir / "exports" / "final_mix.mp3.pending.txt").exists():
                raise ValueError("El MP3 aun no esta disponible. Instala ffmpeg y vuelve a generar el export.")
            raise ValueError(f"El proyecto activo no tiene final_mix.{extension}.")
        if not manifest_path.is_file():
            raise ValueError(
                "El archivo disponible es una maqueta tecnica, no una cancion final local con voz cantada. "
                "Usa 'Generar cancion local final' y espera a que se cree local_final_manifest.json."
            )
        manifest = self.storage.read_json(manifest_path)
        manifest_matches = (
            str(manifest.get("song_id", "")) == str(song["song_id"])
            and str(manifest.get("set_id", "")) == str(song["set_id"])
        )
        if not manifest_matches:
            raise ValueError("El manifest final no corresponde al proyecto activo.")
        filename = f"{self._safe_name(str(song_set.get('project_name', song['song_id'])))}.{extension}"
        return export_path, filename

    def _extension(self, extension: str) -> str:
        safe_extension = extension.lower().strip().lstrip(".")
        if safe_extension not in {"mp3", "wav"}:
            raise ValueError("Formato de descarga no soportado. Usa mp3 o wav.")
        return safe_extension

    def _safe_name(self, value: str) -> str:
        normalized = re.sub(r"[^A-Za-z0-9._-]+", "_", value.strip()).strip("._-")
        return normalized or "song-ai-final-mix"
