"""Compare installed Python source signatures without importing ACE-Step."""
import ast
from importlib import metadata
from pathlib import Path
import sys


def compare_signature(method: ast.FunctionDef, calls: list[ast.Call]) -> dict[str, object]:
    parameters = {item.arg for item in (*method.args.posonlyargs, *method.args.args, *method.args.kwonlyargs)} - {"self"}
    passed = {kw.arg for call in calls for kw in call.keywords if kw.arg}
    required = {item.arg for item in method.args.args[:len(method.args.args) - len(method.args.defaults)]} - {"self"}
    required.update(item.arg for item, default in zip(method.args.kwonlyargs, method.args.kw_defaults) if default is None)
    unsupported = sorted(passed - parameters) if method.args.kwarg is None else []
    missing = sorted(required - passed)
    return {"accepted_parameters": sorted(parameters), "wrapper_parameters": sorted(passed),
            "unsupported_keywords": unsupported, "missing_required": missing,
            "signature_compatible": not unsupported and not missing,
            "accepts_extra_kwargs": method.args.kwarg is not None,
            "execution_verified": False}


def audit_acestep_api(root: Path) -> dict[str, object]:
    package = Path(sys.prefix) / "Lib" / "site-packages" / "acestep"
    if not package.is_dir():
        try:
            package = Path(metadata.distribution("ace-step").locate_file("acestep"))
        except metadata.PackageNotFoundError:
            return {"status": "not_found", "execution_verified": False}
    if not package.is_dir():
        return {"status": "source_not_found", "execution_verified": False}
    wrapper = ast.parse((root / "tools" / "acestep_generate.py").read_text(encoding="utf-8-sig"))
    methods = {}
    for name in ("generate_music", "initialize_service"):
        calls = [node for node in ast.walk(wrapper) if isinstance(node, ast.Call)
                 and isinstance(node.func, ast.Attribute) and node.func.attr == name]
        definitions = []
        source_root = package / "core" / "generation" / "handler"
        for source in sorted(source_root.rglob("*.py")):
            if source.name.endswith("_test.py"):
                continue
            tree = ast.parse(source.read_text(encoding="utf-8-sig"))
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    for method in node.body:
                        if isinstance(method, ast.FunctionDef) and method.name == name:
                            definitions.append((source, node.name, method))
        if len(definitions) != 1:
            methods[name] = {"status": "unknown", "candidate_count": len(definitions),
                             "reason": "Unique method definition not found."}
        else:
            source, class_name, method = definitions[0]
            methods[name] = {"source": str(source), "class": class_name,
                             "definition_line": method.lineno,
                             "status": "static_signature_only", **compare_signature(method, calls)}
    return {"status": "source_inspected", "package_source": str(package), "methods": methods,
            "execution_verified": False,
            "limitations": ["Static signatures do not prove import, mixin resolution, checkpoint compatibility or execution."]}
