from __future__ import annotations

import importlib.util
import sys
import traceback


def torch_accelerator_snapshot(run_tensor_probe: bool = False) -> dict[str, object]:
    snapshot: dict[str, object] = {
        "torch_importable": False,
        "torch_version": "",
        "cuda_available": False,
        "cuda_device_count": 0,
        "cuda_device_name": "",
        "xpu_api_available": False,
        "xpu_available": False,
        "xpu_device_count": 0,
        "xpu_current_device": None,
        "xpu_device_name": "",
        "ipex_importable": importlib.util.find_spec("intel_extension_for_pytorch") is not None,
        "soundfile_importable": importlib.util.find_spec("soundfile") is not None,
        "torchcodec_importable": importlib.util.find_spec("torchcodec") is not None,
        "recommended_backend": "cpu",
        "fallback_reason": "",
        "probe_ok": None,
        "probe_error": "",
    }
    try:
        import torch
    except Exception as error:
        snapshot["fallback_reason"] = f"torch no importable: {error}"
        snapshot["probe_error"] = traceback.format_exc()
        return snapshot

    snapshot["torch_importable"] = True
    snapshot["torch_version"] = str(getattr(torch, "__version__", ""))
    cuda = getattr(torch, "cuda", None)
    if cuda is not None:
        try:
            snapshot["cuda_available"] = bool(cuda.is_available())
            snapshot["cuda_device_count"] = int(cuda.device_count())
            if snapshot["cuda_available"]:
                snapshot["cuda_device_name"] = str(cuda.get_device_name(0))
        except Exception as error:
            snapshot["fallback_reason"] = f"CUDA probe fallo: {error}"

    xpu = getattr(torch, "xpu", None)
    snapshot["xpu_api_available"] = xpu is not None
    if xpu is not None:
        try:
            snapshot["xpu_available"] = bool(xpu.is_available())
            snapshot["xpu_device_count"] = int(xpu.device_count()) if snapshot["xpu_available"] else 0
            if snapshot["xpu_available"]:
                snapshot["xpu_current_device"] = int(xpu.current_device())
                snapshot["xpu_device_name"] = _xpu_device_name(xpu)
        except Exception as error:
            snapshot["fallback_reason"] = f"XPU probe fallo: {error}"

    if snapshot["xpu_available"]:
        snapshot["recommended_backend"] = "xpu"
    elif snapshot["cuda_available"]:
        snapshot["recommended_backend"] = "cuda"
    elif not snapshot["fallback_reason"]:
        if not snapshot["xpu_api_available"]:
            snapshot["fallback_reason"] = "torch fue instalado sin API torch.xpu; instala ruedas PyTorch XPU."
        elif not snapshot["xpu_available"]:
            snapshot["fallback_reason"] = "torch.xpu existe pero no detecta GPU Intel; revisa driver Intel y ruedas XPU."

    if run_tensor_probe and snapshot["xpu_available"]:
        try:
            tensor = torch.ones((8, 8), device="xpu")
            result = tensor @ tensor
            xpu.synchronize()
            snapshot["probe_ok"] = bool(float(result[0, 0].cpu()) == 8.0)
        except Exception as error:
            snapshot["probe_ok"] = False
            snapshot["probe_error"] = traceback.format_exc()
            snapshot["fallback_reason"] = f"torch.device('xpu') fallo en prueba tensorial: {error}"
    return snapshot


def choose_ace_device(torch_module: object, requested: str = "auto", require_device: bool = False) -> dict[str, object]:
    requested = (requested or "auto").strip().lower()
    if requested not in {"auto", "xpu", "cuda", "cpu"}:
        requested = "auto"
    snapshot = _torch_module_snapshot(torch_module)
    selected = "cpu"
    fallback_reason = ""

    if requested == "xpu":
        xpu = getattr(torch_module, "xpu", None)
        if xpu is None:
            fallback_reason = "torch.xpu no existe en este torch."
        else:
            try:
                if bool(xpu.is_available()):
                    selected = "xpu"
                else:
                    device_count = _safe_device_count(xpu)
                    fallback_reason = f"torch.xpu existe pero no esta disponible. device_count={device_count}."
            except Exception as error:
                fallback_reason = f"torch.xpu existe pero fallo al consultar disponibilidad: {error}"
    elif requested == "auto" and snapshot["xpu_available"]:
        selected = "xpu"
    elif requested in {"auto", "cuda"} and snapshot["cuda_available"] and sys.platform != "win32":
        selected = "cuda"
    elif requested == "cpu":
        selected = "cpu"
    elif requested == "cuda":
        if sys.platform == "win32":
            fallback_reason = "CUDA esta deshabilitado en Windows para esta ruta ACE-Step Intel XPU."
        else:
            fallback_reason = "CUDA solicitado pero torch.cuda no esta disponible."
    else:
        fallback_reason = str(snapshot.get("fallback_reason") or "No hay acelerador compatible; se usara CPU.")
    if require_device and requested != "auto" and selected != requested:
        raise RuntimeError(f"Dispositivo requerido '{requested}' no disponible. Motivo: {fallback_reason}")
    return {
        "requested_device": requested,
        "active_device": selected,
        "backend_active": selected,
        "fallback_reason": fallback_reason,
        "torch": snapshot,
    }


def _safe_device_count(device_module: object) -> int | str:
    try:
        return int(device_module.device_count())
    except Exception as error:
        return f"error: {error}"


def _torch_module_snapshot(torch_module: object) -> dict[str, object]:
    cuda = getattr(torch_module, "cuda", None)
    xpu = getattr(torch_module, "xpu", None)
    snapshot: dict[str, object] = {
        "torch_version": str(getattr(torch_module, "__version__", "")),
        "cuda_available": False,
        "cuda_device_count": 0,
        "cuda_device_name": "",
        "xpu_api_available": xpu is not None,
        "xpu_available": False,
        "xpu_device_count": 0,
        "xpu_current_device": None,
        "xpu_device_name": "",
        "fallback_reason": "",
    }
    if cuda is not None:
        try:
            snapshot["cuda_available"] = bool(cuda.is_available())
            snapshot["cuda_device_count"] = int(cuda.device_count())
            if snapshot["cuda_available"]:
                snapshot["cuda_device_name"] = str(cuda.get_device_name(0))
        except Exception as error:
            snapshot["fallback_reason"] = f"CUDA probe fallo: {error}"
    if xpu is not None:
        try:
            snapshot["xpu_available"] = bool(xpu.is_available())
            snapshot["xpu_device_count"] = int(xpu.device_count()) if snapshot["xpu_available"] else 0
            if snapshot["xpu_available"]:
                snapshot["xpu_current_device"] = int(xpu.current_device())
                snapshot["xpu_device_name"] = _xpu_device_name(xpu)
        except Exception as error:
            snapshot["fallback_reason"] = f"XPU probe fallo: {error}"
    if not snapshot["fallback_reason"] and not snapshot["xpu_available"]:
        snapshot["fallback_reason"] = (
            "torch.xpu no disponible."
            if snapshot["xpu_api_available"]
            else "torch fue instalado sin soporte torch.xpu."
        )
    return snapshot


def _xpu_device_name(xpu_module: object) -> str:
    for attr in ("get_device_name",):
        func = getattr(xpu_module, attr, None)
        if callable(func):
            try:
                return str(func(0))
            except Exception:
                pass
    props_func = getattr(xpu_module, "get_device_properties", None)
    if callable(props_func):
        try:
            props = props_func(0)
            return str(getattr(props, "name", props))
        except Exception:
            pass
    return "Intel XPU"
