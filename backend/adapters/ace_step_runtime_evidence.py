"""Preserve wrapper observations; never infer audible quality from diagnostics."""
import hashlib
import json
from pathlib import Path
from adapters.ace_step_input_observation import inspect_input_observation


def read_candidate_runtime(directory: Path, output: Path, profile, plan=None) -> dict:
    path = directory / "ace_step_diagnostics.json"
    try:
        if not path.resolve().is_relative_to(directory.resolve()) or path.stat().st_size > 2_000_000:
            raise ValueError("Diagnostico fuera del directorio o demasiado grande.")
        raw = path.read_bytes()
        data = json.loads(raw)
        if not isinstance(data, dict) or data.get("schema") != "song-ai-ace-step-diagnostics-v1":
            raise ValueError("Formato de diagnostico no reconocido.")
        runtime, reported = data.get("runtime", {}), data.get("output", {})
        init = runtime.get("ace_step_init", {})
        completed = (data.get("status") == "completed" and init.get("enable_generate") is True
                     and reported.get("exists") is True and Path(reported.get("path", "")).resolve() == output.resolve()
                     and reported.get("size_bytes") == output.stat().st_size)
        return {"status": "reported_completion" if completed else "pending",
                "source": "wrapper_diagnostics", "diagnostics_sha256": hashlib.sha256(raw).hexdigest(),
                "audio_sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
                "requested_config": profile.config_path, "reported_config": init.get("config_path"),
                "configuration_matches": completed and init.get("config_path") == profile.config_path,
                "requested_device": runtime.get("requested_device"), "active_device": runtime.get("active_device"),
                "fallback_reason": runtime.get("fallback_reason", ""),
                "infer_steps": data.get("parameters", {}).get("infer_step"),
                "runtime_options_trace": data.get('runtime_options_trace'),
                "runtime_input_trace": data.get('runtime_input_trace'),
                "input_observation": inspect_input_observation(data.get('runtime_input_trace'), plan),
                "task_type": data.get("parameters", {}).get("task_type"),
                "generation_api": runtime.get("generation_api", {"api": data.get("parameters", {}).get("generation_api", "direct"), "lm_used": False}),
                "quality_verified": False}
    except (OSError, ValueError, TypeError, AttributeError) as error:
        return {"status": "pending", "source": "wrapper_diagnostics", "reason": str(error), "quality_verified": False}
