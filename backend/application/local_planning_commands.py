"""Local production commands; derived compatibility assets are not ACE-Step requirements."""
from models.song_workflow import SongPhase, SongPhaseStatus


class GenerateLocalMusicPlan:
    def __init__(self, context, music_plan_service):
        self.context, self.storage = context, context.storage
        self.music_plan_service = music_plan_service

    def execute(self, song_id: str) -> dict[str, object]:
        project = self.storage.get_song_project(song_id)
        if project is None:
            raise ValueError("Proyecto profesional no encontrado.")
        project = self.context.require_project(project)
        self.context.require_project(project)
        spec_record = project.get("spec")
        if not spec_record or not bool(dict(spec_record).get("approved_by_qwen")):
            raise ValueError("La especificacion debe estar aprobada antes de generar el plan musical.")
        lyrics_approved_path = self.storage.data_dir / "projects" / song_id / "lyrics_approved.json"
        if not lyrics_approved_path.exists():
            raise ValueError("La letra debe estar aprobada por el director tecnico antes de generar el plan musical.")
        lyrics_approved = self.storage.read_json(lyrics_approved_path)
        if not bool(lyrics_approved.get("approved_by_qwen")):
            raise ValueError("La letra aprobada no esta disponible; revisa la fase LYRICS_TECHNICAL_REVIEW.")

        self.storage.create_song_event(
            song_id=song_id,
            phase=SongPhase.MUSIC_PLAN_GENERATION.value,
            status=SongPhaseStatus.RUNNING.value,
            progress=40,
            message="Creando plan musical derivado de compatibilidad mediante reglas; no es inferencia Qwen.",
            active_model="deterministic-compatibility-planning",
            payload={"lyrics_approved": str(lyrics_approved_path)},
        )
        result = self.music_plan_service.generate(
            song_id,
            dict(dict(spec_record).get("json_spec", {})),
            lyrics_approved,
        )
        result["progress"] = self.context.progress_for(result["project"])
        return result



class GenerateLocalMidi:
    def __init__(self, context, midi_generation_service):
        self.context, self.storage = context, context.storage
        self.midi_generation_service = midi_generation_service

    def execute(self, song_id: str) -> dict[str, object]:
        project = self.storage.get_song_project(song_id)
        if project is None:
            raise ValueError("Proyecto profesional no encontrado.")
        project = self.context.require_project(project)
        self.context.require_project(project)
        music_plan = self.context.artifacts.get(song_id, 'music_plan')["music_plan"]
        self.storage.create_song_event(
            song_id=song_id,
            phase=SongPhase.MIDI_GENERATION.value,
            status=SongPhaseStatus.RUNNING.value,
            progress=45,
            message="Creando MIDI de compatibilidad mediante reglas; no es un requisito de ACE-Step.",
            active_model="deterministic-compatibility-planning",
            payload={"music_plan": str(self.storage.data_dir / "projects" / song_id / "music_plan.json")},
        )
        result = self.midi_generation_service.generate(song_id, dict(music_plan))
        result["progress"] = self.context.progress_for(result["project"])
        return result
