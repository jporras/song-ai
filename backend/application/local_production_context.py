"""Persisted production guards shared by small local commands."""
import re
from application.music_spec_revision_service import require_confirmed_music_spec, MusicSpecRevisionService
from application.local_production_artifact_queries import LocalProductionArtifactQueries
from application.local_lyrics_access import LocalLyricsAccess
from application.music_spec_snapshot_export import export_music_spec
from application.final_production_gate import FinalProductionGate


class LocalProductionContext:
    def __init__(self, storage):
        self.storage = storage
        self.artifacts = LocalProductionArtifactQueries(storage)

    def require_project(self, project):
        require_confirmed_music_spec(project)
        return project

    def require_sample(self, project):
        return FinalProductionGate(self.storage).require_for_project(project)

    def progress_for(self, project):
        return MusicSpecRevisionService(self.storage).progress_for(project)

    def prepare_final_project(self, project):
        self.require_project(project)
        result = LocalLyricsAccess(self.storage).get(project['id'])
        text = result['markdown']
        if '# Letra mock' in text or 'Pendiente de completar' in text:
            raise ValueError('La letra final todavía apunta a un mock. Guarda la fase Letra antes de generar.')
        unresolved = sorted(set(re.findall(r'\{[^{}\n]+\}', text)))
        if unresolved:
            raise ValueError('La letra final contiene placeholders sin resolver: ' + ', '.join(unresolved))
        if result.get('active_music_spec_document'):
            export_music_spec(self.storage, project['id'])
        return project
