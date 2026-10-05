from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class Capability:
    identifier: str
    engine: str
    configured: bool
    available: bool | None
    verified: bool = False
    experimental: bool = False
    reason: str = ""


class CapabilityRegistry:
    """Read-only evidence registry; configuration never proves execution."""

    def __init__(self, capabilities: list[Capability]) -> None:
        identifiers = [item.identifier for item in capabilities]
        if len(set(identifiers)) != len(identifiers):
            raise ValueError("Duplicate capability identifier.")
        if any(item.verified and (not item.configured or item.available is not True) for item in capabilities):
            raise ValueError("Verified capability requires configured and available evidence.")
        self._capabilities = {item.identifier: item for item in capabilities}

    def snapshot(self) -> list[dict[str, object]]:
        return [asdict(item) for item in self._capabilities.values()]

    def require_verified(self, identifier: str) -> Capability:
        item = self._capabilities.get(identifier)
        if item is None or not item.verified:
            raise ValueError(f"Capability not verified: {identifier}")
        return item
