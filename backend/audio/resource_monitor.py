from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import shutil
import subprocess
import time
from uuid import uuid4

try:
    import psutil
except ImportError:  # pragma: no cover - mantiene importable el entorno si falta psutil.
    psutil = None

from config.resource_settings import ResourceMonitorSettings
from core.storage import StorageManager


HEAVY_PROCESS_NAMES = ("llama", "llama-server", "python", "torch", "uvicorn")


@dataclass(frozen=True)
class AudioReadiness:
    ready: bool
    decision: str
    message: str
    snapshot: dict[str, object]
    recommendations: list[str]


class ResourceMonitor:
    def __init__(
        self,
        storage: StorageManager,
        settings: ResourceMonitorSettings,
        data_path: Path | None = None,
        models_path: Path | None = None,
        cache_path: Path | None = None,
    ) -> None:
        self.storage = storage
        self.settings = settings
        self.data_path = data_path or storage.data_dir
        self.models_path = models_path or storage.data_dir / "models"
        self.cache_path = cache_path or storage.data_dir / "provider-cache"

    def status(self, phase: str = "status") -> dict[str, object]:
        snapshot = self.capture(phase=phase, persist=True)
        readiness = self.evaluate(snapshot)
        return {
            "enabled": self.settings.enabled,
            "settings": self.settings.to_dict(),
            "snapshot": snapshot,
            "readiness": self._readiness_dict(readiness),
        }

    def history(self, limit: int = 100) -> dict[str, object]:
        return {"snapshots": self.storage.list_resource_snapshots(limit)}

    def check_audio_readiness(self, phase: str = "before_audio") -> dict[str, object]:
        snapshot = self.capture(phase=phase, persist=True)
        readiness = self.evaluate(snapshot)
        return {"snapshot": snapshot, "readiness": self._readiness_dict(readiness)}

    def prepare_for_audio(self, phase: str, event_callback=None) -> dict[str, object]:
        if not self.settings.enabled:
            snapshot = self.capture(phase=phase, persist=True, decision="skipped", message="ResourceMonitor desactivado.")
            return {"snapshot": snapshot, "readiness": self._readiness_dict(self.evaluate(snapshot)), "released_llm": False}
        if psutil is None:
            snapshot = self.capture(phase=phase, persist=True, decision="skipped", message="ResourceMonitor omitido: psutil no esta instalado.")
            return {"snapshot": snapshot, "readiness": {"ready": True, "decision": "skipped_missing_psutil", "message": str(snapshot["message"]), "recommendations": []}, "released_llm": False}

        before = self.capture(phase="before_audio", persist=True)
        if self.settings.release_llm_before_audio:
            if event_callback is not None:
                event_callback("Liberando memoria: pausando modelos de texto antes de iniciar la generacion de audio.")
            if self.settings.stop_llm_command:
                subprocess.run(self.settings.stop_llm_command, shell=True, timeout=60, check=False)
            if self.settings.audio_start_delay_seconds > 0:
                time.sleep(self.settings.audio_start_delay_seconds)
        after = self.capture(phase="after_llm_release", persist=True)
        readiness = self.evaluate(after)
        return {"snapshot": after, "before": before, "readiness": self._readiness_dict(readiness), "released_llm": True}

    def restore_text_models(self, event_callback=None) -> None:
        if not self.settings.enabled or not self.settings.start_llm_command:
            return
        if event_callback is not None:
            event_callback("Restaurando modelos de texto despues de la generacion de audio.")
        subprocess.run(self.settings.start_llm_command, shell=True, timeout=120, check=False)

    def capture(
        self,
        phase: str,
        persist: bool = True,
        decision: str | None = None,
        message: str | None = None,
    ) -> dict[str, object]:
        if psutil is None:
            snapshot = {
                "id": f"resource_{uuid4().hex[:12]}",
                "phase": phase,
                "ram_total_mb": 0,
                "ram_available_mb": 0,
                "ram_used_percent": 100,
                "swap_total_mb": 0,
                "swap_free_mb": 0,
                "swap_used_mb": 0,
                "visible_memory_limit_mb": 0,
                "cpu_percent": 100,
            "vram": [],
            "accelerators": self._accelerator_snapshot(),
            "disk_data_free_mb": 0,
                "disk_models_free_mb": 0,
                "disk_cache_free_mb": 0,
                "heavy_processes": [],
                "decision": "blocked_missing_psutil",
                "message": "psutil no esta instalado. Ejecuta scripts/setup-local.ps1.",
            }
            if persist:
                stored = self.storage.create_resource_snapshot(snapshot)
                stored["accelerators"] = snapshot["accelerators"]
                return stored
            return snapshot
        cpu_percent = psutil.cpu_percent(interval=max(0, self.settings.sample_seconds))
        memory = psutil.virtual_memory()
        swap = psutil.swap_memory()
        snapshot = {
            "id": f"resource_{uuid4().hex[:12]}",
            "phase": phase,
            "ram_total_mb": self._mb(memory.total),
            "ram_available_mb": self._mb(memory.available),
            "ram_used_percent": float(memory.percent),
            "swap_total_mb": self._mb(swap.total),
            "swap_free_mb": self._mb(swap.free),
            "swap_used_mb": self._mb(swap.used),
            "visible_memory_limit_mb": self._visible_memory_limit_mb(),
            "cpu_percent": float(cpu_percent),
            "vram": self._vram_snapshot(),
            "accelerators": self._accelerator_snapshot(),
            "disk_data_free_mb": self._disk_free_mb(self.data_path),
            "disk_models_free_mb": self._disk_free_mb(self.models_path),
            "disk_cache_free_mb": self._disk_free_mb(self.cache_path),
            "heavy_processes": self._heavy_processes(),
            "decision": decision or "observed",
            "message": message or "Snapshot de recursos registrado.",
        }
        if persist:
            stored = self.storage.create_resource_snapshot(snapshot)
            stored["accelerators"] = snapshot["accelerators"]
            return stored
        return snapshot

    def evaluate(self, snapshot: dict[str, object]) -> AudioReadiness:
        recommendations = self.recommendations(snapshot)
        if snapshot.get("decision") == "blocked_missing_psutil":
            return AudioReadiness(False, "blocked_missing_psutil", str(snapshot.get("message", "")), snapshot, recommendations)
        ram_available = float(snapshot["ram_available_mb"])
        cpu_percent = float(snapshot["cpu_percent"])
        disk_values = [
            float(snapshot["disk_data_free_mb"]),
            float(snapshot["disk_models_free_mb"]),
            float(snapshot["disk_cache_free_mb"]),
        ]
        if ram_available < self.settings.min_free_ram_mb_for_audio:
            message = (
                "Advertencia: RAM disponible baja para voz cantada. "
                f"Disponible {ram_available:.0f} MB, referencia {self.settings.min_free_ram_mb_for_audio} MB. "
                "Puedes continuar; si ACE-Step falla, revisa este diagnostico."
            )
            return AudioReadiness(True, "warning_ram", message, snapshot, recommendations)
        if min(disk_values) < self.settings.min_free_disk_mb_for_audio:
            message = (
                "Advertencia: disco libre bajo para audio pesado. "
                f"Minimo libre {min(disk_values):.0f} MB, referencia {self.settings.min_free_disk_mb_for_audio} MB."
            )
            return AudioReadiness(True, "warning_disk", message, snapshot, recommendations)
        if cpu_percent > self.settings.max_cpu_percent_before_audio:
            message = (
                "Advertencia: CPU ocupada antes de iniciar audio pesado. "
                f"Actual {cpu_percent:.0f}%, referencia {self.settings.max_cpu_percent_before_audio}%."
            )
            return AudioReadiness(True, "warning_cpu", message, snapshot, recommendations)
        return AudioReadiness(True, "ready", "Diagnostico de recursos registrado. Puedes iniciar audio pesado.", snapshot, recommendations)

    def recommendations(self, snapshot: dict[str, object]) -> list[str]:
        recommendations: list[str] = []
        heavy_names = " ".join(str(item.get("name", "")) for item in list(snapshot.get("heavy_processes", []))).lower()
        if "llama" in heavy_names:
            recommendations.append("Cerrar Gemma/Qwen")
        if float(snapshot["ram_available_mb"]) < self.settings.min_free_ram_mb_for_audio * 1.25:
            recommendations.append("Bajar duracion a 15s")
            recommendations.append("Usar RVC en vez de ACE-Step")
            recommendations.append("Cerrar apps pesadas o aumentar memoria virtual")
        if float(snapshot.get("swap_total_mb", 0)) < 4096:
            recommendations.append("Se recomienda disponer de al menos 4 GB de swap para mejorar la estabilidad durante la generacion de audio")
        accelerators = dict(snapshot.get("accelerators", {}))
        if not bool(accelerators.get("cuda_available")):
            if bool(accelerators.get("intel_device_nodes")):
                recommendations.append("iGPU Intel visible como dispositivo Linux; ACE-Step/PyTorch necesita backend Intel XPU/Level Zero para usarla")
            else:
                recommendations.append("No hay GPU/NPU visible para el proceso local; ACE-Step esta limitado a CPU")
        if min(float(snapshot["disk_data_free_mb"]), float(snapshot["disk_models_free_mb"]), float(snapshot["disk_cache_free_mb"])) < self.settings.min_free_disk_mb_for_audio * 1.25:
            recommendations.append("Liberar espacio en disco")
        return recommendations or ["Recursos dentro del rango configurado"]

    def _accelerator_snapshot(self) -> dict[str, object]:
        device_nodes = {
            "nvidia": sorted(str(path) for path in Path("/dev").glob("nvidia*")),
            "dri": sorted(str(path) for path in Path("/dev/dri").glob("*")) if Path("/dev/dri").exists() else [],
            "dxg": ["/dev/dxg"] if Path("/dev/dxg").exists() else [],
            "accel": sorted(str(path) for path in Path("/dev/accel").glob("*")) if Path("/dev/accel").exists() else [],
        }
        cuda_available = bool(device_nodes["nvidia"]) and shutil.which("nvidia-smi") is not None
        return {
            "visible_cpu_count": os.cpu_count() or 0,
            "cpu_affinity_count": len(os.sched_getaffinity(0)) if hasattr(os, "sched_getaffinity") else os.cpu_count() or 0,
            "cuda_available": cuda_available,
            "nvidia_smi": bool(shutil.which("nvidia-smi")),
            "device_nodes": device_nodes,
            "intel_device_nodes": bool(device_nodes["dri"] or device_nodes["dxg"]),
            "npu_visible_to_process": bool(device_nodes["accel"]),
            "note": (
                "El proceso ve dispositivos de aceleracion Linux."
                if cuda_available or device_nodes["dri"] or device_nodes["dxg"] or device_nodes["accel"]
                else "El proceso local no ve iGPU/NPU/GPU mediante dispositivos Linux; revisa backend nativo Windows/OpenVINO/DirectML."
            ),
        }

    def _visible_memory_limit_mb(self) -> float:
        candidates = [
            Path("/sys/fs/cgroup/memory.max"),
            Path("/sys/fs/cgroup/memory/memory.limit_in_bytes"),
        ]
        for path in candidates:
            try:
                value = path.read_text(encoding="utf-8").strip()
            except OSError:
                continue
            if not value or value == "max":
                continue
            try:
                limit = int(value)
            except ValueError:
                continue
            if limit <= 0 or limit > 10**15:
                continue
            return self._mb(limit)
        return self._mb(os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES")) if hasattr(os, "sysconf") else 0

    def _heavy_processes(self) -> list[dict[str, object]]:
        processes: list[dict[str, object]] = []
        for process in psutil.process_iter(["pid", "name", "cmdline", "memory_info", "cpu_percent"]):
            try:
                name = str(process.info.get("name") or "")
                cmdline = " ".join(str(item) for item in (process.info.get("cmdline") or []))
                haystack = f"{name} {cmdline}".lower()
                if not any(token in haystack for token in HEAVY_PROCESS_NAMES):
                    continue
                memory_info = process.info.get("memory_info")
                processes.append(
                    {
                        "pid": int(process.info["pid"]),
                        "name": name,
                        "cmdline": cmdline[:240],
                        "rss_mb": self._mb(memory_info.rss) if memory_info else 0,
                        "cpu_percent": float(process.info.get("cpu_percent") or 0),
                    }
                )
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return processes

    def _vram_snapshot(self) -> list[dict[str, object]]:
        if shutil.which("nvidia-smi") is None:
            return []
        command = [
            "nvidia-smi",
            "--query-gpu=name,memory.total,memory.used,memory.free,utilization.gpu",
            "--format=csv,noheader,nounits",
        ]
        try:
            result = subprocess.run(command, capture_output=True, text=True, check=False, timeout=5)
        except (OSError, subprocess.SubprocessError):
            return []
        if result.returncode != 0:
            return []
        gpus: list[dict[str, object]] = []
        for line in result.stdout.splitlines():
            parts = [part.strip() for part in line.split(",")]
            if len(parts) != 5:
                continue
            gpus.append(
                {
                    "name": parts[0],
                    "vram_total_mb": self._float(parts[1]),
                    "vram_used_mb": self._float(parts[2]),
                    "vram_free_mb": self._float(parts[3]),
                    "gpu_util_percent": self._float(parts[4]),
                }
            )
        return gpus

    def _float(self, value: str) -> float:
        try:
            return float(value)
        except ValueError:
            return 0.0

    def _disk_free_mb(self, path: Path) -> float:
        path.mkdir(parents=True, exist_ok=True)
        return self._mb(shutil.disk_usage(path).free)

    def _mb(self, value: int | float) -> float:
        return round(float(value) / 1024 / 1024, 2)

    def _readiness_dict(self, readiness: AudioReadiness) -> dict[str, object]:
        return {
            "ready": readiness.ready,
            "decision": readiness.decision,
            "message": readiness.message,
            "recommendations": readiness.recommendations,
        }
