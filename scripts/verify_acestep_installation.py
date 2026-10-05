"""Verify local Base weights without importing models or allocating tensors."""
import argparse
import hashlib
import json
from pathlib import Path
import struct


def verify(root: Path, expected: str, revision: str) -> dict:
    base = root / "acestep-v15-base"
    required = ("config.json", "configuration_acestep_v15.py", "modeling_acestep_v15_base.py",
                "apg_guidance.py", "silence_latent.pt", "model.safetensors")
    for filename in required:
        path = base / filename
        if not path.is_file() or path.stat().st_size == 0:
            raise ValueError(f"Falta archivo Base completo: {filename}")
    for component, filename in (("vae", "diffusion_pytorch_model.safetensors"),
                                ("Qwen3-Embedding-0.6B", "model.safetensors")):
        path = root / component / filename
        if not path.is_file() or path.stat().st_size == 0:
            raise ValueError(f"Faltan pesos compartidos: {component}")
    weight = base / "model.safetensors"
    digest = hashlib.sha256()
    with weight.open("rb") as source:
        while chunk := source.read(1024 * 1024):
            digest.update(chunk)
    actual = digest.hexdigest()
    if actual != expected:
        raise ValueError("El SHA-256 de Base no coincide con el esperado de la descarga oficial.")
    with weight.open("rb") as source:
        header_length = struct.unpack("<Q", source.read(8))[0]
        if header_length > 100_000_000 or header_length > weight.stat().st_size - 8:
            raise ValueError("Cabecera safetensors invalida.")
        header = json.loads(source.read(header_length))
    tensors = [value for key, value in header.items() if key != "__metadata__"]
    data_length = weight.stat().st_size - 8 - header_length
    if not tensors or any(not 0 <= value["data_offsets"][0] <= value["data_offsets"][1] <= data_length
                          for value in tensors):
        raise ValueError("Offsets safetensors invalidos.")
    config = json.loads((base / "config.json").read_text(encoding="utf-8"))
    return {"repo": "ACE-Step/acestep-v15-base", "revision": revision,
            "root": str(root), "config_path": "acestep-v15-base", "architecture": config.get("architectures"),
            "weight_bytes": weight.stat().st_size, "weight_sha256": actual, "tensor_entries": len(tensors),
            "base_weight_checksum_verified": True, "shared_weights_present": True,
            "shared_weights_checksum_verified": False, "model_loaded_verified": False,
            "generation_verified": False, "quality_verified": False}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--expected-weight-sha256", required=True)
    parser.add_argument("--revision", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = verify(args.root, args.expected_weight_sha256, args.revision)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result))
