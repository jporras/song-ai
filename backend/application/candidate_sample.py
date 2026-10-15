"""Explicit pending sample copy; does not certify representative final audio."""
import shutil
from uuid import uuid4


class CreateCandidateSample:
    def __init__(self, store, jobs, plans, verify_audio, inspect_audio):
        self.store, self.jobs, self.plans = store, jobs, plans
        self.verify_audio, self.inspect_audio = verify_audio, inspect_audio

    def execute(self, song_id: str, task_id: str, request: dict) -> dict:
        if request.get("create_sample_confirmed") is not True:
            raise ValueError("Confirma que quieres crear un sample pendiente de revision.")
        set_id = request.get("set_id")
        project = self.store.get_song_project(song_id)
        if not isinstance(set_id, str) or not set_id or not project or project.get("user_id") != f"set:{set_id}":
            raise ValueError("Selecciona el set vinculado al proyecto para crear su sample.")
        task = self.jobs.get(song_id, task_id)
        metadata = task.get("result", {}).get("artifact", {}).get("metadata", {})
        fingerprint = self.store.set_generation_fingerprint(set_id)

        def validate():
            active = self.store.get_song_project(song_id)
            plan = self.plans.latest(song_id)
            if not active or active.get("user_id") != f"set:{set_id}":
                raise ValueError("El proyecto cambio de set; revisa el candidato.")
            if metadata.get("set_id") != set_id or not metadata.get("set_fingerprint") or metadata["set_fingerprint"] != self.store.set_generation_fingerprint(set_id):
                raise ValueError("El candidato no acredita el set vigente; genera uno nuevo.")
            if not plan or plan.get("effective_status") != "approved" or plan.get("plan_id") != metadata.get("plan_id") or plan["plan"]["plan_sha256"] != metadata.get("plan_sha256"):
                raise ValueError("El candidato no corresponde al plan aprobado vigente.")
            return plan

        plan = validate()
        source = self.verify_audio(song_id, task_id, request.get("audio_sha256", ""))
        sample_id = "sample-" + uuid4().hex
        directory = self.store.data_dir / "samples" / sample_id
        directory.mkdir(parents=True)
        output = directory / "preview.wav"
        try:
            shutil.copyfile(source, output)
            evidence = self.inspect_audio(output, directory)
            if evidence["sha256"] != metadata.get("audio_evidence", {}).get("sha256"):
                raise ValueError("El audio cambio durante la copia; vuelve a revisar el candidato.")
            validate()
            self.verify_audio(song_id, task_id, request.get("audio_sha256", ""))
            sample = {"sample_id": sample_id, "set_id": set_id, "set_fingerprint": fingerprint,
                      "provider": "ace-step", "status": "candidate_audio_checkpoint",
                      "approval_status": "pending", "audio_evidence": evidence,
                      "source_song_id": song_id, "source_task_id": task_id,
                      "source_artifact_id": task["result"]["artifact"]["artifact_id"],
                      "plan_id": metadata["plan_id"], "plan_sha256": metadata["plan_sha256"],
                      "spec_revision_id": metadata["spec_revision_id"],
                      "provider_config": plan["plan"]["retained_spec"].get("ace_step_config"),
                      "runtime_evidence": metadata.get("runtime_evidence", {"status": "pending", "quality_verified": False}),
                      "task_type": metadata.get("task_type"), "representativity_verified": False,
                      "final_quality_verified": False}
        except Exception:
            # Only files created by this call, never candidate originals.
            output.unlink(missing_ok=True)
            raise
        self.store.save_legacy_sample(sample, directory / "sample.json")
        return {"sample": sample, "message": "Sample creado. Escuchalo y revisalo por separado; la representatividad para produccion real sigue pendiente."}
