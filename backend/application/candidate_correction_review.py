"""Explicit technical handoff for a persisted correction; never applies model output."""
from datetime import datetime, timezone


class ReviewCandidateCorrection:
    def __init__(self, store, corrections, orchestrator, project_context):
        self.store, self.corrections = store, corrections
        self.orchestrator, self.project_context = orchestrator, project_context

    def execute(self, song_id, task_id, request):
        if request.get("review_requested") is not True:
            raise ValueError("Solicita explicitamente la revision tecnica de la propuesta.")
        proposal = self.corrections.latest(song_id, task_id).get("proposal")
        if (not proposal or proposal.get("inputs_current") is not True
                or proposal["created_at"] != request.get("proposal_created_at")):
            raise ValueError("Recarga y revisa una propuesta vigente antes de solicitar asistencia tecnica.")
        # Prior review output is history, not fresh creative input; avoid recursive handoff payloads.
        proposal = {key: value for key, value in proposal.items() if key != "technical_review"}
        project = self.store.get_song_project(song_id)
        owner = str((project or {}).get("user_id", ""))
        if not owner.startswith("set:") or not owner[4:].strip():
            raise ValueError("Vincula el proyecto a un set con sus tres piezas antes de solicitar esta revision.")
        context = self.project_context(owner[4:].strip())
        assets = context["assets"]
        handoff = self.orchestrator.run_handoff({"model_role": "technical", "task_type": "candidate_correction_review",
            "phase": "technical_review", "project_id": context["project"]["project_id"],
            "project_name": context["project"]["project_name"], "description": proposal["notes"], "question": proposal["notes"],
            "context": {"project": context["project"], "set": context["set"],
                "assets": assets, "instrumental_intent": assets["instrumental"].get("intent", {}),
                "vocal_intent": assets["melody"].get("intent", {}), "lyrical_intent": assets["lyrics"].get("intent", {}),
                "spec": project.get("spec", {}), "correction": proposal,
                "creative_changes_require_user_review": True, "apply_changes": False}})
        latest = self.corrections.latest(song_id, task_id).get("proposal")
        current = bool(latest and latest.get("inputs_current") is True and latest["created_at"] == proposal["created_at"])
        result = {"task_id": task_id, "proposal_created_at": proposal["created_at"], "handoff": handoff,
                  "inputs_current_at_completion": current, "changes_applied": False,
                  "reviewed_at": datetime.now(timezone.utc).isoformat()}
        self.store.create_song_event(song_id=song_id, phase="SONG_SPEC_COLLECTION", status="completed", progress=100,
            active_model="technical", message="Revision tecnica registrada; propuestas pendientes de revision del usuario.",
            payload={"candidate_correction_technical_review": result}, artifact_id=proposal["artifact_id"])
        return {"review": result}
