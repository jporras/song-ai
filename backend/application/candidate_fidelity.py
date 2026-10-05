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
        return {"schema_version": "1.0", "spec_revision_id": plan["spec_revision_id"],
                "plan_sha256": plan["plan_sha256"], "audio_sha256": evidence.get("sha256"),
                "checks": checks, "musical_acceptance": "pending_user_review", "final_quality_verified": False}
