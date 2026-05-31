from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = PROJECT_ROOT / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from audio.accelerator_detection import torch_accelerator_snapshot


def main() -> int:
    parser = argparse.ArgumentParser(description="Verifica el stack Intel XPU para Song-AI/ACE-Step.")
    parser.add_argument("--json", action="store_true", help="Imprime solo JSON.")
    parser.add_argument(
        "--probe-tensor",
        action="store_true",
        help="Ejecuta una prueba tensorial en torch.device('xpu') si XPU esta disponible.",
    )
    args = parser.parse_args()

    payload = {
        "schema": "song-ai-xpu-stack-v1",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "accelerators": torch_accelerator_snapshot(run_tensor_probe=args.probe_tensor),
    }
    if args.json:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return 0

    accel = dict(payload["accelerators"])
    print("Song-AI Intel XPU check")
    print("=======================")
    print(f"torch importable: {accel['torch_importable']} ({accel['torch_version']})")
    print(f"torch.xpu API: {accel['xpu_api_available']}")
    print(f"torch.xpu available: {accel['xpu_available']}")
    print(f"XPU devices: {accel['xpu_device_count']} {accel['xpu_device_name']}")
    print(f"torch.xpu.current_device(): {accel['xpu_current_device']}")
    print(f"intel_extension_for_pytorch importable: {accel['ipex_importable']}")
    print(f"soundfile importable: {accel['soundfile_importable']}")
    print(f"torchcodec importable: {accel['torchcodec_importable']}")
    print(f"CUDA available: {accel['cuda_available']} {accel['cuda_device_name']}")
    print(f"Backend recomendado: {accel['recommended_backend']}")
    if accel.get("probe_ok") is not None:
        print(f"Prueba tensorial XPU: {accel['probe_ok']}")
    if accel.get("fallback_reason"):
        print(f"Motivo fallback: {accel['fallback_reason']}")
    if accel.get("probe_error"):
        print("Detalle tecnico:")
        print(accel["probe_error"])
    return 0 if accel.get("torch_importable") else 1


if __name__ == "__main__":
    raise SystemExit(main())
