"""Local production commands; derived compatibility assets are not ACE-Step requirements."""
from models.song_workflow import SongPhase, SongPhaseStatus


class MixLocalSong:
    def __init__(self, context, mixing_service):
        self.context, self.storage = context, context.storage
        self.mixing_service = mixing_service

    def execute(self, song_id: str) -> dict[str, object]:
        project = self.storage.get_song_project(song_id)
        if project is None:
            raise ValueError("Proyecto profesional no encontrado.")
        project = self.context.require_project(project)
        self.context.require_project(project)
        self.context.artifacts.get(song_id, 'instrumental')
        try:
            self.context.artifacts.get(song_id, 'vocals_converted')
        except ValueError:
            self.context.artifacts.get(song_id, 'vocals')
        self.storage.create_song_event(
            song_id=song_id,
            phase=SongPhase.MIXING.value,
            status=SongPhaseStatus.RUNNING.value,
            progress=45,
            message="Mezclando instrumental y voz con ganancia, reverb suave y normalizacion.",
            active_model="local-mixer",
            payload={},
        )
        result = self.mixing_service.mix(song_id)
        result["progress"] = self.context.progress_for(result["project"])
        return result
