"""Compile a candidate handler payload from a confirmed SQLite specification."""
from copy import deepcopy
import hashlib
import json
import math
import re
from typing import Protocol
from models.ace_step_generation_options import generation_options
from models.ace_step_tasks import validate_task_inputs, validate_source_interval
from models.ace_step_input_trace import CAPTION_FIELDS, input_trace, record_verified_audio
from models.ace_step_capability_profile import CONNECTED_PROFILE
from application.lyric_section_direction import section_direction_trace


class SongPlanStore(Protocol):
    def get_song_project(self, song_id: str) -> dict | None: ...
    def get_indexed_set(self, set_id: str) -> dict | None: ...
    def set_generation_fingerprint(self, set_id: str) -> str: ...


class SourceAudioInspector(Protocol):
    def inspect(self, project: dict, artifact_id: str, requested_path: str) -> dict: ...


class AceStepPlanCompiler:
    LANGUAGES = {"spanish": "es", "espanol": "es", "español": "es", "english": "en",
                 "french": "fr", "frances": "fr", "portuguese": "pt", "portugues": "pt"}
    SIGNATURES = {"2/4": "2", "3/4": "3", "4/4": "4", "6/8": "6"}

    def compile(self, record: dict, lyrics: str) -> dict:
        revision = record.get("revision", {})
        if revision.get("user_confirmation_status") != "confirmed" or not revision.get("revision_id"):
            raise ValueError("Confirma la revision de la ficha antes de preparar el plan ACE-Step.")
        if revision.get("deterministic_valid") is not True or record.get("missing_fields"):
            raise ValueError("La ficha tiene datos pendientes; corrige y confirma una revision valida.")
        if not isinstance(record.get("json_spec"), dict):
            raise ValueError("La ficha confirmada no contiene una especificacion valida.")
        spec = deepcopy(record["json_spec"])
        if spec.get('_lyrics_document') and lyrics != spec['_lyrics_document'].get('markdown'):
            raise ValueError('La letra no coincide con MusicSpec. Guarda y confirma su nueva revisión antes de preparar el plan.')
        task = str(spec.get("task_type", "text2music"))
        tracks = spec.get("target_tracks", [])
        if not isinstance(tracks, list) or any(not isinstance(track, str) for track in tracks):
            raise ValueError("Las pistas objetivo deben ser una lista de nombres admitidos.")
        start, end = spec.get("repainting_start", 0), spec.get("repainting_end", -1)
        if not isinstance(start, (int, float)) or not isinstance(end, (int, float)):
            raise ValueError("El intervalo de edicion debe expresarse en segundos numericos.")
        source = str(spec.get("src_audio", ""))
        instruction = str(spec.get("instruction", ""))
        validate_task_inputs(task, str(spec.get("ace_step_config", "")), source, instruction,
                             start, end, tuple(tracks))
        bpm = self._number(spec.get("bpm"), "BPM", 30, 300)
        if not bpm.is_integer():
            raise ValueError("ACE-Step requiere BPM entero; revisa la propuesta sin redondear silenciosamente.")
        duration = self._number(spec.get("duration_seconds"), "duracion", 10, 600)
        language = str(spec.get("language", "")).strip().lower()
        language = self.LANGUAGES.get(language, language)
        if not re.fullmatch(r"[a-z]{2}", language):
            raise ValueError("Selecciona un codigo de idioma vocal de dos letras, por ejemplo es.")
        key = str(spec.get("key", "")).strip()
        if not re.fullmatch(r"[A-Ga-g][#b]?(?:\s+(?:major|minor)|m)?", key, re.IGNORECASE):
            raise ValueError("Revisa la tonalidad para ACE-Step, por ejemplo C Major o Am.")
        signature = str(spec.get("time_signature") or "4/4").strip()
        signature = self.SIGNATURES.get(signature, signature)
        if signature not in {"2", "3", "4", "6"}:
            raise ValueError("El compas solicitado no tiene mapeo validado a ACE-Step; conserva el requisito y revisa la ruta.")
        instruments = spec.get("instruments", [])
        instruments = ", ".join(map(str, instruments)) if isinstance(instruments, list) else str(instruments)
        caption = "; ".join(str(value).strip() for value in
                            (instruments if field == "instruments" else spec.get(field)
                             for field in CAPTION_FIELDS) if value)
        if not caption or len(caption) > 512:
            raise ValueError("La descripcion musical debe ocupar 1 a 512 caracteres; revisala sin omitir requisitos.")
        if not isinstance(lyrics, str) or (task != "extract" and not lyrics.strip()) or len(lyrics) > 4096:
            raise ValueError("La letra candidata debe ocupar 1 a 4096 caracteres; no se truncara.")
        payload = {"task_type": task, "captions": caption, "lyrics": lyrics,
                   "bpm": int(bpm), "key_scale": key, "time_signature": signature,
                   "vocal_language": language, "audio_duration": duration}
        payload.update(generation_options(spec))
        if spec.get("reference_audio"):
            if not spec.get("reference_artifact_id"):
                raise ValueError("La referencia necesita un artefacto registrado del proyecto.")
            payload["reference_audio"] = spec["reference_audio"]
        if task != "text2music":
            payload["src_audio"] = source
        if instruction:
            payload["instruction"] = instruction
        if task in {"repaint", "lego"}:
            payload.update(repainting_start=start, repainting_end=end, chunk_mask_mode="explicit")
        if task == "cover":
            payload["audio_cover_strength"] = self._number(spec.get("audio_cover_strength", 1), "fuerza de conservacion", 0, 1)
        routes = {field: "retained_requirement_needs_evaluation_or_external_processor" for field in spec}
        for field in ("bpm", "key", "time_signature", "language", "duration_seconds"):
            if field in spec:
                routes[field] = "structured_handler_parameter"
        for field in ("task_type", "src_audio", "instruction", "repainting_start", "repainting_end", "audio_cover_strength"):
            if field in spec and field in payload:
                routes[field] = "structured_handler_parameter"
        for field in ("song_type", "emotion", "instruments", "voice_style", "vocal_expression", "dynamic_arc", "groove", "vocal_range", "mix_balance"):
            if field in spec:
                routes[field] = "caption_conditioning_not_guarantee"
        result = {"schema_version": "1.0", "spec_revision_id": revision["revision_id"],
                  "payload": payload, "retained_spec": spec, "field_routes": routes,
                  "defaults": {"time_signature": "4/4"} if not spec.get("time_signature") else {},
                  "status": "candidate_plan", "ready_for_execution": False,
                  "lyrics_source": "confirmed_music_spec_document" if spec.get('_lyrics_document') else "preview_request_unconfirmed",
                  "pending": ["lyrics_confirmation", "effective_provider_configuration"],
                  "generation_verified": False, "lm_policy": "approved_inputs_no_rewrite",
                  "instrumental_control": "not_connected_boolean_keep_vocal_intent"}
        if task != "text2music":
            result["pending"].extend(["source_artifact_verification", "task_real_execution_validation"])
        result["input_trace"] = input_trace(spec, payload, revision["revision_id"])
        result['section_direction_trace'] = section_direction_trace(spec)
        contract = CONNECTED_PROFILE.public_contract()
        result["capability_profile"] = {"version": CONNECTED_PROFILE.version,
            "scope": contract["scope"],
            "sha256": hashlib.sha256(json.dumps(contract, sort_keys=True).encode()).hexdigest()}
        result["plan_sha256"] = hashlib.sha256(json.dumps(result, ensure_ascii=False, sort_keys=True).encode()).hexdigest()
        return result

    @staticmethod
    def _number(value, label: str, minimum: float, maximum: float) -> float:
        try:
            result = float(value) if not isinstance(value, bool) else float("nan")
        except (TypeError, ValueError):
            result = float("nan")
        if not math.isfinite(result) or not minimum <= result <= maximum:
            raise ValueError(f"Revisa {label}: ACE-Step documenta valores de {minimum} a {maximum}.")
        return result


class PreviewAceStepPlan:
    def __init__(self, store: SongPlanStore, source_audio: SourceAudioInspector | None = None):
        self.store = store
        self.source_audio = source_audio

    def execute(self, song_id: str, lyrics: str) -> dict:
        project = self.store.get_song_project(song_id)
        if project is None:
            raise ValueError("Proyecto no encontrado.")
        plan = AceStepPlanCompiler().compile(project.get("spec") or {}, lyrics)
        owner = str(project.get("user_id", ""))
        if owner.startswith("set:"):
            set_id = owner[4:].strip()
            if not set_id or self.store.get_indexed_set(set_id) is None:
                raise ValueError("El proyecto necesita un set valido antes de preparar el plan.")
            # A changed selection or asset content invalidates the exact approved plan.
            plan["set_context"] = {"set_id": set_id, "fingerprint": self.store.set_generation_fingerprint(set_id)}
        artifact_id = plan["retained_spec"].get("source_artifact_id")
        if plan["payload"]["task_type"] != "text2music" and artifact_id:
            if self.source_audio is None:
                raise ValueError("La verificacion de audio fuente no esta configurada.")
            evidence = self.source_audio.inspect(project, str(artifact_id), plan["payload"]["src_audio"])
            duration = evidence["duration_seconds"]
            if plan["payload"]["task_type"] in {"repaint", "lego"}:
                start, end = plan["payload"]["repainting_start"], plan["payload"]["repainting_end"]
                validate_source_interval(plan["payload"]["task_type"], start, end, duration)
            plan["source_audio_evidence"] = evidence
            record_verified_audio(plan["input_trace"], "src_audio", evidence)
            plan["pending"].remove("source_artifact_verification")
            plan["field_routes"]["source_artifact_id"] = "verified_project_audio_artifact"
            plan.pop("plan_sha256")
            plan["plan_sha256"] = hashlib.sha256(json.dumps(plan, ensure_ascii=False, sort_keys=True).encode()).hexdigest()
        if plan["payload"].get("reference_audio"):
            if self.source_audio is None:
                raise ValueError("La verificacion de referencia no esta configurada.")
            plan["reference_audio_evidence"] = self.source_audio.inspect(
                project, str(plan["retained_spec"]["reference_artifact_id"]), plan["payload"]["reference_audio"])
            record_verified_audio(plan["input_trace"], "reference_audio", plan["reference_audio_evidence"])
            plan["field_routes"]["reference_artifact_id"] = "verified_project_audio_artifact"
        for field in ("reference_audio", "seed", "inference_steps", "guidance_scale", "shift", "generation_api", "lm_model_path"):
            if field in plan["payload"]:
                plan["field_routes"][field] = "structured_handler_parameter"
        if "set_context" in plan or plan.get("reference_audio_evidence"):
            plan.pop("plan_sha256")
            plan["plan_sha256"] = hashlib.sha256(json.dumps(plan, ensure_ascii=False, sort_keys=True).encode()).hexdigest()
        return plan
