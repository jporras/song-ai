"""Register an original authorized WAV without changing creative specification."""
from pathlib import Path
from typing import Protocol, Callable
from uuid import uuid4

MAX_SOURCE_BYTES = 64 * 1024 * 1024


class SourceImportStore(Protocol):
    data_dir: Path
    def get_song_project(self, song_id: str) -> dict | None: ...
    def create_song_artifact(self, **kwargs) -> dict: ...


class ImportSourceAudio:
    def __init__(self, store: SourceImportStore, inspect: Callable):
        self.store, self.inspect = store, inspect

    def execute(self, song_id: str, filename: str, content: bytes, authorized: bool) -> dict:
        if not authorized:
            raise ValueError('Confirma que tienes permiso de usar este audio.')
        project = self.store.get_song_project(song_id)
        if not project:
            raise ValueError('Proyecto no encontrado.')
        original_name = Path(filename.replace('\\', '/')).name
        if not original_name.lower().endswith('.wav'):
            raise ValueError('Importa un WAV PCM. La conversión de otros formatos todavía no está disponible.')
        if not content or len(content) > MAX_SOURCE_BYTES:
            raise ValueError('El archivo debe tener contenido y no superar 64 MiB.')
        root = (self.store.data_dir / 'projects').resolve()
        directory = (root / song_id / 'sources').resolve()
        if root not in directory.parents:
            raise ValueError('Carpeta de proyecto no válida.')
        directory.mkdir(parents=True, exist_ok=True)
        artifact_id = 'source_' + uuid4().hex
        path = directory / (artifact_id + '.wav')
        try:
            with path.open('xb') as output:
                output.write(content)
            evidence = self.inspect(path, directory)
            return self.store.create_song_artifact(artifact_id=artifact_id, song_id=song_id,
                phase='SOURCE_IMPORT', artifact_type='source_audio', file_path=str(path),
                metadata={'original_filename': original_name, 'usage_authorized': True,
                          'source': 'user_upload', 'audio_evidence': evidence,
                          'technical_integrity_verified': True, 'musical_quality_verified': False})
        except Exception:
            path.unlink(missing_ok=True)
            raise
