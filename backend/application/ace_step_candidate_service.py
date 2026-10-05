"""Exploratory audio is a candidate artifact, never a final song or approved sample."""
from typing import Protocol
from uuid import uuid4
from audio.execution_lock import exclusive_audio
from audio.ace_step_profiles import resolve_ace_step_profile
from application.audio_cancellation import AudioCancelled
from application.candidate_fidelity import CandidateFidelityReport


class CandidateRunner(Protocol):
    def run(self, project, item, profile, directory, output, revalidate, cancellation_check=None): ...


class AceStepCandidateService:
    def __init__(self, store, review, runner: CandidateRunner, audio_inspector):
        self.store, self.review = store, review
        self.runner, self.audio_inspector = runner, audio_inspector

    def execute(self, song_id: str, request: dict, cancellation_check=None) -> dict:
        if request.get("exploratory_audio_authorized") is not True:
            raise ValueError("Autoriza explicitamente un borrador de audio; no sera sample ni cancion final.")
        with exclusive_audio():
            project = self.store.get_song_project(song_id)
            if project is None:
                raise ValueError("Proyecto no encontrado.")
            item = self.review.latest(song_id)
            if not item or item["effective_status"] != "approved" or request.get("plan_sha256") != item["plan"]["plan_sha256"]:
                raise ValueError("Revisa y aprueba el plan vigente antes de generar un borrador.")
            if request.get("plan_id") is not None and request["plan_id"] != item["plan_id"]:
                raise ValueError("El plan seleccionado cambio; solicita un nuevo trabajo.")
            config = item["plan"]["retained_spec"].get("ace_step_config")
            if config not in {"acestep-v15-base", "acestep-v15-turbo"}:
                raise ValueError("Selecciona una configuracion local comprobable.")
            profile = resolve_ace_step_profile("base" if config == "acestep-v15-base" else "turbo")
            run_id = "ace_candidate_" + uuid4().hex
            directory = self.store.data_dir / "projects" / song_id / "candidates" / run_id
            output = directory / "candidate.wav"

            def revalidate():
                if cancellation_check is not None:
                    cancellation_check()
                current = self.review.latest(song_id)
                if not current or current["effective_status"] != "approved" or current["plan_id"] != item["plan_id"] or current["plan"]["plan_sha256"] != item["plan"]["plan_sha256"]:
                    raise ValueError("El plan o sus inputs cambiaron; el borrador no se asociara a esa revision.")

            self.store.create_song_event(song_id=song_id, phase="SONG_SPEC_COLLECTION", status="running", progress=0,
                message="Generando borrador exploratorio de audio.", active_model="ace-step",
                payload={"run_id": run_id, "plan_id": item["plan_id"], "task_type": item["plan"]["payload"]["task_type"]})
            try:
                if cancellation_check is None:
                    self.runner.run(project, item, profile, directory, output, revalidate)
                else:
                    self.runner.run(project, item, profile, directory, output, revalidate, cancellation_check=cancellation_check)
                evidence = self.audio_inspector(output, directory)
                fidelity = CandidateFidelityReport().build(item["plan"], evidence)
                revalidate()
                artifact = self.store.create_song_artifact(artifact_id=run_id, song_id=song_id,
                    phase="SONG_SPEC_COLLECTION", artifact_type="ace_step_candidate_wav", file_path=str(output),
                    metadata={"plan_id": item["plan_id"], "plan_sha256": item["plan"]["plan_sha256"],
                        "spec_revision_id": item["plan"]["spec_revision_id"], "task_type": item["plan"]["payload"]["task_type"],
                        "quality_status": "exploratory_candidate", "audio_evidence": evidence,
                        "sample_approved": False, "musical_quality_verified": False, "fidelity_report": fidelity})
            except Exception as error:
                cancelled = isinstance(error, AudioCancelled)
                self.store.create_song_event(song_id=song_id, phase="SONG_SPEC_COLLECTION", status="cancelled" if cancelled else "failed", progress=0,
                    message="Borrador cancelado; el original se conserva." if cancelled else "Fallo el borrador; el original se conserva.", active_model="ace-step",
                    payload={"run_id": run_id, "error": str(error)})
                raise
            self.store.create_song_event(song_id=song_id, phase="SONG_SPEC_COLLECTION", status="completed", progress=100,
                message="Borrador creado; pendiente de escucha y evaluacion.", active_model="ace-step",
                payload={"run_id": run_id, "plan_id": item["plan_id"]}, artifact_id=run_id)
            return {"artifact": artifact, "quality_status": "exploratory_candidate", "sample_approved": False,
                    "fidelity_report": fidelity}
