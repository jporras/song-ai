import json
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import build_opener, ProxyHandler, HTTPRedirectHandler


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def probe_runtime(root: Path, urls: dict[str, str]) -> dict[str, object]:
    result: dict[str, object] = {"hardware": {}, "servers": {}}
    try:
        completed = subprocess.run(
            [sys.executable, str(root / "scripts" / "probe_studio_runtime.py")],
            capture_output=True, text=True, timeout=30, check=False,
        )
        if completed.returncode == 0:
            result["hardware"] = json.loads(completed.stdout)
        else:
            result["hardware"] = {"status": "failed", "returncode": completed.returncode}
    except (subprocess.TimeoutExpired, OSError, ValueError):
        result["hardware"] = {"status": "failed_or_timeout"}
    opener = build_opener(ProxyHandler({}), NoRedirect())
    servers = {}
    for role, base in urls.items():
        parsed = urlsplit(base)
        if (parsed.scheme not in {"http", "https"} or parsed.hostname not in {"localhost", "127.0.0.1", "::1"}
                or parsed.username or parsed.password):
            servers[role] = {"available": None, "reason": "Only explicit loopback servers are probed."}
            continue
        try:
            with opener.open(base.rstrip("/") + "/health", timeout=2) as response:
                payload = json.loads(response.read(65536))
            servers[role] = {"available": payload.get("status") == "ok",
                             "health_status": payload.get("status"), "inference_verified": False}
        except Exception as error:
            servers[role] = {"available": False, "error_type": type(error).__name__,
                             "inference_verified": False}
    result["servers"] = servers
    return result
