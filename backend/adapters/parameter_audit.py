"""Find candidate parameter consumers; occurrences do not prove data flow."""
import ast
import re
from pathlib import Path

from adapters.ui_control_audit import audit_controls


def audit_parameters(root: Path) -> list[dict[str, object]]:
    references: dict[str, list[dict[str, object]]] = {}
    application = root / "backend" / "application"
    for source in sorted(application.glob("*.py")):
        if source.name in {"song_service.py", "capability_registry.py", "song_specification_service.py"}:
            continue
        tree = ast.parse(source.read_text(encoding="utf-8-sig"))
        for node in ast.walk(tree):
            key = None
            if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                    and node.func.attr == "get" and node.args and isinstance(node.args[0], ast.Constant)):
                key = node.args[0].value
            elif isinstance(node, ast.Subscript) and isinstance(node.slice, ast.Constant):
                key = node.slice.value
            if isinstance(key, str):
                references.setdefault(key, []).append({
                    "source": source.relative_to(root).as_posix(), "line": node.lineno,
                    "evidence": "dictionary_key_read", "data_flow_verified": False,
                })
    result = []
    for control in audit_controls(root):
        for binding, expression in control["bindings"].items():
            if not binding.startswith("v-model") or not expression:
                continue
            if not re.fullmatch(r"[A-Za-z_][\w]*(?:\.[A-Za-z_][\w]*)+", expression):
                result.append({"control": expression, "line": control["line"],
                               "status": "dynamic_expression", "candidate_consumers": []})
                continue
            key = expression.rsplit(".", 1)[1]
            result.append({
                "control": expression, "line": control["line"], "field": key,
                "status": "candidate_reads" if references.get(key) else "no_direct_read_found",
                "candidate_consumers": references.get(key, []),
                "audio_effect_verified": False,
                "reason": "Static key matching cannot establish aliasing, dynamic reads or audible effect.",
            })
    return result
