from __future__ import annotations

import argparse
from datetime import datetime, timezone
import importlib
import importlib.util
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

# Configuración dinámica de paths del proyecto
PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = PROJECT_ROOT / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

# Import local sin interferencias
from audio.accelerator_detection import choose_ace_device


def patch_transformers_dtype_kwarg_for_acestep() -> bool:
    """ACE-Step 1.5 passes dtype= to Transformers; 4.53 expects torch_dtype=."""
    try:
        from transformers import AutoModel
    except Exception:
        return False

    if getattr(AutoModel.from_pretrained, "__song_ai_dtype_patch__", False):
        return False

    original_from_pretrained = AutoModel.from_pretrained

    def _from_pretrained_with_torch_dtype(cls, *args, **kwargs):
        if "dtype" in kwargs and "torch_dtype" not in kwargs:
            kwargs["torch_dtype"] = kwargs.pop("dtype")
        return original_from_pretrained(*args, **kwargs)

    _from_pretrained_with_torch_dtype.__song_ai_dtype_patch__ = True
    AutoModel.from_pretrained = classmethod(_from_pretrained_with_torch_dtype)
    return True


def patch_transformers_dynamic_cache_for_acestep() -> bool:
    """ACE-Step 1.5 remote model expects DynamicCache.layers[*].keys/values."""
    try:
        from types import SimpleNamespace
        from transformers.cache_utils import DynamicCache
    except Exception:
        return False

    if hasattr(DynamicCache, "layers"):
        return False

    def _layers(self):
        return [
            SimpleNamespace(keys=key_states, values=value_states)
            for key_states, value_states in zip(self.key_cache, self.value_cache)
        ]

    DynamicCache.layers = property(_layers)
    return True


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
    parser.add_argument(
        "--config-path",
        default=os.getenv("ACESTEP_CONFIG_PATH", "acestep-v15-turbo"),
        help="Modelo DiT ACE-Step 1.5, por ejemplo acestep-v15-turbo.",
    )
    parser.add_argument(
        "--lm-model-path",
        default=os.getenv("ACESTEP_LM_MODEL_PATH", "acestep-5Hz-lm-0.6B"),
        help="Modelo LM 5Hz para rutas con LM/API. En pruebas XPU usar 0.6B o 1.7B.",
    )
    parser.add_argument(
        "--device",
        default=os.getenv("SONG_AI_ACE_DEVICE", "auto"),
        choices=["auto", "xpu", "cuda", "cpu"],
        help="Dispositivo ACE-Step: auto intenta XPU, luego CUDA y finalmente CPU.",
    )
    parser.add_argument(
        "--require-device",
        default=os.getenv("SONG_AI_REQUIRE_ACE_DEVICE", "false"),
        help="Si es true, falla si el dispositivo solicitado no queda activo.",
    )
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
        "--check-only",
        action="store_true",
        help="Solo valida imports, device y entorno. No carga el pipeline ni genera audio.",
    )
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
    if output_path.exists() and not args.check_only:
        output_path.unlink()
    checkpoint_path.mkdir(parents=True, exist_ok=True)

    configure_official_xpu_environment(args)
    configure_cpu_threads(args)
    started_at = time.monotonic()
    diagnostics = build_diagnostics(args, prompt, lyrics, output_path, checkpoint_path)
    diagnostics["resources"]["before"] = resource_snapshot()
    write_diagnostics(diagnostics_path, diagnostics)
    print_check("inputs", True, f"prompt={args.prompt} lyrics={args.lyrics}")
    print_check("checkpoint path", checkpoint_path.exists(), str(checkpoint_path))

    try:
        import torch
    except ImportError as error:
        diagnostics["status"] = "import_error"
        diagnostics["error"] = {
            "type": type(error).__name__,
            "message": str(error),
            "traceback": traceback.format_exc(),
        }
        diagnostics["resources"]["after_error"] = resource_snapshot()
        write_diagnostics(diagnostics_path, diagnostics)
        print_check("torch import", False, str(error))
        raise SystemExit("PyTorch no esta instalado en el .venv local. Ejecuta pip install -r requirements.txt.") from error
    apply_torch_thread_settings(torch)
    torch_debug = torch_debug_snapshot(torch)
    diagnostics["runtime"]["torch_debug"] = torch_debug
    print_torch_debug(torch_debug)
    companions = preload_torch_companions()
    diagnostics["runtime"]["torch_companions"] = companions

    acestep_api = load_acestep_api()
    diagnostics["runtime"]["ace_step_api"] = {
        key: value
        for key, value in acestep_api.items()
        if key != "handler_class"
    }
    if not bool(acestep_api["available"]):
        error = RuntimeError(str(acestep_api["message"]))
        diagnostics["status"] = "import_error"
        diagnostics["runtime"]["torch"] = torch_runtime_snapshot(torch)
        diagnostics["runtime"]["torch_debug"] = torch_debug
        diagnostics["error"] = {
            "type": type(error).__name__,
            "message": str(error),
            "traceback": traceback.format_exc(),
        }
        diagnostics["resources"]["after_error"] = resource_snapshot()
        write_diagnostics(diagnostics_path, diagnostics)
        print_check("ACE-Step import", False, str(acestep_api["message"]))
        print(f"Diagnostico ACE-Step guardado: {diagnostics_path}")
        raise SystemExit(
            "ACE-Step no esta listo en el .venv local. Revisa el diagnostico para distinguir "
            "instalacion faltante, dependencia faltante o API incompatible."
        ) from error
    AceStepHandler = acestep_api["handler_class"]
    print_check("ACE-Step API", True, str(acestep_api["message"]))

    try:
        device_selection = choose_ace_device(torch, args.device, require_device=truthy(args.require_device))
    except Exception as error:
        diagnostics["status"] = "failed"
        diagnostics["duration_seconds"] = round(time.monotonic() - started_at, 3)
        diagnostics["runtime"]["torch"] = torch_runtime_snapshot(torch)
        diagnostics["runtime"]["torch_debug"] = torch_debug
        diagnostics["resources"]["after_error"] = resource_snapshot()
        diagnostics["error"] = {
            "type": type(error).__name__,
            "message": str(error),
            "traceback": traceback.format_exc(),
        }
        write_diagnostics(diagnostics_path, diagnostics)
        print_check("device", False, str(error))
        print(f"Diagnostico ACE-Step guardado: {diagnostics_path}")
        raise SystemExit(1) from error
    configure_accelerator_environment(args, device_selection)
    diagnostics["runtime"].update(device_selection)
    diagnostics["runtime"]["cuda_visible_devices"] = os.environ.get("CUDA_VISIBLE_DEVICES", "")
    diagnostics["runtime"]["acestep_device_env"] = os.environ.get("ACESTEP_DEVICE", "")
    diagnostics["runtime"]["acestep_lm_device_env"] = os.environ.get("ACESTEP_LM_DEVICE", "")
    diagnostics["runtime"]["pytorch_device_env"] = os.environ.get("PYTORCH_DEVICE", "")
    diagnostics["runtime"]["sycl_cache_persistent"] = os.environ.get("SYCL_CACHE_PERSISTENT", "")
    diagnostics["runtime"]["sycl_immediate_commandlists"] = os.environ.get("SYCL_PI_LEVEL_ZERO_USE_IMMEDIATE_COMMANDLISTS", "")
    diagnostics["runtime"]["torch_compile_backend"] = os.environ.get("TORCH_COMPILE_BACKEND", "")
    diagnostics["runtime"]["acestep_config_path_env"] = os.environ.get("ACESTEP_CONFIG_PATH", "")
    diagnostics["runtime"]["acestep_lm_backend_env"] = os.environ.get("ACESTEP_LM_BACKEND", "")
    diagnostics["runtime"]["acestep_lm_model_path_env"] = os.environ.get("ACESTEP_LM_MODEL_PATH", "")
    diagnostics["runtime"]["ace_step_pipeline"] = str(acestep_api["import_path"])
    diagnostics["runtime"]["torch"] = torch_runtime_snapshot(torch)
    print_device_summary(diagnostics["runtime"])
    if args.check_only:
        diagnostics["status"] = "check_only_completed"
        diagnostics["duration_seconds"] = round(time.monotonic() - started_at, 3)
        diagnostics["resources"]["after"] = resource_snapshot()
        write_diagnostics(diagnostics_path, diagnostics)
        print_check("check-only", True, "validacion terminada sin cargar modelo ni generar audio")
        print(f"Diagnostico ACE-Step guardado: {diagnostics_path}")
        return 0
    try:
        os.environ["ACESTEP_CHECKPOINTS_DIR"] = str(checkpoint_path)
        config_path = resolve_acestep_v15_config_path(checkpoint_path, args.config_path)
        dtype_patch_applied = patch_transformers_dtype_kwarg_for_acestep()
        cache_patch_applied = patch_transformers_dynamic_cache_for_acestep()
        handler = AceStepHandler()
        init_status, enable_generate = handler.initialize_service(
            project_root=str(PROJECT_ROOT),
            config_path=config_path,
            device=str(device_selection.get("active_device", "cpu")),
            use_flash_attention=False,
            compile_model=False,
            offload_to_cpu=truthy(args.cpu_offload),
            offload_dit_to_cpu=truthy(args.cpu_offload),
            quantization=None,
            prefer_source=os.getenv("ACESTEP_DOWNLOAD_SOURCE") or None,
            use_mlx_dit=False,
        )
        diagnostics["runtime"]["ace_step_init"] = {
            "status": init_status,
            "enable_generate": bool(enable_generate),
            "config_path": config_path,
            "checkpoints_dir": str(checkpoint_path),
            "lm_model_path": os.environ.get("ACESTEP_LM_MODEL_PATH", ""),
            "lm_backend": os.environ.get("ACESTEP_LM_BACKEND", ""),
            "pytorch_device": os.environ.get("PYTORCH_DEVICE", ""),
            "torch_compile_backend": os.environ.get("TORCH_COMPILE_BACKEND", ""),
            "transformers_dtype_patch_applied": dtype_patch_applied,
            "transformers_dynamic_cache_patch_applied": cache_patch_applied,
        }
        if not enable_generate:
            raise RuntimeError(f"ACE-Step 1.5 no pudo inicializar: {init_status}")
        diagnostics["status"] = "pipeline_loaded"
        diagnostics["resources"]["after_pipeline_load"] = resource_snapshot()
        diagnostics["runtime"]["torch_after_pipeline_load"] = torch_runtime_snapshot(torch)
        diagnostics["runtime"]["pipeline_device_snapshot"] = pipeline_device_snapshot(handler)
        write_diagnostics(diagnostics_path, diagnostics)
        print_check("pipeline", True, f"AceStepHandler inicializado: {init_status}")
        print_pipeline_device_summary(diagnostics["runtime"])

        print_check("generation", True, f"iniciando {args.duration}s infer_step={args.infer_step} oss_steps={args.oss_steps}")
        result = handler.generate_music(
            captions=prompt,
            global_caption="",
            lyrics=lyrics,
            inference_steps=args.infer_step,
            guidance_scale=args.guidance_scale,
            use_random_seed=False,
            seed=args.seed,
            audio_duration=args.duration,
            task_type="text2music",
            infer_method="ode",
            sampler_mode=args.scheduler_type,
            cfg_interval_start=0.0,
            cfg_interval_end=1.0,
            use_tiled_decode=truthy(args.overlapped_decode),
        )
        save_acestep_v15_audio(result, output_path)
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
    print_check("output wav", True, f"{output_path} ({output_path.stat().st_size} bytes)")
    print(f"Diagnostico ACE-Step guardado: {diagnostics_path}")
    print(f"Cancion completa generada con ACE-Step: {output_path}")
    return 0


def print_check(name: str, ok: bool, detail: str = "") -> None:
    status = "OK" if ok else "FAIL"
    suffix = f" - {detail}" if detail else ""
    print(f"[{status}] {name}{suffix}", flush=True)


def torch_debug_snapshot(torch_module: object) -> dict[str, object]:
    xpu = getattr(torch_module, "xpu", None)
    cuda = getattr(torch_module, "cuda", None)
    payload: dict[str, object] = {
        "sys_executable": sys.executable,
        "torch_version": str(getattr(torch_module, "__version__", "")),
        "torch_file": str(getattr(torch_module, "__file__", "")),
        "has_xpu": xpu is not None,
        "xpu_is_available": False,
        "xpu_device_count": 0,
        "xpu_current_device": None,
        "xpu_device_name": "",
        "cuda_is_available": False,
        "cuda_device_count": 0,
    }
    if xpu is not None:
        try:
            payload["xpu_is_available"] = bool(xpu.is_available())
        except Exception as error:
            payload["xpu_is_available_error"] = str(error)
        try:
            payload["xpu_device_count"] = int(xpu.device_count())
        except Exception as error:
            payload["xpu_device_count_error"] = str(error)
        if payload["xpu_is_available"]:
            try:
                payload["xpu_current_device"] = int(xpu.current_device())
            except Exception as error:
                payload["xpu_current_device_error"] = str(error)
            try:
                get_name = getattr(xpu, "get_device_name", None)
                if callable(get_name):
                    payload["xpu_device_name"] = str(get_name(0))
            except Exception as error:
                payload["xpu_device_name_error"] = str(error)
    if cuda is not None:
        try:
            payload["cuda_is_available"] = bool(cuda.is_available())
            payload["cuda_device_count"] = int(cuda.device_count())
        except Exception as error:
            payload["cuda_error"] = str(error)
    return payload


def print_torch_debug(payload: dict[str, object]) -> None:
    print_check("python executable", True, str(payload.get("sys_executable", "")))
    print_check("torch import", True, f"{payload.get('torch_version', '')} from {payload.get('torch_file', '')}")
    print_check("torch.xpu exists", bool(payload.get("has_xpu")), str(payload.get("has_xpu")))
    print_check("torch.xpu.is_available", bool(payload.get("xpu_is_available")), str(payload.get("xpu_is_available")))
    print_check("torch.xpu.device_count", int(payload.get("xpu_device_count") or 0) > 0, str(payload.get("xpu_device_count")))
    if payload.get("xpu_device_name"):
        print_check("torch.xpu.device_name", True, str(payload.get("xpu_device_name")))


def preload_torch_companions() -> dict[str, object]:
    companions: dict[str, object] = {}
    for module_name in ("torchvision",):
        try:
            module = __import__(module_name)
            companions[module_name] = {
                "importable": True,
                "version": str(getattr(module, "__version__", "")),
                "file": str(getattr(module, "__file__", "")),
            }
            print_check(f"{module_name} import", True, f"{companions[module_name]['version']} from {companions[module_name]['file']}")
        except Exception as error:
            companions[module_name] = {
                "importable": False,
                "error": str(error),
            }
            print_check(f"{module_name} import", False, str(error))
    return companions


def load_acestep_api() -> dict[str, object]:
    if importlib.util.find_spec("acestep") is None:
        return {
            "available": False,
            "kind": "not_installed",
            "message": "ACE-Step no esta instalado en el .venv.",
            "import_path": "",
            "handler_class": None,
        }
    try:
        module = importlib.import_module("acestep.acestep_v15_pipeline")
    except ModuleNotFoundError as error:
        missing_name = str(getattr(error, "name", "")) or str(error)
        if missing_name.startswith("acestep"):
            return {
                "available": False,
                "kind": "old_api_or_missing_v15_module",
                "message": "ACE-Step instalado, pero no expone acestep.acestep_v15_pipeline.",
                "import_path": "acestep.acestep_v15_pipeline",
                "handler_class": None,
            }
        return {
            "available": False,
            "kind": "missing_dependency",
            "message": f"Dependencia faltante al importar ACE-Step: {missing_name}",
            "import_path": "acestep.acestep_v15_pipeline",
            "handler_class": None,
        }
    except ImportError as error:
        return {
            "available": False,
            "kind": "dependency_or_api_error",
            "message": f"ACE-Step instalado, pero fallo una importacion: {error}",
            "import_path": "acestep.acestep_v15_pipeline",
            "handler_class": None,
        }
    except Exception as error:
        return {
            "available": False,
            "kind": "dependency_or_runtime_error",
            "message": f"ACE-Step instalado, pero fallo al importar su API real: {error}",
            "import_path": "acestep.acestep_v15_pipeline",
            "handler_class": None,
        }
    handler_class = getattr(module, "AceStepHandler", None)
    if handler_class is None:
        legacy_available = False
        try:
            legacy_module = importlib.import_module("acestep.pipeline_ace_step")
            legacy_available = hasattr(legacy_module, "ACEStepPipeline")
        except Exception:
            legacy_available = False
        return {
            "available": False,
            "kind": "api_incompatible",
            "message": (
                "ACE-Step instalado, pero la API real no expone AceStepHandler. "
                f"API antigua ACEStepPipeline disponible={legacy_available}."
            ),
            "import_path": "acestep.acestep_v15_pipeline",
            "handler_class": None,
        }
    return {
        "available": True,
        "kind": "v15_handler",
        "message": "API real detectada: acestep.acestep_v15_pipeline.AceStepHandler",
        "import_path": "acestep.acestep_v15_pipeline.AceStepHandler",
        "handler_class": handler_class,
    }


def resolve_acestep_v15_config_path(checkpoint_path: Path, configured_value: str = "") -> str:
    configured = (configured_value or os.getenv("ACESTEP_CONFIG_PATH", "")).strip()
    if configured:
        return configured
    name = checkpoint_path.name.lower()
    if "xl" in name and "turbo" in name:
        return "acestep-v15-xl-turbo"
    if "xl" in name and "sft" in name:
        return "acestep-v15-xl-sft"
    if "xl" in name:
        return "acestep-v15-xl-base"
    if "sft" in name:
        return "acestep-v15-sft"
    if "base" in name or "3.5" in name or "default" in name:
        return "acestep-v15-base"
    return "acestep-v15-turbo"


def save_acestep_v15_audio(result: dict[str, object], output_path: Path) -> None:
    if not bool(result.get("success")):
        raise RuntimeError(str(result.get("error") or result.get("status_message") or "ACE-Step genero un resultado fallido."))
    audios = list(result.get("audios") or [])
    if not audios:
        raise RuntimeError("ACE-Step no devolvio audios en el payload.")
    first = dict(audios[0])
    tensor = first.get("tensor")
    sample_rate = int(first.get("sample_rate") or 48000)
    if tensor is None:
        raise RuntimeError("ACE-Step devolvio audio sin tensor.")
    try:
        import soundfile as sf
    except ImportError as error:
        raise RuntimeError("Falta soundfile para guardar el WAV devuelto por ACE-Step 1.5.") from error
    audio = tensor.detach().cpu().float().numpy()
    if audio.ndim == 2:
        audio = audio.T
    output_path.parent.mkdir(parents=True, exist_ok=True)
    sf.write(str(output_path), audio, sample_rate)


def print_device_summary(runtime: dict[str, object]) -> None:
    active = str(runtime.get("active_device", ""))
    requested = str(runtime.get("requested_device", ""))
    fallback = str(runtime.get("fallback_reason", ""))
    torch_info = dict(runtime.get("torch", {}))
    details = [
        f"requested={requested}",
        f"active={active}",
        f"torch={torch_info.get('torch_version', '')}",
        f"xpu={torch_info.get('xpu_available', False)}",
        f"cuda={torch_info.get('cuda_available', False)}",
    ]
    if fallback:
        details.append(f"fallback={fallback}")
    print_check("device selection", active in {"xpu", "cuda", "cpu"}, " ".join(details))
    if active in {"xpu", "cuda"}:
        print_check("gpu backend", True, f"ACE-Step intentara usar {active}")
    else:
        print_check("gpu backend", False, "no hay GPU activa; se usaria CPU si no exiges device")


def print_pipeline_device_summary(runtime: dict[str, object]) -> None:
    active = str(runtime.get("active_device", ""))
    snapshot = dict(runtime.get("pipeline_device_snapshot", {}))
    counts = dict(snapshot.get("parameter_device_counts", {}))
    if not counts:
        print_check("pipeline devices", False, "no se pudieron inspeccionar parametros del pipeline")
        return
    detail = ", ".join(f"{device}:{count}" for device, count in sorted(counts.items()))
    init = dict(runtime.get("ace_step_init", {}))
    offload_enabled = "Offload to CPU: True" in str(init.get("status", ""))
    if active == "xpu" and offload_enabled and "cpu" in counts:
        print_check("pipeline devices", True, f"{detail} (CPU offload activo; DiT se carga temporalmente en XPU)")
        return
    print_check("pipeline devices", active in counts, detail)


def truthy(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "on"}


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


def configure_official_xpu_environment(args: argparse.Namespace) -> None:
    requested_device = str(getattr(args, "device", "auto") or "auto").strip().lower()
    if requested_device in {"auto", "xpu"}:
        os.environ.setdefault("PYTORCH_DEVICE", "xpu")
        os.environ.setdefault("SYCL_CACHE_PERSISTENT", "1")
        os.environ.setdefault("SYCL_PI_LEVEL_ZERO_USE_IMMEDIATE_COMMANDLISTS", "1")
        os.environ.setdefault("TORCH_COMPILE_BACKEND", "eager")
        os.environ.setdefault("ACESTEP_CONFIG_PATH", str(getattr(args, "config_path", "acestep-v15-turbo")))
        os.environ.setdefault("ACESTEP_LM_BACKEND", "pt")
        os.environ.setdefault("ACESTEP_LM_MODEL_PATH", str(getattr(args, "lm_model_path", "acestep-5Hz-lm-0.6B")))
        os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")


def apply_torch_thread_settings(torch_module: object) -> None:
    try:
        torch_module.set_num_threads(int(os.environ["TORCH_NUM_THREADS"]))
        torch_module.set_num_interop_threads(int(os.environ["TORCH_INTEROP_THREADS"]))
    except Exception:
        pass


def configure_accelerator_environment(args: argparse.Namespace, selection: dict[str, object]) -> None:
    active_device = str(selection.get("active_device", "cpu"))
    os.environ["ACESTEP_DEVICE"] = active_device
    os.environ["ACESTEP_LM_DEVICE"] = active_device
    
    if active_device == "cuda":
        os.environ["CUDA_VISIBLE_DEVICES"] = str(args.device_id)
    elif active_device == "xpu":
        os.environ["CUDA_VISIBLE_DEVICES"] = ""
        os.environ["PYTORCH_DEVICE"] = "xpu"
        os.environ["SYCL_CACHE_PERSISTENT"] = "1"
        os.environ["SYCL_PI_LEVEL_ZERO_USE_IMMEDIATE_COMMANDLISTS"] = "1"
        os.environ["TORCH_COMPILE_BACKEND"] = "eager"
        os.environ.setdefault("ACESTEP_LM_BACKEND", "pt")
        os.environ.setdefault("ACESTEP_CONFIG_PATH", str(getattr(args, "config_path", "acestep-v15-turbo")))
        os.environ.setdefault("ACESTEP_LM_MODEL_PATH", str(getattr(args, "lm_model_path", "acestep-5Hz-lm-0.6B")))
        # Forzamos el offload a true para que la iGPU Intel no colapse la RAM
        os.environ["ACESTEP_OFFLOAD_TO_CPU"] = "true"
        os.environ["ACESTEP_OFFLOAD_DIT_TO_CPU"] = "true"
    else:
        os.environ["CUDA_VISIBLE_DEVICES"] = ""

def torch_runtime_snapshot(torch_module: object) -> dict[str, object]:
    cuda = getattr(torch_module, "cuda", None)
    xpu = getattr(torch_module, "xpu", None)
    cuda_available = bool(cuda and cuda.is_available())
    gpu_name = ""
    if cuda_available:
        try:
            gpu_name = str(cuda.get_device_name(0))
        except Exception:
            gpu_name = ""
    xpu_available = False
    xpu_name = ""
    xpu_current_device = None
    if xpu is not None:
        try:
            xpu_available = bool(xpu.is_available())
            if xpu_available:
                xpu_current_device = int(xpu.current_device())
                name_func = getattr(xpu, "get_device_name", None)
                props_func = getattr(xpu, "get_device_properties", None)
                if callable(name_func):
                    xpu_name = str(name_func(0))
                elif callable(props_func):
                    props = props_func(0)
                    xpu_name = str(getattr(props, "name", props))
        except Exception:
            xpu_available = False
    return {
        "torch_version": str(getattr(torch_module, "__version__", "")),
        "cuda_available": cuda_available,
        "cuda_device_count": int(cuda.device_count()) if cuda else 0,
        "cuda_device_name": gpu_name,
        "xpu_api_available": xpu is not None,
        "xpu_available": xpu_available,
        "xpu_device_count": int(xpu.device_count()) if xpu and xpu_available else 0,
        "xpu_current_device": xpu_current_device,
        "xpu_device_name": xpu_name,
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
    device = getattr(args, "device", "auto")
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
            "requested_device": device,
            "active_device": "",
            "backend_active": "",
            "fallback_reason": "",
            "cuda_visible_devices": "",
            "acestep_device_env": "",
            "acestep_lm_device_env": "",
            "pytorch_device_env": "",
            "sycl_cache_persistent": "",
            "sycl_immediate_commandlists": "",
            "torch_compile_backend": "",
            "acestep_config_path_env": "",
            "acestep_lm_backend_env": "",
            "acestep_lm_model_path_env": "",
            "ace_step_pipeline": "",
            "torch": {},
            "torch_debug": {},
            "torch_companions": {},
            "pipeline_device_snapshot": {},
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
        "intel_gpu": intel_gpu_snapshot(),
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
    snapshot["intel_gpu"] = intel_gpu_snapshot()
    return snapshot


def pipeline_device_snapshot(pipeline: object) -> dict[str, object]:
    found: dict[str, int] = {}
    visited: set[int] = set()

    def visit(value: object, depth: int = 0) -> None:
        if depth > 3 or id(value) in visited or len(visited) > 200:
            return
        visited.add(id(value))
        parameters = getattr(value, "parameters", None)
        if callable(parameters):
            try:
                for parameter in parameters():
                    device = getattr(parameter, "device", None)
                    if device is not None:
                        key = str(getattr(device, "type", device))
                        found[key] = found.get(key, 0) + 1
                        if sum(found.values()) >= 24:
                            return
            except Exception:
                pass
        for name in ("model", "dit", "vae", "text_encoder", "lm", "pipeline"):
            child = getattr(value, name, None)
            if child is not None:
                visit(child, depth + 1)

    visit(pipeline)
    return {"parameter_device_counts": found, "objects_visited": len(visited)}


def intel_gpu_snapshot() -> list[dict[str, object]]:
    powershell = shutil.which("powershell") or shutil.which("pwsh")
    if powershell is None:
        return []
    command = [
        powershell,
        "-NoProfile",
        "-Command",
        "Get-Counter '\\GPU Engine(*)\\Utilization Percentage' -ErrorAction SilentlyContinue | "
        "Select-Object -ExpandProperty CounterSamples | "
        "Where-Object {$_.InstanceName -match 'intel|render|compute|copy|3d'} | "
        "Select-Object -First 12 InstanceName,CookedValue | ConvertTo-Json -Compress",
    ]
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=False, timeout=5)
    except Exception:
        return []
    if result.returncode != 0 or not result.stdout.strip():
        return []
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError:
        return []
    rows = payload if isinstance(payload, list) else [payload]
    return [
        {
            "name": str(row.get("InstanceName", ""))[:160],
            "utilization_percent": parse_float(str(row.get("CookedValue", 0))),
        }
        for row in rows
        if isinstance(row, dict)
    ]


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
