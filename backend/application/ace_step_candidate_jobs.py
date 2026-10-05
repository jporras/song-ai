"""Background candidates reuse persisted orchestrator tasks and model runs."""
from copy import deepcopy
from threading import Lock, Event
from application.audio_cancellation import AudioCancelled
from uuid import uuid4
from typing import Protocol


class AudioHandoffLifecycle(Protocol):
    def begin_audio_handoff(self, task_id: str, run_id: str, payload: dict): ...
    def end_audio_handoff(self, task_id: str, run_id: str, payload: dict): ...


class AceStepCandidateJobs:
    TASK_TYPE = "ace_step_exploratory_candidate"

    def __init__(self, store, generate, review, dispatcher, preflight=None, orchestrator: AudioHandoffLifecycle | None = None):
        self.store, self.generate, self.review = store, generate, review
        self.dispatcher = dispatcher
        self.lock = Lock()
        self.cancellations = {}
        self.preflight = preflight
        self.orchestrator = orchestrator

    def recover_interrupted(self):
        for task in self.store.list_tasks():
            if task["task_type"] == self.TASK_TYPE and task["status"] in {"pending", "running", "cancelling"}:
                self.store.update_task(task["task_id"], "failed", 0,
                    "La generacion fue interrumpida; revisa el plan y vuelve a solicitar el borrador.", {"interrupted": True})
        for run in self.store.list_model_runs():
            if run.get("model_role") == "ace_candidate" and run.get("status") == "running":
                self.store.complete_model_run(run["run_id"], "failed", {"interrupted": True})

    def start(self, song_id: str, request: dict) -> dict:
        if request.get("exploratory_audio_authorized") is not True:
            raise ValueError("Autoriza el borrador exploratorio antes de iniciar.")
        item = self.review.latest(song_id)
        if not item or item["effective_status"] != "approved" or request.get("plan_sha256") != item["plan"]["plan_sha256"]:
            raise ValueError("Aprueba el plan vigente antes de iniciar el borrador.")
        evidence = self.preflight(item) if self.preflight is not None else {"status": "not_checked"}
        with self.lock:
            if any(task["task_type"] == self.TASK_TYPE and task["status"] in {"pending", "running", "cancelling"} for task in self.store.list_tasks()):
                raise ValueError("Ya hay un borrador en curso; espera a que termine.")
            task_id = "ace_job_" + uuid4().hex
            payload = {"song_id": song_id, "plan_id": item["plan_id"], "request": deepcopy(request)}
            payload["preflight"] = evidence
            payload["request"]["plan_id"] = item["plan_id"]
            task = self.store.create_task(task_id, self.TASK_TYPE, "music", payload, "Borrador pendiente de ejecucion.")
            self.cancellations[task_id] = Event()
            try:
                self.dispatcher.submit(lambda: self._run(task_id, payload))
            except Exception:
                self.store.update_task(task_id, "failed", 0, "No se pudo iniciar el trabajo; vuelve a intentarlo.")
                raise
            return task

    def cancel(self, song_id: str, task_id: str) -> dict:
        with self.lock:
            task = self.get(song_id, task_id)
            if task["status"] in {"completed", "failed", "cancelled"}:
                return task
            token = self.cancellations.get(task_id)
            if token is None:
                raise ValueError("El worker no esta disponible; reinicia y revisa el trabajo interrumpido.")
            token.set()
            status = "cancelled" if task["status"] == "pending" else "cancelling"
            return self.store.update_task(task_id, status, task["progress"],
                "Borrador cancelado antes de iniciar." if status == "cancelled" else "Deteniendo el borrador y restaurando recursos.")

    def get(self, song_id: str, task_id: str) -> dict:
        matches = [task for task in self.store.list_tasks() if task["task_id"] == task_id
                   and task["task_type"] == self.TASK_TYPE and task["payload"].get("song_id") == song_id]
        if len(matches) != 1:
            raise ValueError("El trabajo no pertenece al proyecto activo.")
        return matches[0]

    def latest(self, song_id: str) -> dict | None:
        return next((task for task in self.store.list_tasks() if task["task_type"] == self.TASK_TYPE
                     and task["payload"].get("song_id") == song_id), None)

    def _run(self, task_id: str, payload: dict):
        run_id = "ace_run_" + uuid4().hex
        token = self.cancellations[task_id]
        handoff_started = False

        def check_cancelled():
            if token.is_set():
                raise AudioCancelled("El usuario cancelo el borrador.")

        try:
            with self.lock:
                check_cancelled()
                self.store.update_task(task_id, "running", 5, "ACE-Step esta preparando el borrador.")
            self.store.create_model_run(run_id, task_id, "ace_candidate", "ACE-Step", "plan_selected_model",
                                        {"song_id": payload["song_id"], "plan_id": payload["plan_id"]})
            if self.orchestrator is not None:
                self.orchestrator.begin_audio_handoff(task_id, run_id, payload)
                handoff_started = True
            result = self.generate(payload["song_id"], payload["request"], cancellation_check=check_cancelled)
            check_cancelled()
        except AudioCancelled:
            self.store.update_task(task_id, "cancelled", 0, "Borrador cancelado; el original se conserva.", {"cancelled": True})
            self.store.complete_model_run(run_id, "cancelled", {"cancelled": True})
        except Exception as error:
            self.store.update_task(task_id, "failed", 0, "No se pudo generar el borrador; revisa el error y vuelve a intentarlo.", {"error": str(error)})
            self.store.complete_model_run(run_id, "failed", {"error": str(error)})
        else:
            with self.lock:
                if token.is_set():
                    self.store.complete_model_run(run_id, "cancelled", {"cancelled": True})
                    self.store.update_task(task_id, "cancelled", 0, "Borrador cancelado; no se acepta el resultado.")
                else:
                    self.store.complete_model_run(run_id, "completed", {"result": result})
                    self.store.update_task(task_id, "completed", 100, "Borrador creado; pendiente de escucha y evaluacion.", result)
        finally:
            with self.lock:
                self.cancellations.pop(task_id, None)
            if handoff_started:
                self.orchestrator.end_audio_handoff(task_id, run_id, payload)
