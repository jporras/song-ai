"""Bounded hardware probe. Does not import ACE-Step, load weights or allocate tensors."""
import json
import platform
import sys

result = {"python": sys.executable, "platform": platform.platform(), "torch": None, "devices": {}}
try:
    import torch
    result["torch"] = torch.__version__
    for name in ("cuda", "xpu"):
        device_api = getattr(torch, name, None)
        try:
            available = bool(device_api and device_api.is_available())
            count = device_api.device_count() if available else 0
            result["devices"][name] = {
                "available": available, "count": count,
                "names": [device_api.get_device_name(index) for index in range(count)],
                "tensor_execution_verified": False,
            }
        except Exception as error:
            result["devices"][name] = {"available": None, "error_type": type(error).__name__}
except Exception as error:
    result["error_type"] = type(error).__name__
print(json.dumps(result))
