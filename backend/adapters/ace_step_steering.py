"""Read a bounded documentation section and inspect the current wrapper, without engines."""
import ast
import hashlib
from importlib import metadata
import json
from pathlib import Path

from adapters.acestep_configuration_audit import audit_acestep_configuration
from adapters.acestep_task_audit import wrapper_tasks


class AceStepSteering:
    START = "<!-- MODEL_STEERING_START -->"
    END = "<!-- MODEL_STEERING_END -->"

    def __init__(self, root: Path):
        self.root = root

    def snapshot(self, role: str) -> dict[str, object]:
        if role not in {"gemma", "qwen"}:
            raise ValueError("Rol de steering desconocido.")
        document = self.root / "docs" / "ACE_STEP_CAPABILITIES.md"
        content = document.read_text(encoding="utf-8-sig")
        if content.count(self.START) != 1 or content.count(self.END) != 1:
            raise ValueError("El contrato ACE-Step necesita una unica seccion de steering.")
        start = content.index(self.START) + len(self.START)
        end = content.index(self.END)
        guidance = content[start:end].strip()
        if end <= start or not guidance or len(guidance) > 6500:
            raise ValueError("La seccion de steering ACE-Step es invalida o excede el presupuesto.")
        role_file = self.root / "docs" / "steering" / f"{role.upper()}_SONG_ROLE.md"
        role_guidance = role_file.read_text(encoding="utf-8-sig").strip()
        if not role_guidance or len(role_guidance) > 2500:
            raise ValueError("El steering de rol es invalido o excede el presupuesto.")
        wrapper_path = self.root / "tools" / "acestep_generate.py"
        wrapper_bytes = wrapper_path.read_bytes()
        tree = ast.parse(wrapper_bytes.decode("utf-8-sig"))
        calls = [node for node in ast.walk(tree) if isinstance(node, ast.Call)
                 and isinstance(node.func, ast.Attribute) and node.func.attr == "generate_music"]
        tasks = wrapper_tasks(tree)
        passed = sorted({kw.arg for call in calls for kw in call.keywords if kw.arg})
        music_root = self.root / "data" / "models" / "music"
        configs = list(music_root.rglob("config.json"))
        model_configs = {family: sorted(path.relative_to(self.root).as_posix() for path in configs
                        if path.parent.name in {f"acestep-v15-{family}", f"acestep-v15-xl-{family}"})
                         for family in ("base", "turbo")}
        try:
            version = metadata.version("ace-step")
        except metadata.PackageNotFoundError:
            version = None
        runtime = {"package_version": version, "integration": "handler.generate_music",
                   "model_config_inventory": model_configs,
                   "wrapper_tasks": tasks, "wrapper_keyword_arguments": passed,
                   "verified_tasks": [], "public_generation_task_selection": False,
                   "missing_structured_music_fields": sorted(set(("bpm", "key_scale", "time_signature", "vocal_language")) - set(passed)),
                   "configuration": audit_acestep_configuration(self.root),
                   "generation_verified": False, "quality_verified": False,
                   "end_to_end_spec_mapping_verified": False,
                   "evidence": "source_inspection_only"}
        evidence = {"document": "docs/ACE_STEP_CAPABILITIES.md", "document_sha256": hashlib.sha256(content.encode()).hexdigest(),
                    "role": role, "role_sha256": hashlib.sha256(role_guidance.encode()).hexdigest(),
                    "wrapper_sha256": hashlib.sha256(wrapper_bytes).hexdigest(), "runtime": runtime}
        revision = hashlib.sha256(json.dumps(evidence, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
        return {**evidence, "revision": revision,
                "prompt_context": f"{role_guidance}\n\n{guidance}\n\nEstado local observado (no prueba de audio):\n{json.dumps(runtime, ensure_ascii=False)}"}
