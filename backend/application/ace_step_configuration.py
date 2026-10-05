"""Explicit edits of engine inputs on the existing specification revision."""
from copy import deepcopy
import math
from typing import Protocol

from application.song_specification_service import SongSpecificationService
from models.ace_step_tasks import TASKS, TRACKS, validate_task_inputs, validate_source_interval
from application.ace_step_plan_compiler import SourceAudioInspector


class EngineConfigurationStore(Protocol):
    def get_song_project(self, song_id: str) -> dict | None: ...
    def upsert_song_spec(self, **kwargs) -> dict: ...


class EditAceStepConfiguration:
    def __init__(self, store: EngineConfigurationStore, source_audio: SourceAudioInspector | None = None):
        self.store = store
        self.source_audio = source_audio

    def execute(self, song_id: str, request: dict) -> dict:
        project = self.store.get_song_project(song_id)
        if not project or not project.get("spec"):
            raise ValueError("Prepara la ficha del proyecto antes de configurar el audio.")
        record = project["spec"]
        revision = record.get("revision", {})
        expected = request.get("revision_id")
        if not expected or expected != revision.get("revision_id"):
            raise ValueError("La revision cambio. Recarga la ficha antes de guardar.")
        edits = request.get("values")
        editable = (set(SongSpecificationService.ENGINE_FIELDS) - {"src_audio"}) | SongSpecificationService.QUALITY_FIELDS
        if not isinstance(edits, dict) or not edits or set(edits) - editable:
            raise ValueError("Envia solo controles ACE-Step editables; la ruta se obtiene del artefacto.")
        spec = deepcopy(record["json_spec"])
        spec.update(edits)
        if "duration_tolerance_seconds" in edits:
            tolerance = edits["duration_tolerance_seconds"]
            if tolerance is None:
                spec.pop("duration_tolerance_seconds", None)
            elif (isinstance(tolerance, bool) or not isinstance(tolerance, (int, float))
                  or not math.isfinite(tolerance) or not 0 <= tolerance <= 600):
                raise ValueError("El margen de duracion debe ser un numero entre 0 y 600 segundos, o quedar sin definir.")
        task = spec.get("task_type", "text2music")
        if not isinstance(task, str) or task not in TASKS or spec.get("ace_step_config") not in ("acestep-v15-base", "acestep-v15-turbo"):
            raise ValueError("Selecciona una accion y un modelo ACE-Step admitidos.")
        if not isinstance(spec.get("instruction", ""), str):
            raise ValueError("La instruccion debe ser texto.")
        tracks = spec.get("target_tracks", [])
        if not isinstance(tracks, list) or any(not isinstance(track, str) or track not in TRACKS for track in tracks):
            raise ValueError("Selecciona pistas admitidas.")
        for key in ("repainting_start", "repainting_end", "audio_cover_strength"):
            if key in spec and (isinstance(spec[key], bool) or not isinstance(spec[key], (int, float)) or not math.isfinite(spec[key])):
                raise ValueError("Los intervalos y la conservacion deben ser numeros.")
        source_id = spec.get("source_artifact_id", "")
        if task != "text2music":
            sources = [item for item in project.get("artifacts", [])
                       if item.get("artifact_id") == source_id and item.get("song_id") == song_id]
            if len(sources) != 1:
                raise ValueError("Selecciona un audio registrado del proyecto activo.")
            spec["src_audio"] = sources[0]["file_path"]
        validate_task_inputs(task, spec["ace_step_config"], str(spec.get("src_audio", "")),
                             str(spec.get("instruction", "")), spec.get("repainting_start", 0),
                             spec.get("repainting_end", -1), tuple(tracks))
        strength = spec.get("audio_cover_strength", 1)
        if not 0 <= strength <= 1:
            raise ValueError("La conservacion debe estar entre 0 y 1.")
        if task != "text2music":
            if self.source_audio is None:
                raise ValueError("La verificacion de audio fuente no esta configurada.")
            evidence = self.source_audio.inspect(project, str(source_id), spec["src_audio"])
            validate_source_interval(task, spec.get("repainting_start", 0), spec.get("repainting_end", -1), evidence["duration_seconds"])
        provenance = spec.setdefault("_provenance", {})
        for key in edits:
            if spec.get(key) != record["json_spec"].get(key):
                provenance[key] = {"source": "explicit_user_control", "note": "Guardado por el usuario; revision pendiente de confirmar."}
        return self.store.upsert_song_spec(
            song_id=song_id, json_spec=spec,
            approved_by_qwen=revision.get("deterministic_valid") is True,
            missing_fields=record.get("missing_fields", []), schema_version="1.1",
            technical_review_mode="engine_inputs_deterministic_edit",
            user_confirmation_status="pending", expected_revision_id=expected)
