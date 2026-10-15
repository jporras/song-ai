"""Sample feedback is separate from candidate feedback and approval."""
from datetime import datetime, timezone
from pathlib import Path
from application.listening_feedback import validate_listening_feedback


class ReviewSampleListening:
    def __init__(self, store, find_sample):
        self.store, self.find_sample = store, find_sample

    def execute(self, song_id: str, sample_id: str, request: dict) -> dict:
        decision, notes = validate_listening_feedback(request)
        sample = self.find_sample(song_id, sample_id)
        fingerprint = self.store.set_generation_fingerprint(sample["set_id"])
        evidence = self.store.verify_sample_audio(sample)
        if sample.get("set_fingerprint") != fingerprint or request.get("audio_sha256") != evidence["sha256"]:
            raise ValueError("El sample o el set cambiaron. Revisa su version vigente antes de guardar.")
        review = {"sample_id": sample_id, "audio_sha256": evidence["sha256"], "set_fingerprint": fingerprint,
                  "decision": decision, "notes": notes, "listened": True, "actor": "user",
                  "reviewed_at": datetime.now(timezone.utc).isoformat(), "final_quality_verified": False}
        updated = {**sample, "listening_review": review}
        if decision == "changes_requested":
            updated["approval_status"] = "pending"
            for key in ("approved_at", "approved_set_fingerprint", "approved_audio_sha256", "listening_confirmed_at"):
                updated.pop(key, None)
        self.store.save_legacy_sample({k: v for k, v in updated.items() if k not in {"json_path", "path"}}, Path(sample["path"]) / "sample.json",
                                     event_type="SAMPLE_LISTENING_REVIEWED", message="Opinion de escucha del sample registrada.")
        self.store.create_song_event(song_id=song_id, phase="SONG_SPEC_COLLECTION", status="completed", progress=100,
            message="Opinion de escucha del sample registrada; la aprobacion es una accion separada.", active_model="user",
            payload={"sample_listening_review": review}, artifact_id=sample.get("source_artifact_id", ""))
        return {"review": review}
