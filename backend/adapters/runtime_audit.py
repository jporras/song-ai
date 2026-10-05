import ast
from datetime import datetime, timezone
from importlib import metadata
from pathlib import Path
import shutil
import sys
import platform
import hashlib
import json

from application.capability_registry import Capability, CapabilityRegistry
from config.model_settings import LocalModelSettings
from adapters.ui_control_audit import audit_controls
from adapters.acestep_api_audit import audit_acestep_api
from adapters.parameter_audit import audit_parameters
from adapters.acestep_configuration_audit import audit_acestep_configuration
from adapters.acestep_task_audit import wrapper_tasks


class RuntimeAudit:
    """Inspects metadata and source without importing engines or executing commands."""

    def __init__(self, root: Path, settings: LocalModelSettings) -> None:
        self.root = root
        self.settings = settings

    def run(self) -> dict[str, object]:
        packages = {}
        for name in ("ace-step", "torch", "transformers", "soundfile", "fastapi"):
            try:
                packages[name] = metadata.version(name)
            except metadata.PackageNotFoundError:
                packages[name] = None
        wrapper = self.root / "tools" / "acestep_generate.py"
        wrapper_source = wrapper.read_text(encoding="utf-8") if wrapper.exists() else ""
        tree = ast.parse(wrapper_source)
        tasks = wrapper_tasks(tree)
        capabilities = [
            Capability("song.generate", "ace_step", bool(self.settings.full_song_command.strip()), None,
                       reason="Command configured does not prove package/API/checkpoint execution."),
            Capability("tempo.audio_stretch", "dsp", False, False, reason="No studio tempo tool implemented."),
            Capability("audio.export", "ffmpeg", True, bool(shutil.which("ffmpeg")),
                       reason="Executable presence only; audio integration not executed."),
        ]
        ffmpeg_path = shutil.which("ffmpeg")
        local_ffmpeg = self.root / "data" / "tools" / "ffmpeg" / "bin" / "ffmpeg.exe"
        ffmpeg_inventory = {
            "path_executable": ffmpeg_path,
            "project_executable": str(local_ffmpeg) if local_ffmpeg.is_file() else None,
            "launcher_adds_project_bin": True,
            "execution_verified": False,
        }
        if not ffmpeg_path and local_ffmpeg.is_file():
            capabilities[2] = Capability("audio.export", "ffmpeg", True, True,
                                         reason="Project executable present; launcher adds bin to PATH. Execution not verified.")
        for task in ("repaint", "cover", "extract", "lego", "complete"):
            capabilities.append(Capability(f"song.{task}", "ace_step", task in tasks, False,
                                           reason="Not exposed by current wrapper." if task not in tasks else "Runtime not verified."))
        for role, path in (("gemma", self.settings.gemma_gguf_path), ("qwen", self.settings.qwen_gguf_path)):
            capabilities.append(Capability(f"assistant.{role}", "llama.cpp", self.settings.llama_cpp_enabled,
                                           None, reason=f"Model file exists: {path.is_file()}; server not probed."))
        imports = {}
        consumers = []
        endpoints = []
        for source in sorted((self.root / "backend").rglob("*.py")):
            relative = source.relative_to(self.root).as_posix()
            source_tree = ast.parse(source.read_text(encoding="utf-8-sig"))
            modules = set()
            for node in ast.walk(source_tree):
                if isinstance(node, ast.ImportFrom):
                    modules.add("." * node.level + (node.module or ""))
                elif isinstance(node, ast.Import):
                    modules.update(alias.name for alias in node.names)
            imports[relative] = sorted(modules)
            if any("professional_song_service" in module for module in imports[relative]):
                consumers.append(relative)
            for node in ast.walk(source_tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    for decorator in node.decorator_list:
                        if (isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Attribute)
                                and decorator.func.attr in {"get", "post", "put", "patch", "delete"}
                                and decorator.args and isinstance(decorator.args[0], ast.Constant)):
                            endpoints.append({"method": decorator.func.attr.upper(), "path": decorator.args[0].value,
                                              "handler": node.name, "source": relative})
        checkpoints = []
        music_root = self.root / "data" / "models" / "music"
        if music_root.exists():
            for directory in sorted(path for path in music_root.iterdir() if path.is_dir()):
                configs = []
                for config in sorted(directory.rglob("config.json")):
                    configs.append({"path": str(config.relative_to(self.root)),
                                    "sha256": hashlib.sha256(config.read_bytes()).hexdigest()})
                checkpoints.append({"path": str(directory.relative_to(self.root)), "configs": configs,
                                    "loaded_verified": False})
        historical_runs = []
        for directory_name in ("projects", "diagnostics"):
            for diagnostic in sorted((self.root / "data" / directory_name).rglob("*diagnostics.json")):
                try:
                    payload = json.loads(diagnostic.read_text(encoding="utf-8"))
                    runtime = payload.get("runtime", {})
                    historical_runs.append({
                        "source": str(diagnostic.relative_to(self.root)),
                        "created_at": payload.get("created_at"), "status": payload.get("status"),
                        "checkpoint_path": payload.get("model", {}).get("checkpoint_path"),
                        "config_path": runtime.get("ace_step_init", {}).get("config_path"),
                        "active_device": runtime.get("active_device"),
                        "current_execution_verified": False,
                    })
                except (OSError, ValueError, AttributeError):
                    historical_runs.append({"source": str(diagnostic.relative_to(self.root)), "status": "unreadable"})
        return {
            "schema_version": "1.0", "audit_type": "static_and_package_metadata",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "limitations": ["No engine import, server probe, generation, model download or audio evaluation.",
                            "Checkpoint defaults are not evidence of the loaded model.",
                            "Package metadata describes the Python interpreter running this audit."],
            "packages": packages, "exposed_wrapper_tasks": tasks,
            "ace_step_api_contract": audit_acestep_api(self.root),
            "ace_step_configuration": audit_acestep_configuration(self.root),
            "interpreter": {"executable": sys.executable, "version": platform.python_version()},
            "ui_controls": audit_controls(self.root),
            "parameter_trace_candidates": audit_parameters(self.root),
            "checkpoint_inventory": checkpoints,
            "historical_diagnostics": historical_runs,
            "ffmpeg_inventory": ffmpeg_inventory,
            "configured_models": {
                "gemma": {"file": str(self.settings.gemma_gguf_path), "exists": self.settings.gemma_gguf_path.is_file()},
                "qwen": {"file": str(self.settings.qwen_gguf_path), "exists": self.settings.qwen_gguf_path.is_file()},
                "ace_step": {"loaded_model": None, "reason": "Requires runtime evidence; not inferred from wrapper defaults."},
            },
            "capabilities": CapabilityRegistry(capabilities).snapshot(),
            "professional_service_consumers": consumers,
            "endpoints": endpoints, "imports": imports,
        }
