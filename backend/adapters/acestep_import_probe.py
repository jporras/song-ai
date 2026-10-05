"""Bounded subprocess evidence; no raw logs are published."""
import json
from pathlib import Path
import subprocess
import sys


def probe_acestep_import(root: Path) -> dict[str, object]:
    base = {"import_verified": False, "generation_verified": False, "weights_loaded": False}
    try:
        process = subprocess.run(
            [sys.executable, str(root / "scripts" / "probe_acestep_import.py")],
            capture_output=True, text=True, timeout=60, check=False,
        )
    except subprocess.TimeoutExpired:
        return {**base, "status": "timeout", "stage": "subprocess", "timeout_seconds": 60}
    except OSError as error:
        return {**base, "status": "launch_error", "error_type": type(error).__name__}
    try:
        result = json.loads(process.stdout)
        if not isinstance(result, dict):
            raise ValueError("Invalid probe payload")
    except ValueError:
        return {**base, "status": "invalid_payload", "returncode": process.returncode}
    allowed = {"status", "stage", "kind", "import_path", "elapsed_seconds", "stack", "error_type"}
    payload = {**base, **{key: value for key, value in result.items() if key in allowed},
               "returncode": process.returncode}
    payload["import_verified"] = (
        process.returncode == 0 and result.get("status") == "imported" and result.get("import_verified") is True
    )
    return payload
