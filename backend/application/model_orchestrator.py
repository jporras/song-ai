from uuid import uuid4

from core.storage import StorageManager
from providers.registry import ProviderRegistry


class ModelOrchestrator:
    ROLE_PROVIDER_KEYS = {
        "assistant": "interpreter",
        "intent_extractor": "interpreter",
        "music": "music",
        "voice": "voice",
        "lyrics": "lyrics",
        "audio": "music",
    }

    DEFAULT_MODELS = {
        "assistant": "assistant-placeholder",
        "intent_extractor": "qwen-intent-placeholder",
        "music": "musicgen-placeholder",
        "voice": "voice-placeholder",
        "lyrics": "lyrics-placeholder",
        "audio": "audio-pipeline-placeholder",
    }

    def __init__(self, storage: StorageManager, provider_registry: ProviderRegistry) -> None:
        self.storage = storage
        self.provider_registry = provider_registry

    def status(self) -> dict[str, object]:
        tasks = self.storage.list_tasks()
        latest_task = tasks[0] if tasks else None
        return {
            "mode": "mock_orchestrator",
            "memory_policy": "one_heavy_model_at_a_time",
            "assistant_state": "active" if latest_task is None else "active_after_handoff",
            "active_model": None,
            "latest_task": latest_task,
            "available_roles": list(self.ROLE_PROVIDER_KEYS),
            "active_providers": self.provider_registry.active_providers(),
        }

    def run_handoff(self, payload: dict[str, object]) -> dict[str, object]:
        model_role = str(payload.get("model_role", "intent_extractor"))
        task_type = str(payload.get("task_type", "extract_intent"))
        if model_role not in self.ROLE_PROVIDER_KEYS:
            raise ValueError(f"Rol de modelo no soportado: {model_role}")

        task_id = f"task_{uuid4().hex[:12]}"
        run_id = f"run_{uuid4().hex[:12]}"
        provider = self.select_provider(model_role)
        model_name = str(payload.get("model_name", self.DEFAULT_MODELS[model_role]))
        project_name = str(payload.get("project_name", "Proyecto activo"))
        project_id = str(payload.get("project_id", project_name))
        phase = str(payload.get("phase", task_type))

        task = self.storage.create_task(
            task_id=task_id,
            task_type=task_type,
            model_role=model_role,
            payload=payload,
            message="Tarea registrada. Assistant suspendido temporalmente.",
        )
        self.record_project_event(
            project_id=project_id,
            project_name=project_name,
            phase=phase,
            actor="assistant",
            model_role="assistant",
            provider_name="assistant-ui",
            status="suspended",
            message=f"Assistant entrega el proyecto a {model_role} para {task_type}.",
            task_id=task_id,
            run_id="",
            metadata={"handoff_to": model_role},
        )
        self.storage.update_task(
            task_id=task_id,
            status="running",
            progress=40,
            message=f"Ejecutando handoff hacia {model_role}.",
        )
        self.record_project_event(
            project_id=project_id,
            project_name=project_name,
            phase=phase,
            actor="model",
            model_role=model_role,
            provider_name=provider["name"],
            status="running",
            message=f"{model_role} inicia procesamiento tecnico.",
            task_id=task_id,
            run_id=run_id,
            metadata={"model_name": model_name, "capabilities": provider["capabilities"]},
        )
        self.storage.create_model_run(
            run_id=run_id,
            task_id=task_id,
            model_role=model_role,
            provider_name=provider["name"],
            model_name=model_name,
            metadata={
                "mode": "mock_handoff",
                "capabilities": provider["capabilities"],
                "assistant_state": "suspended",
            },
        )

        result = self.build_mock_result(model_role, task_type, payload)
        completed_task = self.storage.update_task(
            task_id=task_id,
            status="completed",
            progress=100,
            message="Handoff completado. Resultado persistido y assistant reactivado.",
            result=result,
        )
        completed_run = self.storage.complete_model_run(
            run_id=run_id,
            status="completed",
            metadata={
                "mode": "mock_handoff",
                "capabilities": provider["capabilities"],
                "assistant_state": "reactivated",
                "result_summary": result["summary"],
            },
        )
        self.record_project_event(
            project_id=project_id,
            project_name=project_name,
            phase=phase,
            actor="assistant",
            model_role="assistant",
            provider_name="assistant-ui",
            status="reactivated",
            message="Assistant retoma conversacion con el resultado persistido.",
            task_id=task_id,
            run_id=run_id,
            metadata={"result_summary": result["summary"]},
        )

        return {
            "task": completed_task,
            "model_run": completed_run,
            "summary": result["summary"],
        }

    def record_project_event(
        self,
        project_id: str,
        project_name: str,
        phase: str,
        actor: str,
        model_role: str,
        provider_name: str,
        status: str,
        message: str,
        task_id: str,
        run_id: str,
        metadata: dict[str, object],
    ) -> dict[str, object]:
        return self.storage.create_project_event(
            event_id=f"event_{uuid4().hex[:12]}",
            project_id=project_id,
            project_name=project_name,
            phase=phase,
            actor=actor,
            model_role=model_role,
            provider_name=provider_name,
            status=status,
            message=message,
            task_id=task_id,
            run_id=run_id,
            metadata=metadata,
        )

    def select_provider(self, model_role: str) -> dict[str, object]:
        provider_key = self.ROLE_PROVIDER_KEYS[model_role]
        return self.provider_registry.active_providers()[provider_key]

    def build_mock_result(
        self,
        model_role: str,
        task_type: str,
        payload: dict[str, object],
    ) -> dict[str, object]:
        project_name = str(payload.get("project_name", "Proyecto activo"))
        return {
            "model_role": model_role,
            "task_type": task_type,
            "summary": (
                f"{model_role} preparo la tarea '{task_type}' para {project_name}. "
                "La ejecucion real queda lista para conectarse a un provider local/pro."
            ),
            "missing_fields": [],
            "validation_results": {
                "status": "mock_valid",
                "source_of_truth": "sqlite",
            },
            "next_action": "Persistir intent/set y continuar con el siguiente paso del pipeline.",
        }
