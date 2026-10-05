"""Template evidence only: event bindings are not proof of audible processing."""
from html.parser import HTMLParser
from pathlib import Path


class ControlParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.controls: list[dict[str, object]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        bindings = {key: value for key, value in attrs if key.startswith(("v-model", "@"))}
        if tag not in {"button", "input", "select", "textarea", "audio"} or not bindings:
            return
        self.controls.append({
            "audit_id": f"frontend/index.html:{self.getpos()[0]}:{len(self.controls)}",
            "line": self.getpos()[0], "tag": tag, "bindings": bindings,
            "disabled_expression": attributes.get(":disabled"),
            "visibility_expression": attributes.get("v-if", attributes.get("v-else-if")),
            "status": "PARTIAL", "engine": "unverified",
            "reason": "Template binding found; handler and engine semantics require explicit tracing.",
        })


def audit_controls(root: Path) -> list[dict[str, object]]:
    path = root / "frontend" / "index.html"
    parser = ControlParser()
    if path.exists():
        parser.feed(path.read_text(encoding="utf-8"))
    return parser.controls
