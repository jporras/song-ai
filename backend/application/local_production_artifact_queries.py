"""Read compatibility artifacts without constructing generation providers."""
from typing import Protocol
from pathlib import Path


class ArtifactQueryStore(Protocol):
    data_dir: Path
    def get_song_project(self, song_id): ...
    def read_json(self, path): ...


class LocalProductionArtifactQueries:
    AUDIO_FILES = {'instrumental':'instrumental.wav', 'vocals':'vocals.wav',
                   'vocals_converted':'vocals_converted.wav', 'mix':'mix.wav'}

    def __init__(self, storage: ArtifactQueryStore):
        self.storage = storage

    def get(self, song_id, kind):
        if self.storage.get_song_project(song_id) is None:
            raise ValueError('Proyecto no encontrado.')
        folder = (self.storage.data_dir / 'projects' / song_id).resolve()
        root = (self.storage.data_dir / 'projects').resolve()
        if root not in folder.parents:
            raise ValueError('La ruta del proyecto no es válida.')

        def required(filename):
            path = folder / filename
            if folder not in path.resolve().parents or not path.is_file():
                raise ValueError(f'Este proyecto aún no tiene un archivo disponible: {filename}.')
            return path

        if kind in self.AUDIO_FILES:
            path = required(self.AUDIO_FILES[kind])
            return {'song_id':song_id, kind:str(path), 'size_bytes':path.stat().st_size}
        if kind == 'music_plan':
            path = required('music_plan.json')
            return {'song_id':song_id, 'music_plan':self.storage.read_json(path), 'path':str(path)}
        if kind == 'midi':
            path, metadata = required('song_base.mid'), required('midi_metadata.json')
            return {'song_id':song_id, 'midi':str(path), 'metadata':self.storage.read_json(metadata)}
        if kind == 'master':
            paths = {format_:required(f'final_song.{format_}') for format_ in ('wav','mp3','flac')}
            return {'song_id':song_id,
                    **{f'final_{fmt}':str(path) for fmt,path in paths.items()},
                    **{f'{fmt}_size_bytes':path.stat().st_size for fmt,path in paths.items()}}
        raise ValueError('Tipo de artefacto no reconocido.')
