"""Configuration correspondence is evidence, not audible quality certification."""
from application.runtime_correspondence import RuntimeCorrespondence


class SampleRepresentativity:
    def build(self, sample: dict, current_plan: dict | None, fingerprint: str, evidence: dict, signal_metrics: dict | None = None) -> dict:
        plan = (current_plan or {}).get("plan", {})
        checks = []
        for key, label, expected, observed in (
            ("set", "Datos del set", fingerprint, sample.get("set_fingerprint")),
            ("plan", "Plan aprobado", (current_plan or {}).get("plan_id"), sample.get("plan_id")),
            ("plan_hash", "Entradas de generacion", plan.get("plan_sha256"), sample.get("plan_sha256")),
            ("revision", "Revision de la ficha", plan.get("spec_revision_id"), sample.get("spec_revision_id")),
            ("configuration", "Configuracion del motor", plan.get("retained_spec", {}).get("ace_step_config"), sample.get("provider_config")),
            ("mode", "Modo de creacion", plan.get("payload", {}).get("task_type"), sample.get("task_type")),
            ("audio", "Audio registrado", sample.get("audio_evidence", {}).get("sha256"), evidence.get("sha256")),
        ):
            checks.append({"id": key, "label": label, "status": "matches" if expected is not None and expected == observed else "mismatch",
                           "expected": expected, "observed": observed, "method": "persisted_inputs_comparison"})
        checks.append({"id": "plan_current", "label": "Plan vigente y aprobado", "status": "matches" if current_plan and current_plan.get("inputs_current") is True and current_plan.get("effective_status") == "approved" else "mismatch"})
        configuration_matches = all(c["status"] == "matches" for c in checks)
        for key, label in (("runtime", "Ejecucion real y configuracion efectiva"), ("voice", "Voz y canto representativos"),
                           ("listening", "Calidad y fidelidad por escucha")):
            checks.append({"id": key, "label": label, "status": "pending", "method": "evidence_required"})
        runtime = sample.get("runtime_evidence", {})
        checks[-3]["observed"] = runtime
        checks[-3]["method"] = runtime.get("source", "evidence_required")
        correspondence = RuntimeCorrespondence().build(runtime, plan, evidence.get("sha256"))
        checks.extend(correspondence["checks"])
        return {"sample_id": sample["sample_id"], "audio_sha256": evidence.get("sha256"),
                "checks": checks, "configuration_matches": configuration_matches,
                "execution_configuration_matches": correspondence["matches"],
                "active_device": correspondence["active_device"], "fallback_reason": correspondence["fallback_reason"],
                "representativity_verified": False, "final_generation_ready": False,
                "sample_approval_status": sample.get("approval_status", "pending"),
                "signal_metrics": signal_metrics,
                "runtime_reported_completion": runtime.get("status") == "reported_completion" and runtime.get("audio_sha256") == evidence.get("sha256"),
                "note": "La coincidencia de datos no acredita la voz ni la calidad del audio. Evalúa las evidencias pendientes para acreditar la representatividad de este sample opcional; no es un requisito para generar la canción completa."}
