"""Open the local app only after the foreground launcher serves its page."""

import sys
import time
import urllib.error
import urllib.request
import webbrowser


def main() -> int:
    url = sys.argv[1]
    if not url.startswith("http://127.0.0.1:") or not url.endswith("/"):
        return 2
    for _ in range(120):
        try:
            with urllib.request.urlopen(url, timeout=2) as response:
                if response.status == 200 and "text/html" in response.headers.get("Content-Type", ""):
                    webbrowser.open(url)
                    return 0
        except (OSError, urllib.error.URLError):
            pass
        time.sleep(1)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
