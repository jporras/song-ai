"""User feedback bound to an exact candidate; independent of sample/final approval."""
from datetime import datetime, timezone
from application.listening_feedback import validate_listening_feedback


class ReviewCandidateListening:
    def __init__(self, store, jobs, verify_audio):
        self.store, self.jobs, self.verify_audio = store, jobs, verify_audio

    def execute(self, song_id: str, task_id: str, request: dict) -> dict:
        decision, notes = validate_listening_feedback(request)
        checksum = request.get("audio_sha256", "")
        self.verify_audio(song_id, task_id, checksum)
        task = self.jobs.get(song_id, task_id)
        artifact = task["result"]["artifact"]
        checks = artifact.get("metadata", {}).get("fidelity_report", task["result"].get("fidelity_report", {})).get("checks", [])
        allowed = {check["id"] for check in checks if check.get("method") == "not_measured"}
        criteria = request.get("criteria", {})
        if not isinstance(criteria, dict) or any(
            key not in allowed or not isinstance(value, str) or value not in {"matches", "needs_changes", "unsure"}
            for key, value in criteria.items()
        ):
            raise ValueError("Revisa los criterios disponibles para este candidato y sus respuestas.")
        if "needs_changes" in criteria.values() and (decision != "changes_requested" or not notes.strip()):
            raise ValueError("Si un aspecto necesita cambios, solicita cambios y describe que corregir.")
        review = {"task_id": task_id, "artifact_id": artifact["artifact_id"],
                  "audio_sha256": checksum, "plan_id": artifact["metadata"]["plan_id"],
                  "spec_revision_id": artifact["metadata"]["spec_revision_id"],
                  "decision": decision, "notes": notes.strip(), "listened": True,
                  "criteria": dict(criteria), "criteria_method": "user_listening",
                  "actor": "user", "reviewed_at": datetime.now(timezone.utc).isoformat(),
                  "sample_approved": False, "final_quality_verified": False}
        event = self.store.create_song_event(song_id=song_id, phase="SONG_SPEC_COLLECTION", status="completed", progress=100,
            message="Opinion de escucha del candidato registrada; no aprueba sample ni cancion final.",
            active_model="user", payload={"candidate_listening_review": review}, artifact_id=artifact["artifact_id"])
        return {"review": review, "event": event}


def listening_review_view(review: dict | None, current_plan: dict | None) -> dict | None:
    """Derive currentness without rewriting the historical user decision."""
    if review is None:
        return None
    current = bool(current_plan and current_plan.get("inputs_current") is True
                   and current_plan.get("plan_id") == review.get("plan_id")
                   and current_plan.get("plan", {}).get("spec_revision_id") == review.get("spec_revision_id"))
    return {**review, "inputs_current": current,
            "context_message": ("Opinion sobre el plan vigente." if current else
                                "Opinion sobre una version anterior. Revisa el plan actual y genera un nuevo candidato para evaluarlo.")}


class CandidateListeningContext:
    """Build assistant evidence from the selected project's persisted candidate."""
    def __init__(self, jobs, latest_review, latest_correction=None):
        self.jobs, self.latest_review = jobs, latest_review
        self.latest_correction = latest_correction

    def build(self, song_id: str) -> dict:
        if not song_id:
            return {"status": "no_project"}
        task = self.jobs.latest(song_id)
        if not task or task["status"] != "completed":
            return {"status": "no_completed_candidate"}
        review = self.latest_review(song_id, task["task_id"])["review"]
        status = "audio_unavailable" if review and review.get("audio_current") is False else "reviewed" if review else "listening_pending"
        return {"status": status, "task_id": task["task_id"],
                "review": review, "source": "sqlite_user_listening",
                "correction": self.latest_correction(song_id, task["task_id"]).get("proposal") if self.latest_correction else None,
                "sample_approved": False, "final_quality_verified": False}
