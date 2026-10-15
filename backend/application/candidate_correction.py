"""Persist an explicit correction request without changing approved musical inputs."""
import math
from datetime import datetime, timezone
from models.ace_step_tasks import BASE_TASKS, validate_task_inputs


class ProposeCandidateCorrection:
    def __init__(self, store, jobs, latest_review, verify_audio):
        self.store, self.jobs = store, jobs
        self.latest_review, self.verify_audio = latest_review, verify_audio

    def execute(self, song_id, task_id, request):
        task = self.jobs.get(song_id, task_id)
        review = self.latest_review(song_id, task_id).get("review")
        if not review or review.get("decision") != "changes_requested" or review.get("inputs_current") is not True:
            raise ValueError("Guarda una opinion vigente que describa los cambios antes de preparar la correccion.")
        if request.get("reviewed_at") != review.get("reviewed_at"):
            raise ValueError("La opinion cambio; revisala antes de preparar la correccion.")
        self.verify_audio(song_id, task_id, review["audio_sha256"])
        scope = request.get("scope")
        modes = {"segment": "repaint", "style": "cover", "reinterpret": "text2music",
                 "add_track": "lego", "isolate_track": "extract", "arrangement": "complete"}
        if not isinstance(scope, str) or scope not in modes:
            raise ValueError("Elige una accion de correccion disponible.")
        params = {"task_type": modes[scope]}
        if modes[scope] in BASE_TASKS:
            tracks, instruction = request.get("target_tracks"), request.get("instruction")
            if (not isinstance(tracks, list) or any(not isinstance(t, str) for t in tracks)
                    or not isinstance(instruction, str) or len(instruction) > 2000):
                raise ValueError("Selecciona pistas e indica una instruccion de hasta 2000 caracteres.")
            validate_task_inputs(modes[scope], "acestep-v15-base", review["artifact_id"], instruction, tracks=tuple(tracks))
            params.update(ace_step_config="acestep-v15-base", target_tracks=list(tracks), instruction=instruction.strip())
            if modes[scope] == "lego":
                params.update(repainting_start=0, repainting_end=-1)
        if scope == "segment":
            start, end = request.get("start"), request.get("end")
            checks = task.get("result", {}).get("fidelity_report", {}).get("checks", [])
            duration = next((c.get("observed") for c in checks if c.get("id") == "duration"
                             and c.get("method") == "wav_frames_sample_rate"), None)
            valid = lambda n: type(n) in (int, float) and math.isfinite(n)
            if not all(valid(n) for n in (start, end, duration)) or not 0 <= start < end <= duration:
                raise ValueError("Indica inicio y final dentro de la duracion medida del candidato.")
            params.update(repainting_start=start, repainting_end=end)
        proposal = {"task_id": task_id, "artifact_id": review["artifact_id"],
                    "audio_sha256": review["audio_sha256"], "plan_id": review["plan_id"],
                    "spec_revision_id": review["spec_revision_id"], "reviewed_at": review["reviewed_at"],
                    "notes": review["notes"], "criteria": dict(review.get("criteria", {})),
                    "scope": scope, "proposed_parameters": params,
                    "source_artifact_id": review["artifact_id"] if scope != "reinterpret" else None,
                    "status": "proposal", "ready_for_execution": False,
                    "pending": ["approved_spec_compilation", "plan_review", "runtime_preflight"]
                               + (["source_verification_in_plan"] if scope != "reinterpret" else []),
                    "created_at": datetime.now(timezone.utc).isoformat(), "actor": "user"}
        event = self.store.create_song_event(song_id=song_id, phase="SONG_SPEC_COLLECTION", status="pending", progress=0,
            message="Propuesta de correccion registrada; revisa la ficha y prepara un nuevo plan antes de generar.",
            active_model="user", payload={"candidate_correction": proposal}, artifact_id=review["artifact_id"])
        return {"proposal": proposal, "event": event}

    def latest(self, song_id, task_id):
        self.jobs.get(song_id, task_id)
        events = self.store.list_song_project_events(song_id)
        proposals = [event["payload"]["candidate_correction"]
                     for event in events
                     if event.get("payload", {}).get("candidate_correction", {}).get("task_id") == task_id]
        if not proposals:
            return {"proposal": None}
        proposal = max(proposals, key=lambda item: item["created_at"])
        review = self.latest_review(song_id, task_id).get("review")
        current = bool(review and review.get("inputs_current") is True
                       and review.get("decision") == "changes_requested"
                       and all(review.get(key) == proposal.get(key) for key in
                               ("reviewed_at", "plan_id", "spec_revision_id", "audio_sha256", "artifact_id")))
        reason = "" if current else "La opinion o los inputs cambiaron; registra una propuesta desde la revision vigente."
        if current:
            try:
                self.verify_audio(song_id, task_id, proposal["audio_sha256"])
            except (ValueError, OSError) as error:
                current, reason = False, str(error)
        reviews = [event["payload"]["candidate_correction_technical_review"] for event in events
                   if event.get("payload", {}).get("candidate_correction_technical_review", {}).get("task_id") == task_id
                   and event["payload"]["candidate_correction_technical_review"].get("proposal_created_at") == proposal["created_at"]]
        technical = max(reviews, key=lambda item: item["reviewed_at"]) if reviews else None
        return {"proposal": {**proposal, "inputs_current": current, "invalid_reason": reason,
                             "technical_review": technical}}
