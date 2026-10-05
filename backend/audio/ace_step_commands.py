"""Keep historical wrapper templates compatible with explicit 1.5 profiles."""


def normalize_ace_step_template(template: str) -> str:
    if "tools/acestep_generate.py" not in template.replace("\\", "/"):
        return template
    updated = template.replace("data/models/music/acestep-1.5-{model_type}", "{checkpoint_root}")
    if "--config-path" not in updated:
        updated += " --config-path {config_path}"
    return updated
