"""Resolve ffmpeg from PATH or the project's managed local installation."""
from pathlib import Path
import os
import shutil


def resolve_ffmpeg(repository_root: Path) -> str | None:
    available = shutil.which("ffmpeg")
    if available:
        return available
    executable = "ffmpeg.exe" if os.name == "nt" else "ffmpeg"
    managed = repository_root / "data" / "tools" / "ffmpeg" / "bin" / executable
    return str(managed.resolve()) if managed.is_file() else None
