from __future__ import annotations

from pathlib import Path
import importlib.util
import os
import shutil
import subprocess
import sys
import urllib.request
from datetime import datetime, timezone


MODEL_ROOT = Path(os.getenv("SONG_AI_MODEL_ROOT", "/app/models"))
PROVIDER_ROOT = Path(os.getenv("SONG_AI_PROVIDER_ROOT", "/app/providers"))
CACHE_ROOT = Path(os.getenv("SONG_AI_PROVIDER_CACHE", "/app/provider-cache"))
PYTHON_TARGET = CACHE_ROOT / "python"
PIP_CACHE = CACHE_ROOT / "pip"
LOCAL_AUDIO_MARKER = CACHE_ROOT / ".local-audio-deps.installed"
ACE_STEP_MARKER = CACHE_ROOT / ".ace-step.installed"


def run_bootstrap(force: bool = False, upgrade: bool = False) -> dict[str, object]:
    summary: dict[str, object] = {
        "enabled": force or enabled("SONG_AI_BOOTSTRAP_ON_START"),
        "upgrade": upgrade or enabled("SONG_AI_BOOTSTRAP_UPGRADE"),
        "python": sys.version.split()[0],
        "policy": "idempotent_no_auto_upgrade",
        "directories": [],
        "installed_deps": False,
        "downloads": [],
        "providers": [],
    }
    ensure_directories(summary)
    if not summary["enabled"]:
        return summary

    if enabled("SONG_AI_INSTALL_LOCAL_AUDIO_DEPS"):
        summary["installed_deps"] = install_local_audio_deps(bool(summary["upgrade"]))
    if enabled("SONG_AI_INSTALL_ACE_STEP"):
        summary["installed_ace_step"] = install_ace_step(bool(summary["upgrade"]))

    download_url_models(summary)
    download_huggingface_models(summary)
    clone_provider_repositories(summary)
    return summary


def ensure_directories(summary: dict[str, object]) -> None:
    directories = [
        MODEL_ROOT,
        MODEL_ROOT / "llm",
        MODEL_ROOT / "music",
        MODEL_ROOT / "voice",
        MODEL_ROOT / "stems",
        MODEL_ROOT / "huggingface",
        PROVIDER_ROOT,
        CACHE_ROOT,
        PYTHON_TARGET,
        PIP_CACHE,
    ]
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
    summary["directories"] = [str(directory) for directory in directories]


def install_local_audio_deps(upgrade: bool = False) -> bool:
    requirements = Path("/app/backend/requirements-local-audio.txt")
    if not requirements.exists():
        raise RuntimeError(f"No existe {requirements}")
    marker_content = requirements.read_text(encoding="utf-8")
    required_modules = ["huggingface_hub", "transformers", "scipy", "torch"]
    if marker_current(LOCAL_AUDIO_MARKER, marker_content, upgrade) and modules_available(required_modules):
        return False
    if not upgrade and modules_available(required_modules):
        write_marker(LOCAL_AUDIO_MARKER, marker_content)
        return False
    command = pip_install_command(upgrade) + ["-r", str(requirements)]
    subprocess.run(command, check=True)
    write_marker(LOCAL_AUDIO_MARKER, marker_content)
    return True


def install_ace_step(upgrade: bool = False) -> bool:
    requirement = os.getenv("SONG_AI_ACE_STEP_PACKAGE", "git+https://github.com/ace-step/ACE-Step.git").strip()
    if marker_current(ACE_STEP_MARKER, requirement, upgrade) and modules_available(["acestep"]):
        return False
    if not upgrade and modules_available(["acestep"]):
        write_marker(ACE_STEP_MARKER, requirement)
        return False
    command = pip_install_command(upgrade) + [requirement]
    subprocess.run(command, check=True)
    write_marker(ACE_STEP_MARKER, requirement)
    return True


def download_url_models(summary: dict[str, object]) -> None:
    url_targets = {
        "SONG_AI_GEMMA_GGUF_URL": MODEL_ROOT / "llm" / "gemma",
        "SONG_AI_QWEN_GGUF_URL": MODEL_ROOT / "llm" / "qwen",
        "SONG_AI_VOICE_MODEL_URL": MODEL_ROOT / "voice",
    }
    for env_name, target_dir in url_targets.items():
        url = os.getenv(env_name, "").strip()
        if not url:
            continue
        target_dir.mkdir(parents=True, exist_ok=True)
        filename = Path(url.split("?")[0]).name or f"{env_name.lower()}.bin"
        target_path = target_dir / filename
        if not target_path.exists():
            urllib.request.urlretrieve(url, target_path)
        summary["downloads"].append({"env": env_name, "path": str(target_path)})


def download_huggingface_models(summary: dict[str, object]) -> None:
    model_ids = split_list(os.getenv("SONG_AI_HF_MODEL_IDS", ""))
    musicgen_model = os.getenv("SONG_AI_MUSICGEN_MODEL_ID", "").strip()
    if enabled("SONG_AI_DOWNLOAD_MUSICGEN") and musicgen_model:
        model_ids.append(musicgen_model)
    if not model_ids:
        return

    try:
        from huggingface_hub import snapshot_download
    except ImportError as error:
        raise RuntimeError(
            "huggingface_hub no esta instalado. Activa SONG_AI_INSTALL_LOCAL_AUDIO_DEPS=true "
            "o instala dependencias locales en el volumen."
        ) from error

    hf_root = MODEL_ROOT / "huggingface"
    for model_id in model_ids:
        local_dir = hf_root / safe_name(model_id)
        snapshot_download(repo_id=model_id, local_dir=local_dir, local_dir_use_symlinks=False)
        summary["downloads"].append({"hf_model": model_id, "path": str(local_dir)})


def clone_provider_repositories(summary: dict[str, object]) -> None:
    repos = split_list(os.getenv("SONG_AI_PROVIDER_REPOS", ""))
    git_path = shutil.which("git")
    if repos and git_path is None:
        raise RuntimeError("SONG_AI_PROVIDER_REPOS requiere git dentro del contenedor.")
    for item in repos:
        if "=" not in item:
            raise RuntimeError("Cada provider repo debe tener formato nombre=url.")
        name, url = item.split("=", 1)
        target = PROVIDER_ROOT / safe_name(name)
        if target.exists():
            subprocess.run([git_path, "-C", str(target), "pull", "--ff-only"], check=True)
        else:
            subprocess.run([git_path, "clone", url, str(target)], check=True)
        summary["providers"].append({"name": name, "path": str(target)})


def enabled(name: str) -> bool:
    return os.getenv(name, "false").strip().lower() in {"1", "true", "yes", "on"}


def split_list(value: str) -> list[str]:
    return [item.strip() for item in value.replace("\n", ";").split(";") if item.strip()]


def safe_name(value: str) -> str:
    return "".join(character if character.isalnum() or character in "._-" else "_" for character in value)


def pip_install_command(upgrade: bool = False) -> list[str]:
    command = [
        sys.executable,
        "-m",
        "pip",
        "install",
        "--disable-pip-version-check",
        "--cache-dir",
        str(PIP_CACHE),
        "--target",
        str(PYTHON_TARGET),
    ]
    if upgrade or enabled("SONG_AI_BOOTSTRAP_UPGRADE"):
        command.extend(["--upgrade", "--upgrade-strategy", "eager"])
    return command


def marker_current(path: Path, content: str, upgrade: bool = False) -> bool:
    if upgrade or enabled("SONG_AI_BOOTSTRAP_UPGRADE"):
        return False
    if not path.exists():
        return False
    marker = path.read_text(encoding="utf-8")
    return marker.startswith(content) and f"python={sys.version.split()[0]}" in marker


def write_marker(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    marker = "\n".join(
        [
            content,
            f"python={sys.version.split()[0]}",
            f"updated_at={datetime.now(timezone.utc).isoformat()}",
        ]
    )
    path.write_text(marker, encoding="utf-8")


def modules_available(module_names: list[str]) -> bool:
    return all(importlib.util.find_spec(module_name) is not None for module_name in module_names)
