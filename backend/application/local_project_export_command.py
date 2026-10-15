"""Export an existing local production without historical project reseeding."""
from application.music_spec_revision_service import require_confirmed_music_spec
from application.local_production_artifact_queries import LocalProductionArtifactQueries
from application.final_production_gate import FinalProductionGate


class ExportLocalProject:
    def __init__(self, storage, exports):
        self.storage, self.exports = storage, exports

    def execute(self, song_id):
        project = self.storage.get_song_project(song_id)
        if project is None:
            raise ValueError('Proyecto no encontrado.')
        require_confirmed_music_spec(project)
        FinalProductionGate(self.storage).require_for_project(project)
        LocalProductionArtifactQueries(self.storage).get(song_id, 'master')
        self.storage.create_song_event(song_id=song_id, phase='EXPORT', status='running', progress=45,
            message='Preparando manifest de export y enlaces de descarga.', active_model='export-service', payload={})
        # Export service retains artifact checksums, quality and download rules.
        return self.exports.export(song_id)
