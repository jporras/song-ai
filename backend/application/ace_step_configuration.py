"""Explicit edits of engine inputs on the existing specification revision."""
from copy import deepcopy
import math
from models.ace_step_generation_options import generation_options
from typing import Protocol

from application.song_specification_service import SongSpecificationService
from models.ace_step_tasks import TASKS, TRACKS, validate_task_inputs, validate_source_interval
from application.ace_step_plan_compiler import SourceAudioInspector


class EngineConfigurationStore(Protocol):
    def get_song_project(self, song_id: str) -> dict | None: ...
    def upsert_song_spec(self, **kwargs) -> dict: ...


class EditAceStepConfiguration:
    technical_review_mode = "engine_inputs_deterministic_edit"

    def editable_fields(self):
        return (set(SongSpecificationService.ENGINE_FIELDS) - {"src_audio", "reference_audio"}) | SongSpecificationService.QUALITY_FIELDS

    def validate_edits(self, edits: dict) -> None:
        pass

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
        editable = self.editable_fields()
        if not isinstance(edits, dict) or not edits or set(edits) - editable:
            raise ValueError("Envia solo controles ACE-Step editables; la ruta se obtiene del artefacto.")
        self.validate_edits(edits)
        spec = deepcopy(record["json_spec"])
        spec.update(edits)
        restored = revision.get('technical_review_mode') == 'restored_snapshot_requires_review'
        prepared = spec.get('_preparation', {}).get('requires_deterministic_review') is True
        if restored or prepared:
            self.validate_edits({key: value for key, value in spec.items() if key in editable})
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
        generation_options(spec)
        for key in ("seed", "inference_steps", "guidance_scale", "shift"):
            if spec.get(key) in (None, ""):
                spec.pop(key, None)
        reference_id = spec.get("reference_artifact_id")
        if reference_id:
            references = [item for item in project.get("artifacts", [])
                          if item.get("artifact_id") == reference_id and item.get("song_id") == song_id]
            if len(references) != 1 or self.source_audio is None:
                raise ValueError("Selecciona una referencia de audio del proyecto activo.")
            spec["reference_audio"] = references[0]["file_path"]
            self.source_audio.inspect(project, str(reference_id), spec["reference_audio"])
        else:
            spec.pop("reference_audio", None)
        provenance = spec.setdefault("_provenance", {})
        for key in edits:
            if key in {'seed','inference_steps','guidance_scale','shift'} and edits[key] in (None, ''):
                provenance[key] = {'source':'explicit_user_delegation', 'confirmation':'pending',
                    'delegated_to':'ace_step_profile', 'previous_value':deepcopy(record['json_spec'].get(key)),
                    'transformations':['omit_override_use_profile_v1'],
                    'note':'Delegación elegida al guardar; requiere confirmar la revisión y revisar el plan.'}
                spec.setdefault('_field_disposition', {})[key] = 'delegated_to_profile'
                continue
            previous = provenance.get(key, {})
            provenance[key] = {"source": "explicit_user_control",
                               "note": "Guardado por el usuario; revision pendiente de confirmar."}
            if previous.get('locked') is True:
                provenance[key]['locked'] = True
            if previous.get('source') and previous['source'] != 'explicit_user_control':
                provenance[key]['previous_source'] = previous['source']
            spec.get('_field_disposition', {}).pop(key, None)
        missing = [field for field in record.get('missing_fields', [])
                   if field not in edits or spec.get(field) in (None, '', [])]
        if prepared:
            from application.music_spec_edit import EditMusicSpec
            missing = sorted(field for field in EditMusicSpec.REQUIRED_FIELDS if spec.get(field) in (None,'',[]))
            spec['_preparation']['requires_deterministic_review'] = bool(missing)
        return self.store.upsert_song_spec(
            song_id=song_id, json_spec=spec,
            approved_by_qwen=False,
            deterministic_valid=(revision.get('deterministic_valid') is True or
                (prepared and not missing) or
                (restored and spec.get('_restoration', {}).get('source_deterministic_valid') is True
                 and not record.get('missing_fields'))),
            missing_fields=missing, schema_version="1.1",
            technical_review_mode=self.technical_review_mode,
            user_confirmation_status="pending", expected_revision_id=expected)
