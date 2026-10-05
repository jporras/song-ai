"""Inspect wrapper configuration defaults without importing the audio engine."""
import ast
from pathlib import Path


def audit_acestep_configuration(root: Path) -> dict[str, object]:
    source = root / "tools" / "acestep_generate.py"
    if not source.is_file():
        return {"status": "wrapper_missing", "loaded_verified": False}
    tree = ast.parse(source.read_text(encoding="utf-8-sig"))
    options = {}
    for node in ast.walk(tree):
        if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                and node.func.attr == "add_argument" and node.args
                and isinstance(node.args[0], ast.Constant)
                and node.args[0].value in {"--config-path", "--checkpoint-path", "--device"}):
            continue
        default = next((item.value for item in node.keywords if item.arg == "default"), None)
        options[node.args[0].value] = ast.unparse(default) if default is not None else None
    resolver = next((node for node in tree.body if isinstance(node, ast.FunctionDef)
                     and node.name == "resolve_acestep_v15_config_path"), None)
    candidates = sorted({node.value.value for node in ast.walk(resolver)
                         if isinstance(node, ast.Return) and isinstance(node.value, ast.Constant)
                         and isinstance(node.value.value, str)}) if resolver else []
    return {"status": "source_inspected", "argument_default_expressions": options,
            "resolver_config_candidates": candidates,
            "effective_config": None, "effective_checkpoint": None, "loaded_verified": False,
            "limitations": ["Defaults and resolver branches are source evidence only.",
                            "Command overrides, environment and loaded checkpoint require per-run diagnostics."]}
