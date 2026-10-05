"""Approval is tied to the exact candidate; it never authorizes final audio."""
from typing import Protocol


class PlanRepository(Protocol):
    def save(self, song_id: str, plan: dict) -> dict: ...
    def get(self, song_id: str, plan_id: str) -> dict | None: ...
    def approve(self, song_id: str, plan_id: str, revision_id: str, sha256: str) -> dict: ...
    def latest(self, song_id: str) -> dict | None: ...


class ReviewAceStepPlan:
    def __init__(self, preview, repository: PlanRepository):
        self.preview = preview
        self.repository = repository

    def prepare(self, song_id: str, lyrics: str) -> dict:
        return self.repository.save(song_id, self.preview.execute(song_id, lyrics))

    def latest(self, song_id: str) -> dict | None:
        item = self.repository.latest(song_id)
        if item is None:
            return None
        try:
            current = self.preview.execute(song_id, item["plan"]["payload"]["lyrics"])
            item["inputs_current"] = current["plan_sha256"] == item["plan"]["plan_sha256"]
            item["invalid_reason"] = "" if item["inputs_current"] else "Los inputs cambiaron; prepara un nuevo plan."
        except ValueError as error:
            item["inputs_current"] = False
            item["invalid_reason"] = str(error)
        item["effective_status"] = item["status"] if item["inputs_current"] else "stale"
        item["ready_for_execution"] = False
        return item

    def approve(self, song_id: str, plan_id: str, request: dict) -> dict:
        item = self.repository.get(song_id, plan_id)
        if not item or request.get("plan_sha256") != item["plan"]["plan_sha256"]:
            raise ValueError("Revisa el plan vigente antes de aprobarlo.")
        if request.get("lyrics_confirmed") is not True:
            raise ValueError("Confirma la letra mostrada en este plan antes de aprobarlo.")
        current = self.preview.execute(song_id, item["plan"]["payload"]["lyrics"])
        if current["plan_sha256"] != item["plan"]["plan_sha256"]:
            raise ValueError("Los inputs del plan cambiaron; prepara y revisa uno nuevo.")
        if "source_artifact_verification" in current["pending"]:
            raise ValueError("Selecciona y verifica el artefacto fuente antes de aprobar el plan.")
        return self.repository.approve(song_id, plan_id, current["spec_revision_id"], current["plan_sha256"])
