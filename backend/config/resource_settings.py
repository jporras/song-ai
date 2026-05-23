from __future__ import annotations

from dataclasses import dataclass
import os


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

    @classmethod
    def load(cls) -> "ResourceMonitorSettings":
        return cls(
            enabled=os.getenv("SONG_AI_RESOURCE_MONITOR_ENABLED", "true").lower() == "true",
            sample_seconds=int(os.getenv("SONG_AI_RESOURCE_SAMPLE_SECONDS", "2")),
            min_free_ram_mb_for_audio=int(os.getenv("SONG_AI_MIN_FREE_RAM_MB_FOR_AUDIO", "6000")),
            min_free_disk_mb_for_audio=int(os.getenv("SONG_AI_MIN_FREE_DISK_MB_FOR_AUDIO", "15000")),
            max_cpu_percent_before_audio=int(os.getenv("SONG_AI_MAX_CPU_PERCENT_BEFORE_AUDIO", "85")),
            audio_start_delay_seconds=int(os.getenv("SONG_AI_AUDIO_START_DELAY_SECONDS", "90")),
            release_llm_before_audio=os.getenv("SONG_AI_RELEASE_LLM_BEFORE_AUDIO", "true").lower() == "true",
            stop_llm_command=os.getenv("SONG_AI_STOP_LLM_COMMAND", "").strip(),
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
        }
