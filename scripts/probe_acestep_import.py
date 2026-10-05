"""Import-only ACE-Step check in an isolated process; never instantiate handler."""
import contextlib
import importlib.util
import io
import json
import os
import sys
import threading
import time
from pathlib import Path

root = Path(__file__).resolve().parents[1]
result = {"import_verified": False, "generation_verified": False, "weights_loaded": False}
started = time.monotonic()
stage = "wrapper_import"


def timed_out() -> None:
    frame = sys._current_frames().get(threading.main_thread().ident)
    frames = []
    while frame is not None:
        frames.append({"file": Path(frame.f_code.co_filename).name,
                       "function": frame.f_code.co_name, "line": frame.f_lineno})
        frame = frame.f_back
    payload = {**result, "status": "timeout", "stage": stage,
               "elapsed_seconds": round(time.monotonic() - started, 2), "stack": frames[:12]}
    sys.__stdout__.write(json.dumps(payload) + "\n")
    sys.__stdout__.flush()
    os._exit(2)


watchdog = threading.Timer(55, timed_out)
watchdog.daemon = True
watchdog.start()
try:
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        spec = importlib.util.spec_from_file_location("studio_acestep_wrapper", root / "tools" / "acestep_generate.py")
        wrapper = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(wrapper)
        stage = "acestep_api_import"
        api = wrapper.load_acestep_api()
    result.update({"status": "imported" if api["available"] else "import_error",
                   "import_verified": bool(api["available"]), "kind": api["kind"], "import_path": api["import_path"]})
except Exception as error:
    result["status"] = "probe_error"
    result["error_type"] = type(error).__name__
finally:
    watchdog.cancel()
result["elapsed_seconds"] = round(time.monotonic() - started, 2)
print(json.dumps(result))
