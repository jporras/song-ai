"""Local production commands; derived compatibility assets are not ACE-Step requirements."""
from models.song_workflow import SongPhase, SongPhaseStatus


class GenerateLocalInstrumental:
    def __init__(self, context, instrumental_generation_service):
        self.context, self.storage = context, context.storage
        self.instrumental_generation_service = instrumental_generation_service

    def execute(self, song_id: str) -> dict[str, object]:
        project = self.storage.get_song_project(song_id)
        if project is None:
            raise ValueError("Proyecto profesional no encontrado.")
        project = self.context.require_project(project)
        self.context.require_project(project)
        music_plan = self.context.artifacts.get(song_id, 'music_plan')["music_plan"]
        midi = self.context.artifacts.get(song_id, 'midi')
        active_model = "musicgen" if self.instrumental_generation_service.command_template else "local-procedural"
        self.storage.create_song_event(
            song_id=song_id,
            phase=SongPhase.INSTRUMENTAL_GENERATION.value,
            status=SongPhaseStatus.RUNNING.value,
            progress=45,
            message="Generando instrumental desde music_plan.json y song_base.mid.",
            active_model=active_model,
            payload={
                "music_plan": str(self.storage.data_dir / "projects" / song_id / "music_plan.json"),
                "midi": str(midi["midi"]),
            },
        )
        result = self.instrumental_generation_service.generate(song_id, dict(music_plan), str(midi["midi"]))
        result["progress"] = self.context.progress_for(result["project"])
        return result



class GenerateLocalVocals:
    def __init__(self, context, vocal_synthesis_service):
        self.context, self.storage = context, context.storage
        self.vocal_synthesis_service = vocal_synthesis_service

    def execute(self, song_id: str) -> dict[str, object]:
        project = self.storage.get_song_project(song_id)
        if project is None:
            raise ValueError("Proyecto profesional no encontrado.")
        project = self.context.require_project(project)
        self.context.require_project(project)
        spec_record = project.get("spec")
        if not spec_record:
            raise ValueError("La especificacion debe existir antes de generar voz.")
        lyrics_approved_path = self.storage.data_dir / "projects" / song_id / "lyrics_approved.json"
        if not lyrics_approved_path.exists():
            raise ValueError("La letra aprobada debe existir antes de generar voz.")
        lyrics_approved = self.storage.read_json(lyrics_approved_path)
        midi = self.context.artifacts.get(song_id, 'midi')
        self.context.artifacts.get(song_id, 'instrumental')
        active_model = "singing-voice-provider" if self.vocal_synthesis_service.command_template else "local-vocal-guide"
        self.storage.create_song_event(
            song_id=song_id,
            phase=SongPhase.VOCAL_SYNTHESIS.value,
            status=SongPhaseStatus.RUNNING.value,
            progress=45,
            message="Generando voz cantada/guia desde lyrics_approved.json y melodia vocal MIDI.",
            active_model=active_model,
            payload={"lyrics_approved": str(lyrics_approved_path), "midi_metadata": str(self.storage.data_dir / "projects" / song_id / "midi_metadata.json")},
        )
        spec = dict(dict(spec_record).get("json_spec", {}))
        try:
            result = self.vocal_synthesis_service.generate(
                song_id,
                lyrics_approved,
                dict(midi["metadata"]),
                str(spec.get("voice_style", "soft vocal")),
            )
        except Exception as exc:
            self.storage.create_song_event(
                song_id=song_id,
                phase=SongPhase.VOCAL_SYNTHESIS.value,
                status=SongPhaseStatus.FAILED.value,
                progress=100,
                message=f"La generacion de voz fallo: {exc}",
                active_model=active_model,
                payload={"error": str(exc)},
            )
            self.storage.update_song_project_phase(
                song_id,
                SongPhase.VOCAL_SYNTHESIS.value,
                SongPhaseStatus.FAILED.value,
            )
            raise
        result["progress"] = self.context.progress_for(result["project"])
        return result



class ConvertLocalVoice:
    def __init__(self, context, voice_conversion_service):
        self.context, self.storage = context, context.storage
        self.voice_conversion_service = voice_conversion_service

    def execute(self, song_id: str) -> dict[str, object]:
        project = self.storage.get_song_project(song_id)
        if project is None:
            raise ValueError("Proyecto profesional no encontrado.")
        project = self.context.require_project(project)
        self.context.require_project(project)
        spec_record = project.get("spec")
        if not spec_record:
            raise ValueError("La especificacion debe existir antes de convertir voz.")
        self.context.artifacts.get(song_id, 'vocals')
        spec = dict(dict(spec_record).get("json_spec", {}))
        active_model = "rvc-or-compatible" if self.voice_conversion_service.command_template else "none"
        self.storage.create_song_event(
            song_id=song_id,
            phase=SongPhase.VOICE_CONVERSION.value,
            status=SongPhaseStatus.RUNNING.value if self.voice_conversion_service.command_template else SongPhaseStatus.SKIPPED.value,
            progress=50,
            message="Evaluando conversion de voz opcional.",
            active_model=active_model,
            payload={"voice_style": str(spec.get("voice_style", ""))},
        )
        result = self.voice_conversion_service.run(song_id, str(spec.get("voice_style", "soft vocal")))
        result["progress"] = self.context.progress_for(result["project"])
        return result
