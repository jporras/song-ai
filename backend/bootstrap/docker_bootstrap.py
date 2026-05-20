from __future__ import annotations

from contextlib import contextmanager
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


LLM_MODEL_CONFIG = {
    "gemma": {
        "url_env": "SONG_AI_GEMMA_GGUF_URL",
        "path_env": "SONG_AI_GEMMA_GGUF_PATH",
        "default_path": MODEL_ROOT / "llm" / "gemma" / "gemma.gguf",
    },
    "qwen": {
        "url_env": "SONG_AI_QWEN_GGUF_URL",
        "path_env": "SONG_AI_QWEN_GGUF_PATH",
        "default_path": MODEL_ROOT / "llm" / "qwen" / "qwen.gguf",
    },
}


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


def refresh_llm_model(role: str) -> dict[str, object]:
    normalized_role = role.strip().lower()
    if normalized_role not in LLM_MODEL_CONFIG:
        raise RuntimeError("Modelo LLM no soportado. Usa 'gemma' o 'qwen'.")
    summary: dict[str, object] = {
        "enabled": True,
        "upgrade": True,
        "python": sys.version.split()[0],
        "policy": "refresh_single_llm_model",
        "directories": [],
        "installed_deps": False,
        "downloads": [],
        "providers": [],
        "model_role": normalized_role,
    }
    ensure_directories(summary)
    download_url_models(summary, refresh_roles={normalized_role}, require_url=True)
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
    ready = local_audio_deps_ready()
    if marker_current(LOCAL_AUDIO_MARKER, marker_content, upgrade) and ready:
        return False
    if not upgrade and ready:
        write_marker(LOCAL_AUDIO_MARKER, marker_content)
        return False
    needs_repair = modules_available(required_modules) and not ready
    command = (
        pip_install_command(upgrade=True) + ["huggingface_hub>=0.34.0,<1.0"]
        if needs_repair and not upgrade
        else pip_install_command(upgrade) + ["-r", str(requirements)]
    )
    subprocess.run(command, check=True)
    write_marker(LOCAL_AUDIO_MARKER, marker_content)
    return True


def install_ace_step(upgrade: bool = False) -> bool:
    requirement = os.getenv("SONG_AI_ACE_STEP_PACKAGE", "git+https://github.com/ace-step/ACE-Step.git").strip()
    ready = ace_step_ready()
    if marker_current(ACE_STEP_MARKER, requirement, upgrade) and ready:
        return False
    if not upgrade and ready:
        write_marker(ACE_STEP_MARKER, requirement)
        return False
    needs_repair = modules_available(["acestep"]) and not ready
    if needs_repair or upgrade:
        clean_provider_packages(
            [
                "torch",
                "torchvision",
                "torchaudio",
                "transformers",
                "diffusers",
                "accelerate",
                "peft",
            ]
        )
    command = pip_install_command(upgrade or needs_repair) + [requirement]
    subprocess.run(command, check=True)
    if modules_available(["acestep"]) and not ace_step_ready():
        clean_provider_packages(["torchvision"])
        if modules_available(["acestep"]) and not ace_step_ready():
            raise RuntimeError(
                "ACE-Step se instalo, pero no pudo importarse. Revisa compatibilidad Torch/Torchvision "
                "en /app/provider-cache/python."
            )
    write_marker(ACE_STEP_MARKER, requirement)
    return True


def download_url_models(
    summary: dict[str, object],
    refresh_roles: set[str] | None = None,
    require_url: bool = False,
) -> None:
    refresh_roles = refresh_roles or set()
    url_targets = {
        config["url_env"]: {
            "role": role,
            "target": Path(os.getenv(str(config["path_env"]), str(config["default_path"]))),
        }
        for role, config in LLM_MODEL_CONFIG.items()
    }
    url_targets["SONG_AI_VOICE_MODEL_URL"] = {"role": "voice", "target": MODEL_ROOT / "voice"}
    for env_name, metadata in url_targets.items():
        role = str(metadata["role"])
        target = Path(metadata["target"])
        if refresh_roles and role not in refresh_roles:
            continue
        url = os.getenv(env_name, "").strip()
        if not url:
            if require_url:
                raise RuntimeError(f"Falta configurar {env_name} para descargar/recrear el modelo {role}.")
            continue
        if target.suffix:
            target_path = target
            target_path.parent.mkdir(parents=True, exist_ok=True)
        else:
            target.mkdir(parents=True, exist_ok=True)
            filename = Path(url.split("?")[0]).name or f"{env_name.lower()}.bin"
            target_path = target / filename
        if role in refresh_roles and target_path.exists():
            target_path.unlink()
        downloaded = False
        if not target_path.exists():
            download_to_path(url, target_path)
            downloaded = True
        summary["downloads"].append({"env": env_name, "role": role, "path": str(target_path), "downloaded": downloaded})


def download_to_path(url: str, target_path: Path) -> None:
    target_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = target_path.with_suffix(target_path.suffix + ".download")
    if temporary_path.exists():
        temporary_path.unlink()
    urllib.request.urlretrieve(url, temporary_path)
    temporary_path.replace(target_path)


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


def clean_provider_packages(package_names: list[str]) -> None:
    for package_name in package_names:
        normalized = package_name.replace("-", "_").lower()
        for path in PYTHON_TARGET.glob(f"{normalized}*"):
            if path.is_dir():
                shutil.rmtree(path)
            elif path.exists():
                path.unlink()


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
    with provider_python_path():
        return all(importlib.util.find_spec(module_name) is not None for module_name in module_names)


def local_audio_deps_ready() -> bool:
    if not modules_available(["huggingface_hub", "transformers", "scipy", "torch"]):
        return False
    return provider_python_probe("from huggingface_hub import DDUFEntry", timeout=30)


def ace_step_ready() -> bool:
    return provider_python_probe("from acestep.pipeline_ace_step import ACEStepPipeline", timeout=180)


@contextmanager
def provider_python_path():
    target = str(PYTHON_TARGET)
    inserted = target not in sys.path
    if inserted:
        sys.path.insert(0, target)
    try:
        yield
    finally:
        if inserted:
            try:
                sys.path.remove(target)
            except ValueError:
                pass


def provider_python_probe(statement: str, timeout: int = 30) -> bool:
    env = os.environ.copy()
    existing_pythonpath = env.get("PYTHONPATH", "")
    provider_path = str(PYTHON_TARGET)
    env["PYTHONPATH"] = provider_path + (os.pathsep + existing_pythonpath if existing_pythonpath else "")
    result = subprocess.run(
        [sys.executable, "-c", statement],
        capture_output=True,
        text=True,
        env=env,
        timeout=timeout,
    )
    return result.returncode == 0
