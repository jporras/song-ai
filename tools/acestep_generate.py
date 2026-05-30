from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
import platform
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
import traceback


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser(description="Genera una cancion completa local con ACE-Step.")
    parser.add_argument("--prompt", required=True, help="Ruta al prompt musical.")
    parser.add_argument("--lyrics", required=True, help="Ruta al lyrics.md final.")
    parser.add_argument("--output", required=True, help="Ruta WAV final esperada.")
    parser.add_argument(
        "--checkpoint-path",
        default=str(PROJECT_ROOT / "data" / "models" / "music" / "ace-step"),
        help="Ruta de checkpoints ACE-Step.",
    )
    parser.add_argument("--duration", type=float, default=60.0, help="Duracion en segundos.")
    parser.add_argument("--infer-step", type=int, default=27)
    parser.add_argument(
        "--oss-steps",
        default="16, 96, 172, 200",
        help="Pasos OSS usados por ACE-Step. En CPU conviene usar pocos pasos para validar flujo.",
    )
    parser.add_argument("--guidance-scale", type=float, default=15.0)
    parser.add_argument("--scheduler-type", default="euler")
    parser.add_argument("--cfg-type", default="apg")
    parser.add_argument("--omega-scale", type=float, default=10.0)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--device-id", type=int, default=0)
    parser.add_argument("--bf16", default="true")
    parser.add_argument("--cpu-offload", default="true")
    parser.add_argument("--overlapped-decode", default="true")
    parser.add_argument(
        "--torch-threads",
        type=int,
        default=0,
        help="Hilos CPU para PyTorch/BLAS. 0 usa SONG_AI_TORCH_THREADS o todos los CPUs visibles.",
    )
    parser.add_argument(
        "--torch-interop-threads",
        type=int,
        default=0,
        help="Hilos inter-op de PyTorch. 0 usa SONG_AI_TORCH_INTEROP_THREADS o un valor conservador.",
    )
    parser.add_argument("--diagnostics", default="", help="Ruta JSON para guardar diagnostico completo de ACE-Step.")
    parser.add_argument(
        "--output-type",
        default="full_song_with_vocals",
        help="Etiqueta diagnostica de salida: instrumental, vocal o full_song_with_vocals.",
    )
    args = parser.parse_args()

    prompt = Path(args.prompt).read_text(encoding="utf-8")
    lyrics = Path(args.lyrics).read_text(encoding="utf-8")
    output_path = Path(args.output)
    checkpoint_path = Path(args.checkpoint_path)
    diagnostics_path = Path(args.diagnostics) if args.diagnostics.strip() else output_path.with_suffix(".ace_diagnostics.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if output_path.exists():
        output_path.unlink()
    checkpoint_path.mkdir(parents=True, exist_ok=True)

    add_provider_cache_to_path(os.getenv("SONG_AI_PROVIDER_CACHE", str(PROJECT_ROOT / "data" / "provider-cache")))
    configure_cpu_threads(args)
    started_at = time.monotonic()
    diagnostics = build_diagnostics(args, prompt, lyrics, output_path, checkpoint_path)
    diagnostics["resources"]["before"] = resource_snapshot()
    write_diagnostics(diagnostics_path, diagnostics)

    try:
        import torch
        from acestep.pipeline_ace_step import ACEStepPipeline
    except ImportError as error:
        diagnostics["status"] = "import_error"
        diagnostics["error"] = {
            "type": type(error).__name__,
            "message": str(error),
            "traceback": traceback.format_exc(),
        }
        diagnostics["resources"]["after_error"] = resource_snapshot()
        write_diagnostics(diagnostics_path, diagnostics)
        raise SystemExit(
            "ACE-Step no esta instalado en el entorno local. Ejecuta scripts/setup-local.ps1 "
            "o activa SONG_AI_BOOTSTRAP_ON_START=true y SONG_AI_INSTALL_ACE_STEP=true."
        ) from error

    os.environ["CUDA_VISIBLE_DEVICES"] = str(args.device_id)
    diagnostics["runtime"]["cuda_visible_devices"] = os.environ["CUDA_VISIBLE_DEVICES"]
    diagnostics["runtime"]["ace_step_pipeline"] = "acestep.pipeline_ace_step.ACEStepPipeline"
    diagnostics["runtime"]["torch"] = torch_runtime_snapshot(torch)
    try:
        pipeline = ACEStepPipeline(
            checkpoint_dir=str(checkpoint_path),
            dtype="bfloat16" if truthy(args.bf16) else "float32",
            torch_compile=False,
            cpu_offload=truthy(args.cpu_offload),
            overlapped_decode=truthy(args.overlapped_decode),
        )
        diagnostics["status"] = "pipeline_loaded"
        diagnostics["resources"]["after_pipeline_load"] = resource_snapshot()
        diagnostics["runtime"]["torch_after_pipeline_load"] = torch_runtime_snapshot(torch)
        write_diagnostics(diagnostics_path, diagnostics)

        pipeline(
            audio_duration=args.duration,
            prompt=prompt,
            lyrics=lyrics,
            infer_step=args.infer_step,
            guidance_scale=args.guidance_scale,
            scheduler_type=args.scheduler_type,
            cfg_type=args.cfg_type,
            omega_scale=args.omega_scale,
            manual_seeds=str(args.seed),
            guidance_interval=0.5,
            guidance_interval_decay=0.0,
            min_guidance_scale=3.0,
            use_erg_tag=True,
            use_erg_lyric=True,
            use_erg_diffusion=True,
            oss_steps=args.oss_steps,
            guidance_scale_text=0.0,
            guidance_scale_lyric=0.0,
            save_path=str(output_path),
            task="text2music",
            debug=True,
        )
    except Exception as error:
        diagnostics["status"] = "failed"
        diagnostics["duration_seconds"] = round(time.monotonic() - started_at, 3)
        diagnostics["resources"]["after_error"] = resource_snapshot()
        diagnostics["error"] = {
            "type": type(error).__name__,
            "message": str(error),
            "traceback": traceback.format_exc(),
        }
        write_diagnostics(diagnostics_path, diagnostics)
        raise

    if not output_path.exists() or output_path.stat().st_size == 0:
        diagnostics["status"] = "missing_output"
        diagnostics["duration_seconds"] = round(time.monotonic() - started_at, 3)
        diagnostics["resources"]["after_missing_output"] = resource_snapshot()
        write_diagnostics(diagnostics_path, diagnostics)
        raise SystemExit(f"ACE-Step no genero el WAV esperado: {output_path}")
    diagnostics["status"] = "completed"
    diagnostics["duration_seconds"] = round(time.monotonic() - started_at, 3)
    diagnostics["output"]["exists"] = True
    diagnostics["output"]["size_bytes"] = output_path.stat().st_size
    diagnostics["resources"]["after"] = resource_snapshot()
    write_diagnostics(diagnostics_path, diagnostics)
    print(f"Diagnostico ACE-Step guardado: {diagnostics_path}")
    print(f"Cancion completa generada con ACE-Step: {output_path}")
    return 0


def truthy(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "on"}


def add_provider_cache_to_path(provider_cache: str) -> None:
    provider_python = str(Path(provider_cache) / "python")
    if provider_python not in sys.path:
        sys.path.insert(0, provider_python)


def visible_cpu_count() -> int:
    try:
        if hasattr(os, "sched_getaffinity"):
            return max(1, len(os.sched_getaffinity(0)))
    except Exception:
        pass
    return max(1, os.cpu_count() or 1)


def int_env(name: str, default: int) -> int:
    try:
        return int(str(os.getenv(name, "")).strip() or default)
    except ValueError:
        return default


def configure_cpu_threads(args: argparse.Namespace) -> None:
    cpu_count = visible_cpu_count()
    torch_threads = args.torch_threads or int_env("SONG_AI_TORCH_THREADS", cpu_count)
    interop_threads = args.torch_interop_threads or int_env("SONG_AI_TORCH_INTEROP_THREADS", max(1, min(4, cpu_count // 2 or 1)))
    torch_threads = max(1, min(torch_threads, cpu_count))
    interop_threads = max(1, min(interop_threads, cpu_count))
    thread_env = {
        "OMP_NUM_THREADS": torch_threads,
        "MKL_NUM_THREADS": torch_threads,
        "OPENBLAS_NUM_THREADS": torch_threads,
        "NUMEXPR_NUM_THREADS": torch_threads,
        "VECLIB_MAXIMUM_THREADS": torch_threads,
        "TORCH_NUM_THREADS": torch_threads,
        "TORCH_INTEROP_THREADS": interop_threads,
    }
    for key, value in thread_env.items():
        os.environ[key] = str(value)
    try:
        import torch

        torch.set_num_threads(torch_threads)
        torch.set_num_interop_threads(interop_threads)
    except Exception:
        pass


def torch_runtime_snapshot(torch_module: object) -> dict[str, object]:
    cuda = getattr(torch_module, "cuda", None)
    cuda_available = bool(cuda and cuda.is_available())
    gpu_name = ""
    if cuda_available:
        try:
            gpu_name = str(cuda.get_device_name(0))
        except Exception:
            gpu_name = ""
    return {
        "torch_version": str(getattr(torch_module, "__version__", "")),
        "cuda_available": cuda_available,
        "cuda_device_count": int(cuda.device_count()) if cuda else 0,
        "cuda_device_name": gpu_name,
        "torch_num_threads": int(torch_module.get_num_threads()),
        "torch_num_interop_threads": int(torch_module.get_num_interop_threads()),
        "visible_cpu_count": visible_cpu_count(),
        "thread_env": {
            key: os.getenv(key, "")
            for key in (
                "OMP_NUM_THREADS",
                "MKL_NUM_THREADS",
                "OPENBLAS_NUM_THREADS",
                "NUMEXPR_NUM_THREADS",
                "TORCH_NUM_THREADS",
                "TORCH_INTEROP_THREADS",
            )
        },
    }


def build_diagnostics(args: argparse.Namespace, prompt: str, lyrics: str, output_path: Path, checkpoint_path: Path) -> dict[str, object]:
    return {
        "schema": "song-ai-ace-step-diagnostics-v1",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": "initialized",
        "integration": {
            "mode": "python_library_via_cli_process",
            "library": "acestep",
            "service_api": False,
            "cli_process": True,
            "entrypoint": "tools/acestep_generate.py",
        },
        "input": {
            "prompt_path": str(Path(args.prompt)),
            "lyrics_path": str(Path(args.lyrics)),
            "prompt": prompt,
            "lyrics": lyrics,
            "prompt_length": len(prompt),
            "lyrics_length": len(lyrics),
            "detected_language": detect_language(lyrics),
            "has_spanish_language_tag": bool(re.search(r"(?im)^\s*\[es\]\s*$", lyrics)),
            "contains_unicode": any(ord(character) > 127 for character in lyrics),
            "contains_accents": bool(re.search(r"[áéíóúÁÉÍÓÚñÑüÜ]", lyrics)),
            "sections": detect_sections(lyrics),
        },
        "model": {
            "checkpoint_path": str(checkpoint_path),
            "checkpoint_path_exists": checkpoint_path.exists(),
        },
        "parameters": {
            "audio_duration": args.duration,
            "infer_step": args.infer_step,
            "guidance_scale": args.guidance_scale,
            "scheduler_type": args.scheduler_type,
            "cfg_type": args.cfg_type,
            "omega_scale": args.omega_scale,
            "manual_seeds": str(args.seed),
            "guidance_interval": 0.5,
            "guidance_interval_decay": 0.0,
            "min_guidance_scale": 3.0,
            "use_erg_tag": True,
            "use_erg_lyric": True,
            "use_erg_diffusion": True,
            "oss_steps": args.oss_steps,
            "guidance_scale_text": 0.0,
            "guidance_scale_lyric": 0.0,
            "task": "text2music",
            "audio2audio_enable": False,
            "output_type": args.output_type,
            "instrumental_mode": False,
            "music_only_mode": False,
            "lyric_free_generation": lyrics.strip() == "",
            "sung_vocal_requested": bool(lyrics.strip()),
        },
        "runtime": {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "visible_cpu_count": visible_cpu_count(),
            "cuda_visible_devices": "",
            "ace_step_pipeline": "",
            "torch": {},
        },
        "output": {
            "path": str(output_path),
            "exists": False,
            "size_bytes": 0,
        },
        "resources": {},
    }


def detect_language(lyrics: str) -> str:
    lower = lyrics.lower()
    if re.search(r"(?im)^\s*\[es\]\s*$", lyrics):
        return "Spanish"
    spanish_tokens = {"duerme", "cielo", "ojos", "aqui", "aquí", "contigo", "sueño", "sueno", "amor", "corazon", "corazón"}
    english_tokens = {"sleep", "dream", "eyes", "with", "here", "lullaby", "heart"}
    spanish_score = sum(1 for token in spanish_tokens if token in lower)
    english_score = sum(1 for token in english_tokens if token in lower)
    if spanish_score > english_score:
        return "Spanish"
    if english_score > spanish_score:
        return "English"
    return "unknown"


def detect_sections(lyrics: str) -> list[dict[str, object]]:
    sections: list[dict[str, object]] = []
    for index, line in enumerate(lyrics.splitlines(), start=1):
        stripped = line.strip()
        bracket_match = re.fullmatch(r"\[([A-Za-z0-9_-]+)\]", stripped)
        markdown_match = re.fullmatch(r"#{1,6}\s+(.+)", stripped)
        if bracket_match:
            sections.append({"line": index, "syntax": "bracket", "label": bracket_match.group(1).lower()})
        elif markdown_match:
            sections.append({"line": index, "syntax": "markdown", "label": markdown_match.group(1).strip()})
    return sections


def resource_snapshot() -> dict[str, object]:
    snapshot: dict[str, object] = {
        "ram_total_mb": 0,
        "ram_available_mb": 0,
        "ram_used_percent": 0,
        "swap_total_mb": 0,
        "swap_used_mb": 0,
        "cpu_percent": 0,
        "vram": [],
    }
    try:
        import psutil

        memory = psutil.virtual_memory()
        swap = psutil.swap_memory()
        snapshot.update(
            {
                "ram_total_mb": mb(memory.total),
                "ram_available_mb": mb(memory.available),
                "ram_used_percent": float(memory.percent),
                "swap_total_mb": mb(swap.total),
                "swap_used_mb": mb(swap.used),
                "cpu_percent": float(psutil.cpu_percent(interval=0.1)),
            }
        )
    except Exception as error:
        snapshot["psutil_error"] = str(error)
    snapshot["vram"] = vram_snapshot()
    return snapshot


def vram_snapshot() -> list[dict[str, object]]:
    if shutil.which("nvidia-smi") is None:
        return []
    command = [
        "nvidia-smi",
        "--query-gpu=name,memory.total,memory.used,memory.free,utilization.gpu",
        "--format=csv,noheader,nounits",
    ]
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=False, timeout=5)
    except Exception:
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
                "vram_total_mb": parse_float(parts[1]),
                "vram_used_mb": parse_float(parts[2]),
                "vram_free_mb": parse_float(parts[3]),
                "gpu_util_percent": parse_float(parts[4]),
            }
        )
    return gpus


def parse_float(value: str) -> float:
    try:
        return float(value)
    except ValueError:
        return 0.0


def mb(value: int | float) -> float:
    return round(float(value) / 1024 / 1024, 2)


def write_diagnostics(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
