from __future__ import annotations

import argparse
import http.client
import json
import socket
from pathlib import Path


SOCKET_PATH = "/var/run/docker.sock"
DEFAULT_CONTAINERS = ("song-ai-llama-gemma", "song-ai-llama-qwen")


class UnixSocketHTTPConnection(http.client.HTTPConnection):
    def __init__(self, socket_path: str) -> None:
        super().__init__("localhost")
        self.socket_path = socket_path

    def connect(self) -> None:
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.connect(self.socket_path)
        self.sock = sock


def docker_request(method: str, path: str) -> tuple[int, str]:
    connection = UnixSocketHTTPConnection(SOCKET_PATH)
    try:
        connection.request(method, path)
        response = connection.getresponse()
        body = response.read().decode("utf-8", errors="replace")
        return response.status, body
    finally:
        connection.close()


def container_state(name: str) -> str:
    status, body = docker_request("GET", f"/containers/{name}/json")
    if status == 404:
        return "missing"
    if status >= 300:
        return f"error:{status}"
    payload = json.loads(body)
    return "running" if bool(payload.get("State", {}).get("Running")) else "stopped"


def manage(action: str, containers: tuple[str, ...]) -> int:
    if not Path(SOCKET_PATH).exists():
        print(f"Docker socket no disponible en {SOCKET_PATH}; se omite gestion de LLM.")
        return 0
    for name in containers:
        state = container_state(name)
        if action == "stop":
            if state != "running":
                print(f"{name}: {state}, no requiere stop.")
                continue
            status, body = docker_request("POST", f"/containers/{name}/stop?t=30")
        else:
            if state == "running":
                print(f"{name}: running, no requiere start.")
                continue
            if state == "missing":
                print(f"{name}: missing, no se puede iniciar.")
                continue
            status, body = docker_request("POST", f"/containers/{name}/start")
        if status not in {204, 304}:
            print(f"{name}: {action} devolvio {status} {body[:240]}")
        else:
            print(f"{name}: {action} ok.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Pausa o restaura contenedores LLM locales de Song AI.")
    parser.add_argument("action", choices=["stop", "start"])
    parser.add_argument("--containers", default=",".join(DEFAULT_CONTAINERS))
    args = parser.parse_args()
    containers = tuple(item.strip() for item in args.containers.split(",") if item.strip())
    return manage(args.action, containers or DEFAULT_CONTAINERS)


if __name__ == "__main__":
    raise SystemExit(main())
