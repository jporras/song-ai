"""Read sample evidence for the selected project without creating an evaluation."""
class SampleEvaluationContext:
    def __init__(self, store, latest_evaluation, latest_listening=None):
        self.store, self.latest_evaluation = store, latest_evaluation
        self.latest_listening = latest_listening

    def build(self, project: dict | None) -> dict:
        owner = str((project or {}).get("user_id", ""))
        if not project or not owner.startswith("set:") or not owner[4:]:
            return {"status": "set_pending", "final_generation_ready": False}
        samples = self.store.list_samples_for_set(owner[4:])
        if not samples:
            return {"status": "sample_pending", "final_generation_ready": False}
        sample = samples[0]
        song_id = project["id"]
        if sample.get("source_song_id") != song_id:
            return {"status": "project_sample_pending", "final_generation_ready": False}
        report = self.latest_evaluation(song_id, sample["sample_id"])["report"]
        status = "evaluation_pending" if report is None else "evaluated" if report.get("assessment_current") is True else "historical_evaluation"
        return {"status": status, "sample_id": sample["sample_id"],
                "approval_status": sample.get("approval_status", "pending"), "report": report,
                "listening_review": self.latest_listening(song_id, sample["sample_id"])["review"] if self.latest_listening else sample.get("listening_review"),
                "source": "sqlite_sample_evaluation", "final_generation_ready": False}
