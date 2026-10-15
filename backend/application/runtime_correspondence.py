"""Compare persisted wrapper observations with the current execution profile."""
from audio.ace_step_profiles import BASE_PROFILE, TURBO_PROFILE


class RuntimeCorrespondence:
    def build(self, runtime: dict, plan: dict, audio_sha256: str | None) -> dict:
        config = plan.get("retained_spec", {}).get("ace_step_config")
        profile = {BASE_PROFILE.config_path: BASE_PROFILE, TURBO_PROFILE.config_path: TURBO_PROFILE}.get(config)
        reported = runtime.get("status") == "reported_completion" and runtime.get("source") == "wrapper_diagnostics"
        checks = []
        for key, label, expected, observed in (
            ("runtime_audio", "Audio de la ejecucion reportada", audio_sha256, runtime.get("audio_sha256")),
            ("runtime_config", "Modelo inicializado", config, runtime.get("reported_config")),
            ("runtime_task", "Modo reportado por el motor", plan.get("payload", {}).get("task_type"), runtime.get("task_type")),
            ("runtime_steps", "Pasos de inferencia reportados", plan.get("payload", {}).get("inference_steps", profile.infer_steps if profile else None), runtime.get("infer_steps")),
        ):
            status = "pending" if not reported or expected is None or observed is None else "matches" if type(expected) is type(observed) and expected == observed else "mismatch"
            checks.append({"id": key, "label": label, "expected": expected, "observed": observed,
                           "status": status, "method": "wrapper_report_comparison"})
        requested_api = plan.get("payload", {}).get("generation_api")
        if requested_api:
            observation = runtime.get("generation_api", {})
            for key, expected, observed in (
                ("runtime_api", requested_api, observation.get("api")),
                ("runtime_lm", requested_api == "high_level_lm", observation.get("lm_used")),
            ):
                status = "pending" if not reported or observed is None else "matches" if type(expected) is type(observed) and expected == observed else "mismatch"
                checks.append({"id": key, "label": key, "expected": expected, "observed": observed,
                               "status": status, "method": "wrapper_report_comparison"})
        return {"checks": checks, "matches": all(c["status"] == "matches" for c in checks),
                "active_device": runtime.get("active_device"), "fallback_reason": runtime.get("fallback_reason", ""),
                "quality_verified": False}
