"""Port for versioned engine guidance supplied by the composition root."""
from typing import Protocol


class ModelSteering(Protocol):
    def snapshot(self, role: str) -> dict[str, object]: ...
