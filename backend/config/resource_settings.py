from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path


@dataclass(frozen=True)
class ResourceMonitorSettings:
    enabled: bool
    sample_seconds: int
    min_free_ram_mb_for_audio: int
    min_free_disk_mb_for_audio: int
    max_cpu_percent_before_audio: int
    audio_start_delay_seconds: int
    release_llm_before_audio: bool
    stop_llm_command: str
    start_llm_command: str

    @classmethod
    def load(cls, project_root: Path | None = None) -> "ResourceMonitorSettings":
        start_script = project_root / "scripts" / "start-local-llms.ps1" if project_root else None
        stop_script = project_root / "scripts" / "stop-local-llms.ps1" if project_root else None
        default_start = f'powershell.exe -NoProfile -ExecutionPolicy Bypass -File "{start_script}"' if start_script and start_script.exists() else ""
        default_stop = f'powershell.exe -NoProfile -ExecutionPolicy Bypass -File "{stop_script}"' if stop_script and stop_script.exists() else ""
        stop_command = os.getenv("SONG_AI_STOP_LLM_COMMAND")
        start_command = os.getenv("SONG_AI_START_LLM_COMMAND")
        return cls(
            enabled=os.getenv("SONG_AI_RESOURCE_MONITOR_ENABLED", "true").lower() == "true",
            sample_seconds=int(os.getenv("SONG_AI_RESOURCE_SAMPLE_SECONDS", "2")),
            min_free_ram_mb_for_audio=int(os.getenv("SONG_AI_MIN_FREE_RAM_MB_FOR_AUDIO", "3500")),
            min_free_disk_mb_for_audio=int(os.getenv("SONG_AI_MIN_FREE_DISK_MB_FOR_AUDIO", "15000")),
            max_cpu_percent_before_audio=int(os.getenv("SONG_AI_MAX_CPU_PERCENT_BEFORE_AUDIO", "85")),
            audio_start_delay_seconds=int(os.getenv("SONG_AI_AUDIO_START_DELAY_SECONDS", "45")),
            release_llm_before_audio=os.getenv("SONG_AI_RELEASE_LLM_BEFORE_AUDIO", "true").lower() == "true",
            stop_llm_command=(stop_command if stop_command and stop_command.strip() else default_stop).strip(),
            start_llm_command=(start_command if start_command and start_command.strip() else default_start).strip(),
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "enabled": self.enabled,
            "sample_seconds": self.sample_seconds,
            "min_free_ram_mb_for_audio": self.min_free_ram_mb_for_audio,
            "min_free_disk_mb_for_audio": self.min_free_disk_mb_for_audio,
            "max_cpu_percent_before_audio": self.max_cpu_percent_before_audio,
            "audio_start_delay_seconds": self.audio_start_delay_seconds,
            "release_llm_before_audio": self.release_llm_before_audio,
            "stop_llm_command_configured": bool(self.stop_llm_command),
            "start_llm_command_configured": bool(self.start_llm_command),
        }
