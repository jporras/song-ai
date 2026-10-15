"""Pure mapping evidence; no provider, model, filesystem or persistence access."""
from copy import deepcopy

CAPTION_FIELDS = ("song_type", "emotion", "instruments", "voice_style", "vocal_expression",
                  "dynamic_arc", "groove", "vocal_range", "mix_balance")
INPUT_SOURCES = {
    "bpm": "bpm", "key_scale": "key", "time_signature": "time_signature",
    "vocal_language": "language", "audio_duration": "duration_seconds",
    "task_type": "task_type", "generation_api": "generation_api", "lm_model_path": "lm_model_path",
    "seed": "seed", "inference_steps": "inference_steps", "guidance_scale": "guidance_scale",
    "shift": "shift", "reference_audio": "reference_audio", "src_audio": "src_audio",
    "instruction": "instruction", "repainting_start": "repainting_start",
    "repainting_end": "repainting_end", "audio_cover_strength": "audio_cover_strength",
    "chunk_mask_mode": None,
}


def record_verified_audio(trace: dict, target: str, evidence: dict) -> None:
    """Attach the inspector evidence to the exact artifact selected by USER."""
    entries = [entry for entry in trace.get("entries", []) if entry.get("target") == target]
    if len(entries) != 1 or target not in {"src_audio", "reference_audio"}:
        raise ValueError("La fuente verificada necesita una entrada única de trazabilidad.")
    entry = entries[0]
    if not evidence.get("sha256") or evidence.get("artifact_id") != entry.get("artifact_id"):
        raise ValueError("La evidencia de audio no corresponde al artefacto seleccionado.")
    entry.update(verification_status="verified_project_audio_artifact",
                 audio_sha256=evidence["sha256"], verified_file_path=evidence.get("file_path"))


def input_trace(spec: dict, payload: dict, revision_id: str) -> dict:
    """Fail closed when the compiler adds a payload input without a mapping rule."""
    unknown = set(payload) - set(INPUT_SOURCES) - {"captions", "lyrics"}
    if unknown:
        raise ValueError("Inputs ACE-Step sin regla de trazabilidad: " + ", ".join(sorted(unknown)))
    provenance = spec.get("_provenance", {})
    entries = []
    for target, after in payload.items():
        fields = CAPTION_FIELDS if target == "captions" else (
            (INPUT_SOURCES[target],) if INPUT_SOURCES.get(target) else ())
        sources = [{"field": field, "value": deepcopy(spec[field]),
                    "provenance": deepcopy(provenance.get(field, {}))}
                   for field in fields if field in spec]
        if target == "lyrics":
            document = spec.get('_lyrics_document')
            sources = [{"field": "_lyrics_document.markdown" if document else "lyrics_argument", "value": after,
                        "provenance": deepcopy(spec.get('_provenance', {}).get('lyrics', {})) if document
                                      else {"source": "preview_request_unconfirmed"}}]
        rule = ("caption_join" if target == "captions" else
                "lyrics_identity" if target == "lyrics" else
                "language_alias" if target == "vocal_language" else
                "signature_alias" if target == "time_signature" else
                "artifact_path" if target in {"reference_audio", "src_audio"} else
                "field_projection" if sources else "system_default")
        entry = {"target": target, "sources": sources, "result": deepcopy(after),
                 "rule": rule, "rule_version": "1.0", "spec_revision_id": revision_id}
        if target in {"reference_audio", "src_audio"}:
            artifact_field = "reference_artifact_id" if target == "reference_audio" else "source_artifact_id"
            entry["artifact_id"] = spec.get(artifact_field)
            entry["sources"] = [{"field": artifact_field, "value": spec.get(artifact_field),
                "provenance": deepcopy(provenance.get(artifact_field, {}))},
                {"field": target, "value": deepcopy(after),
                 "provenance": {"source": "system_artifact_resolution", "derived_from": artifact_field}}]
            entry["verification_status"] = "pending_preview_verification"
        entries.append(entry)
    return {"schema_version": "1.0", "spec_revision_id": revision_id,
            "scope": "compiler_mapping_not_audio_fidelity_or_user_approval", "entries": entries}
