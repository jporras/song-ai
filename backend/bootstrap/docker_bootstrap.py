from __future__ import annotations

from pathlib import Path
import os
import shutil
import subprocess
import sys
import urllib.request


MODEL_ROOT = Path(os.getenv("SONG_AI_MODEL_ROOT", "/app/models"))
PROVIDER_ROOT = Path(os.getenv("SONG_AI_PROVIDER_ROOT", "/app/providers"))
CACHE_ROOT = Path(os.getenv("SONG_AI_PROVIDER_CACHE", "/app/provider-cache"))
PYTHON_TARGET = CACHE_ROOT / "python"
PIP_CACHE = CACHE_ROOT / "pip"


def run_bootstrap(force: bool = False) -> dict[str, object]:
    summary: dict[str, object] = {
        "enabled": force or enabled("SONG_AI_BOOTSTRAP_ON_START"),
        "directories": [],
        "installed_deps": False,
        "downloads": [],
        "providers": [],
    }
    ensure_directories(summary)
    if not summary["enabled"]:
        return summary

    if enabled("SONG_AI_INSTALL_LOCAL_AUDIO_DEPS"):
        install_local_audio_deps()
        summary["installed_deps"] = True
    if enabled("SONG_AI_INSTALL_ACE_STEP"):
        install_ace_step()
        summary["installed_ace_step"] = True

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


def install_local_audio_deps() -> None:
    requirements = Path("/app/backend/requirements-local-audio.txt")
    if not requirements.exists():
        raise RuntimeError(f"No existe {requirements}")
    subprocess.run(
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            "--cache-dir",
            str(PIP_CACHE),
            "--target",
            str(PYTHON_TARGET),
            "-r",
            str(requirements),
        ],
        check=True,
    )


def install_ace_step() -> None:
    subprocess.run(
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            "--cache-dir",
            str(PIP_CACHE),
            "--target",
            str(PYTHON_TARGET),
            "git+https://github.com/ace-step/ACE-Step.git",
        ],
        check=True,
    )


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
