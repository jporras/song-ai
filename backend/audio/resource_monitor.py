from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import shutil
import subprocess
import time
from uuid import uuid4

try:
    import psutil
except ImportError:  # pragma: no cover - Docker instala psutil; esto mantiene importable el entorno local.
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
        self.models_path = models_path or Path("/app/models")
        self.cache_path = cache_path or Path("/app/provider-cache")

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
                event_callback("Liberando Gemma/Qwen/llama.cpp antes de audio pesado.")
            if self.settings.stop_llm_command:
                subprocess.run(self.settings.stop_llm_command, shell=True, timeout=60, check=False)
            if self.settings.audio_start_delay_seconds > 0:
                time.sleep(self.settings.audio_start_delay_seconds)
        after = self.capture(phase="after_llm_release", persist=True)
        readiness = self.evaluate(after)
        if not readiness.ready:
            raise ValueError(readiness.message)
        return {"snapshot": after, "before": before, "readiness": self._readiness_dict(readiness), "released_llm": True}

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
                "cpu_percent": 100,
                "disk_data_free_mb": 0,
                "disk_models_free_mb": 0,
                "disk_cache_free_mb": 0,
                "heavy_processes": [],
                "decision": "blocked_missing_psutil",
                "message": "psutil no esta instalado. Instala requirements o reconstruye Docker.",
            }
            if persist:
                return self.storage.create_resource_snapshot(snapshot)
            return snapshot
        cpu_percent = psutil.cpu_percent(interval=max(0, self.settings.sample_seconds))
        memory = psutil.virtual_memory()
        snapshot = {
            "id": f"resource_{uuid4().hex[:12]}",
            "phase": phase,
            "ram_total_mb": self._mb(memory.total),
            "ram_available_mb": self._mb(memory.available),
            "ram_used_percent": float(memory.percent),
            "cpu_percent": float(cpu_percent),
            "disk_data_free_mb": self._disk_free_mb(self.data_path),
            "disk_models_free_mb": self._disk_free_mb(self.models_path),
            "disk_cache_free_mb": self._disk_free_mb(self.cache_path),
            "heavy_processes": self._heavy_processes(),
            "decision": decision or "observed",
            "message": message or "Snapshot de recursos registrado.",
        }
        if persist:
            return self.storage.create_resource_snapshot(snapshot)
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
                "No hay RAM suficiente para voz cantada. "
                f"Disponible {ram_available:.0f} MB, requerido {self.settings.min_free_ram_mb_for_audio} MB."
            )
            return AudioReadiness(False, "blocked_ram", message, snapshot, recommendations)
        if min(disk_values) < self.settings.min_free_disk_mb_for_audio:
            message = (
                "No hay disco suficiente para audio pesado. "
                f"Minimo libre {min(disk_values):.0f} MB, requerido {self.settings.min_free_disk_mb_for_audio} MB."
            )
            return AudioReadiness(False, "blocked_disk", message, snapshot, recommendations)
        if cpu_percent > self.settings.max_cpu_percent_before_audio:
            message = (
                "CPU demasiado ocupada para iniciar audio pesado. "
                f"Actual {cpu_percent:.0f}%, maximo {self.settings.max_cpu_percent_before_audio}%."
            )
            return AudioReadiness(False, "blocked_cpu", message, snapshot, recommendations)
        return AudioReadiness(True, "ready", "Recursos suficientes para iniciar audio pesado.", snapshot, recommendations)

    def recommendations(self, snapshot: dict[str, object]) -> list[str]:
        recommendations: list[str] = []
        heavy_names = " ".join(str(item.get("name", "")) for item in list(snapshot.get("heavy_processes", []))).lower()
        if "llama" in heavy_names:
            recommendations.append("Cerrar Gemma/Qwen")
        if float(snapshot["ram_available_mb"]) < self.settings.min_free_ram_mb_for_audio * 1.25:
            recommendations.append("Bajar duracion a 15s")
            recommendations.append("Usar RVC en vez de ACE-Step")
            recommendations.append("Aumentar RAM asignada a Docker")
        if min(float(snapshot["disk_data_free_mb"]), float(snapshot["disk_models_free_mb"]), float(snapshot["disk_cache_free_mb"])) < self.settings.min_free_disk_mb_for_audio * 1.25:
            recommendations.append("Liberar espacio en disco")
        return recommendations or ["Recursos dentro del rango configurado"]

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
