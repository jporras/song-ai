"""Read-only project access; never seeds or rewrites the active definition."""
from typing import Protocol
from application.music_spec_revision_service import MusicSpecRevisionService
from models.song_workflow import PHASE_LABELS, PHASE_SEQUENCE


class ProjectQueryStore(Protocol):
    def get_song_project(self, song_id): ...
    def list_song_projects(self): ...
    def list_song_project_events(self, song_id): ...


class LocalProjectQueries:
    def __init__(self, storage: ProjectQueryStore):
        self.storage = storage

    def phases(self):
        return [{'number':index, 'total':len(PHASE_SEQUENCE), 'phase':phase.value,
                 'label':PHASE_LABELS[phase], 'required':phase.value != 'VOICE_CONVERSION'}
                for index, phase in enumerate(PHASE_SEQUENCE, start=1)]

    def list(self):
        return {'projects':[self.storage.get_song_project(str(item['id'])) or item
                            for item in self.storage.list_song_projects()], 'phases':self.phases()}

    def get(self, song_id):
        project = self.storage.get_song_project(song_id)
        if project is None:
            raise ValueError('Proyecto no encontrado.')
        return {'project':project, 'phases':self.phases(),
                'progress':MusicSpecRevisionService(self.storage).progress_for(project)}

    def events(self, song_id):
        self.get(song_id)
        return {'song_id':song_id, 'events':self.storage.list_song_project_events(song_id)}
