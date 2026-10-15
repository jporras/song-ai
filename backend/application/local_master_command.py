"""Local production commands; derived compatibility assets are not ACE-Step requirements."""
from models.song_workflow import SongPhase, SongPhaseStatus


class MasterLocalSong:
    def __init__(self, context, full_song_service, mixing_service, mastering_service):
        self.context, self.storage = context, context.storage
        self.full_song_service = full_song_service
        self.mixing_service = mixing_service
        self.mastering_service = mastering_service

    def execute(self, song_id: str, generation_profile: str | None = None) -> dict[str, object]:
        project = self.storage.get_song_project(song_id)
        if project is None:
            raise ValueError("Proyecto profesional no encontrado.")
        project = self.context.prepare_final_project(project)
        self.context.require_project(project)
        self.context.require_sample(project)
        if self.full_song_service.configured():
            active_model = "local-full-song-provider"
            self.storage.update_song_project_phase(song_id, SongPhase.MASTERING.value, SongPhaseStatus.RUNNING.value)
            self.storage.create_song_event(
                song_id=song_id,
                phase=SongPhase.MASTERING.value,
                status=SongPhaseStatus.RUNNING.value,
                progress=35,
                message="Generando cancion final completa con provider local full-song.",
                active_model=active_model,
                payload={},
            )
            try:
                result = self.full_song_service.generate(song_id, generation_profile=generation_profile)
            except Exception as exc:
                self.storage.create_song_event(
                    song_id=song_id,
                    phase=SongPhase.MASTERING.value,
                    status=SongPhaseStatus.FAILED.value,
                    progress=100,
                    message=f"La generacion full-song fallo: {exc}",
                    active_model=active_model,
                    payload={"error": str(exc)},
                )
                self.storage.update_song_project_phase(
                    song_id,
                    SongPhase.MASTERING.value,
                    SongPhaseStatus.FAILED.value,
                )
                raise
            result["progress"] = self.context.progress_for(result["project"])
            return result
        self.context.artifacts.get(song_id, 'mix')
        active_model = "local-mastering"
        self.storage.update_song_project_phase(song_id, SongPhase.MASTERING.value, SongPhaseStatus.RUNNING.value)
        self.storage.create_song_event(
            song_id=song_id,
            phase=SongPhase.MASTERING.value,
            status=SongPhaseStatus.RUNNING.value,
            progress=45,
            message="Masterizando mix.wav y preparando final_song.wav/final_song.mp3.",
            active_model=active_model,
            payload={},
        )
        try:
            result = self.mastering_service.master(song_id)
        except Exception as exc:
            self.storage.create_song_event(
                song_id=song_id,
                phase=SongPhase.MASTERING.value,
                status=SongPhaseStatus.FAILED.value,
                progress=100,
                message=f"Mastering fallo: {exc}",
                active_model=active_model,
                payload={"error": str(exc)},
            )
            self.storage.update_song_project_phase(song_id, SongPhase.MASTERING.value, SongPhaseStatus.FAILED.value)
            raise
        result["progress"] = self.context.progress_for(result["project"])
        return result
