"""Measured evidence and pending checks; no invented global fidelity score."""
import math


class CandidateFidelityReport:
    def build(self, plan: dict, evidence: dict) -> dict:
        payload = plan["payload"]
        target = payload.get("audio_duration")
        measured = evidence.get("duration_seconds")
        tolerance = plan.get("retained_spec", {}).get("duration_tolerance_seconds")
        valid_tolerance = (isinstance(tolerance, (int, float)) and not isinstance(tolerance, bool)
                           and math.isfinite(tolerance) and tolerance >= 0)
        valid_measurement = (isinstance(measured, (int, float)) and not isinstance(measured, bool)
                             and math.isfinite(measured) and measured > 0)
        valid_target = isinstance(target, (int, float)) and not isinstance(target, bool) and math.isfinite(target)
        delta = abs(measured - target) if valid_measurement and valid_target else None
        comparable = payload.get("task_type") == "text2music"
        verdict = "not_evaluated"
        if delta is not None and comparable:
            verdict = ("within_tolerance" if delta <= tolerance else "outside_tolerance") if valid_tolerance else "tolerance_pending"
        checks = [{"id": "duration", "label": "Duracion", "expected": target,
                   "observed": measured if valid_measurement else None, "unit": "seconds",
                   "absolute_difference": delta if comparable else None,
                   "tolerance": tolerance if valid_tolerance else None, "status": verdict,
                   "method": "wav_frames_sample_rate" if valid_measurement else "no_measurement",
                   "note": "En edicion se debe definir la duracion esperada de la salida por tarea." if not comparable else "La tolerancia debe provenir de la ficha aprobada."}]
        for key, label in (("bpm", "Velocidad"), ("key_scale", "Tonalidad"), ("lyrics", "Letra cantada"),
                           ("captions", "Estilo e instrumentacion")):
            checks.append({"id": key, "label": label, "expected": payload.get(key), "observed": None,
                           "status": "analysis_or_listening_pending", "method": "not_measured"})
        for key, label in (("voice_style", "Caracter de la voz"), ("structure", "Estructura"),
                           ("instruments", "Instrumentos"), ("required_phrases", "Frases obligatorias"),
                           ("excluded_content", "Contenido excluido")):
            checks.append({"id": key, "label": label, "expected": plan.get("retained_spec", {}).get(key),
                           "observed": None, "status": "analysis_or_listening_pending", "method": "not_measured"})
        task = payload.get("task_type")
        mode_checks = []
        if task == "cover":
            mode_checks = [("source_preservation", "Conservacion de la composicion fuente",
                            {"source_artifact_id": plan.get("retained_spec", {}).get("source_artifact_id"),
                             "requested_strength": payload.get("audio_cover_strength")})]
        elif task == "repaint":
            mode_checks = [("edited_interval", "Correccion del fragmento solicitado",
                            {"start": payload.get("repainting_start"), "end": payload.get("repainting_end")}),
                           ("exterior_preservation", "Conservacion del audio fuera del fragmento", "Revisar contra la fuente")]
        elif task in {"lego", "extract", "complete"}:
            mode_checks = [("target_tracks", "Pistas solicitadas", plan.get("retained_spec", {}).get("target_tracks", [])),
                           ("task_instruction", "Operacion solicitada", payload.get("instruction"))]
            if task == "extract":
                mode_checks.append(("extraction_leakage", "Fugas de otras pistas", "Revisar aislamiento contra la mezcla fuente"))
            else:
                mode_checks.append(("context_coherence", "Coherencia con el audio de contexto", "Revisar sincronizacion y arreglo con la fuente"))
        for key, label, expected in mode_checks:
            checks.append({"id": key, "label": label, "expected": expected, "observed": None,
                           "status": "analysis_or_listening_pending", "method": "not_measured"})
        return {"schema_version": "1.1", "task_type": task, "spec_revision_id": plan["spec_revision_id"],
                "plan_sha256": plan["plan_sha256"], "audio_sha256": evidence.get("sha256"),
                "checks": checks, "musical_acceptance": "pending_user_review", "final_quality_verified": False}
