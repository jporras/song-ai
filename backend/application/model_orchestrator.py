from uuid import uuid4
from application.assistant_context_projection import assistant_context

from core.storage import StorageManager
from providers.registry import ProviderRegistry
from providers.llamacpp import LlamaCppError
from audio.execution_lock import audio_execution_active


class ModelOrchestrator:
    ROLE_PROVIDER_KEYS = {
        "assistant": "interpreter",
        "intent_extractor": "interpreter",
        "interpreter": "interpreter",
        "music": "music",
        "soundtrack": "music",
        "voice": "voice",
        "singing_voice": "voice",
        "lyrics": "lyrics",
        "audio": "music",
        "stems": "music",
        "mixer": "music",
        "technical": "technical",
    }

    DEFAULT_MODELS = {
        "assistant": "Gemma 2 2B IT GGUF",
        "intent_extractor": "Gemma 2 2B IT GGUF",
        "interpreter": "Gemma 2 2B IT GGUF",
        "music": "MusicGen small",
        "soundtrack": "MusicGen small",
        "voice": "RVC / ACE-Step",
        "singing_voice": "RVC / ACE-Step",
        "lyrics": "Gemma 2 2B IT GGUF",
        "audio": "ffmpeg",
        "stems": "Demucs",
        "mixer": "ffmpeg",
        "technical": "Qwen3 4B GGUF",
    }

    def __init__(self, storage: StorageManager, provider_registry: ProviderRegistry) -> None:
        self.storage = storage
        self.provider_registry = provider_registry

    def status(self) -> dict[str, object]:
        tasks = self.storage.list_tasks()
        latest_task = tasks[0] if tasks else None
        audio_task = self.active_audio_task()
        return {
            "mode": "local_audio_jobs" if any(task.get("task_type") == "ace_step_exploratory_candidate" for task in tasks) else "mock_orchestrator",
            "memory_policy": "one_heavy_model_at_a_time",
            "load_policy": "load_on_demand_release_after_task",
            "assistant_state": "suspended_for_audio" if audio_task else ("active" if latest_task is None else "active_after_handoff"),
            "active_model": None,
            "active_audio_task": audio_task,
            "latest_task": latest_task,
            "available_roles": list(self.ROLE_PROVIDER_KEYS),
            "active_providers": self.provider_registry.active_providers(),
        }

    def active_audio_task(self):
        return next((task for task in self.storage.list_tasks()
                     if task.get("task_type") == "ace_step_exploratory_candidate"
                     and task.get("status") in {"pending", "running", "cancelling"}), None)

    def require_planning_available(self):
        if self.active_audio_task() is not None or audio_execution_active():
            raise ValueError("Hay un borrador de audio activo; espera o cancela antes de solicitar revision de modelos.")

    def begin_audio_handoff(self, task_id: str, run_id: str, payload: dict):
        self.record_project_event(project_id=payload["song_id"], project_name=payload["song_id"],
            phase="SONG_SPEC_COLLECTION", actor="orchestrator", model_role="music", provider_name="ACE-Step",
            status="suspended", message="Assistant pausado; el plan persistido pasa al worker de audio.",
            task_id=task_id, run_id=run_id, metadata={"plan_id": payload["plan_id"], "model_load_verified": False})

    def end_audio_handoff(self, task_id: str, run_id: str, payload: dict):
        task = next((item for item in self.storage.list_tasks() if item["task_id"] == task_id), {})
        self.record_project_event(project_id=payload["song_id"], project_name=payload["song_id"],
            phase="SONG_SPEC_COLLECTION", actor="orchestrator", model_role="assistant", provider_name="assistant-ui",
            status="resumed", message="Worker de audio cerrado; assistant disponible desde el estado persistido.",
            task_id=task_id, run_id=run_id, metadata={"outcome": task.get("status"), "model_reload_verified": False})

    def run_handoff(self, payload: dict[str, object]) -> dict[str, object]:
        self.require_planning_available()
        from application.song_spec_proposal import engine_input_check
        context = dict(payload.get('context') or {})
        plan = context.get('candidate_plan') or context.get('current_spec')
        if isinstance(plan, dict):
            engine_check = engine_input_check(plan)
            if engine_check:
                payload = {**payload, 'context': {**context, 'engine_input_validation': engine_check}}
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
                "mode": "provider_handoff" if self._can_run_provider_handoff(model_role) else "mock_handoff",
                "capabilities": provider["capabilities"],
                "assistant_state": "suspended",
            },
        )

        provider_payload = {**payload, "_task_id": task_id} if task_type == "compile_song_spec" else payload
        result = self.build_provider_result(model_role, task_type, provider_payload) or self.build_mock_result(
            model_role,
            task_type,
            payload,
        )
        result.setdefault("mode", "mock_handoff")
        result.setdefault("provider_executed", False)
        compilation_failed = task_type == 'compile_song_spec' and (
            result['mode'] != 'provider_handoff' or not result.get('spec_proposal'))
        compilation_failed = compilation_failed or (task_type == 'propose_full_lyrics' and not result.get('lyrics_proposal'))
        compilation_failed = compilation_failed or (task_type == 'collect_song_intent' and not result.get('intent_guidance'))
        outcome = 'failed' if compilation_failed else 'completed'
        completed_task = self.storage.update_task(
            task_id=task_id,
            status=outcome,
            progress=100,
            message=(("No se pudo preparar la propuesta de letra; ficha conservada y assistant reactivado."
                      if task_type == 'propose_full_lyrics' else
                      "No se pudo revisar la intención; ficha conservada y assistant reactivado."
                      if task_type == 'collect_song_intent' else "La compilacion fallo; ficha conservada y assistant reactivado.") if compilation_failed
                     else "Handoff completado. Resultado persistido y assistant reactivado."),
            result=result,
        )
        completed_run = self.storage.complete_model_run(
            run_id=run_id,
            status=outcome,
            metadata={
                "mode": result.get("mode", "mock_handoff"),
                "capabilities": provider["capabilities"],
                "assistant_state": "reactivated",
                "result_summary": result["summary"],
                "provider_executed": result.get("provider_executed", False),
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
            "result": result,
        }

    def review_sqlite_project_state(self, payload: dict[str, object]) -> dict[str, object]:
        context = dict(payload.get("context", {}))
        validation = self._validate_sqlite_project_context(context)
        handoff = self.run_handoff(
            {
                **payload,
                "model_role": "technical",
                "task_type": "sqlite_project_technical_review",
                "phase": str(payload.get("phase", "technical_review")),
                "technical_validation": validation,
            }
        )
        return {
            "handoff": handoff,
            "validation": validation,
        }

    def build_provider_result(
        self,
        model_role: str,
        task_type: str,
        payload: dict[str, object],
    ) -> dict[str, object] | None:
        if task_type == 'collect_song_intent':
            from application.local_intent_assistance import provider_intent_guidance
            return provider_intent_guidance(self.provider_registry, payload)
        if task_type == 'propose_full_lyrics':
            from application.full_lyrics_proposal import provider_lyrics_proposal
            return provider_lyrics_proposal(self.provider_registry, payload)
        if task_type == "sqlite_project_technical_review":
            return None
        if not self._can_run_provider_handoff(model_role):
            return None
        prompt = self._technical_prompt(task_type, payload)
        try:
            response = self.provider_registry.technical_with_active_provider(prompt, task_type)
        except (LlamaCppError, OSError, TimeoutError, ValueError) as error:
            return {
                **self.build_mock_result(model_role, task_type, payload),
                "mode": "mock_handoff_after_provider_error",
                "provider_executed": False,
                "provider_error": str(error),
            }
        summary = str(response.get("summary", "")).strip()
        proposal = None
        if task_type == "compile_song_spec":
            if payload.get("_task_id"):
                self.storage.update_task(task_id=payload["_task_id"], status="running", progress=75,
                                         message="Respuesta del modelo recibida; validando la propuesta.")
            from application.song_spec_proposal import specification_proposal
            try:
                proposal = specification_proposal(summary, payload["context"])
            except ValueError as error:
                return {"mode": "provider_invalid_output", "provider_executed": True,
                        "provider_error": str(error), "summary": "La ficha activa se conserva; revisa el error de la propuesta.",
                        "engine_steering": response.get("engine_steering", {})}
            summary = proposal["summary"]
        if not summary:
            return None
        response_mode = str(response.get("mode", "unknown"))
        provider_executed = response_mode not in {"local_mock", "mock", "placeholder"}
        return {
            "model_role": model_role,
            "task_type": task_type,
            "mode": "provider_handoff" if provider_executed else "mock_handoff",
            "provider_executed": provider_executed,
            "provider_name": response.get("model", self.DEFAULT_MODELS.get(model_role, "unknown")),
            "summary": summary,
            "engine_steering": response.get("engine_steering", {}),
            "engine_input_validation": payload.get('context', {}).get('engine_input_validation'),
            "missing_fields": [],
            "validation_results": {
                "status": "provider_review_unverified",
                "source_of_truth": "sqlite_payload",
                "provider_mode": response_mode,
            },
            "song_blueprint": {
                "goal": "complete_song_with_local_pipeline",
                "audio_pipeline": ["confirmed_spec", "approved_ace_plan", "exploratory_audio", "approved_representative_sample", "full_song", "export"],
            },
            "next_action": summary,
            "spec_proposal": proposal,
        }

    def _can_run_provider_handoff(self, model_role: str) -> bool:
        return model_role == "technical"

    def _technical_prompt(self, task_type: str, payload: dict[str, object]) -> str:
        project_name = str(payload.get("project_name", "Proyecto activo"))
        question = str(payload.get("question", "Revisa el siguiente paso tecnico."))
        context = assistant_context(payload.get("context", {}))
        if task_type == "compile_song_spec":
            import json
            context = {**context,
                "current_spec": {key: value for key, value in context['current_spec'].items() if not key.startswith('_')},
                "fields": {key: {name: value for name, value in field.items() if name in {'help', 'control', 'required_for_spec', 'options', 'applicable'}}
                           for key, field in context['fields'].items()}}
            return json.dumps({"task": task_type, "question": question, "context": context}, ensure_ascii=False, separators=(',', ':'))
        return (
            "Responde en espanol, maximo 5 bullets, sin mostrar razonamiento interno. "
            "Eres el director tecnico invisible de Song AI. Valida el pipeline y di solo el siguiente paso util.\n\n"
            f"Tarea: {task_type}\n"
            f"Proyecto: {project_name}\n"
            f"Contexto SQLite/pipeline: {context}\n"
            f"Pregunta: {question}"
        )

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
        if task_type == "sqlite_project_technical_review":
            validation = dict(payload.get("technical_validation", {}))
            return {
                "model_role": model_role,
                "task_type": task_type,
                "summary": str(validation.get("summary", "Revision tecnica completada desde SQLite.")),
                "missing_fields": list(validation.get("missing_items", [])),
                "validation_results": validation,
                "song_blueprint": {
                    "goal": "complete_song_with_project_state_from_sqlite",
                    "source_of_truth": "sqlite",
                    "handoff_contract": "backend_sqlite_snapshot_to_technical_to_gemma",
                },
                "next_action": str(validation.get("next_action", "")),
            }
        project_name = str(payload.get("project_name", "Proyecto activo"))
        return {
            "model_role": model_role,
            "task_type": task_type,
            "summary": (
                f"{model_role} preparo '{task_type}' para {project_name} como cancion completa. "
                "El resultado mantiene letra, estructura, soundtrack, voz cantada y mezcla como fases separadas."
            ),
            "missing_fields": [],
            "validation_results": {
                "status": "mock_valid",
                "source_of_truth": "sqlite",
                "not_short_format": True,
                "avoid_poor_repetition": True,
                "voice_must_be_sung": True,
            },
            "song_blueprint": {
                "goal": "complete_lullaby_or_children_emotional_song",
                "structure": [
                    "intro",
                    "verse 1",
                    "optional pre chorus",
                    "chorus",
                    "verse 2",
                    "optional bridge",
                    "final chorus",
                    "outro",
                ],
                "audio_pipeline": ["soundtrack", "singing_voice", "stems", "mixer", "export"],
                "video": "optional_only",
            },
            "next_action": "Persistir intent/set y continuar con letra completa, prompt musical, soundtrack, voz cantada y mezcla.",
        }

    def _validate_sqlite_project_context(self, context: dict[str, object]) -> dict[str, object]:
        project = dict(context.get("project") or {})
        set_data = dict(context.get("set") or {})
        phase_data = dict(context.get("phase_data") or {})
        saved_editor_phases = dict(context.get("saved_editor_phases") or {})
        ui_ready_phases = dict(context.get("ui_ready_phases") or {})
        professional_project = dict(context.get("active_professional_project") or {})
        professional_next = dict(context.get("professional_next") or {})
        ui_statuses = dict(context.get("ui_editor_phase_statuses") or {})

        missing: list[str] = []
        warnings: list[str] = []
        required_assets = ("instrumental_id", "melody_id", "lyrics_id")
        for key in required_assets:
            if not str(set_data.get(key, "")).strip():
                missing.append(key)

        active_spec = dict(dict(professional_project.get("spec") or {}).get("json_spec") or {})
        from models.ace_step_tasks import TASKS
        ace_route = active_spec.get("task_type") in TASKS
        required_phases = ("intent",) if ace_route else ("intent", "lyrics", "music-plan", "midi", "instrumental", "voice")
        for phase in required_phases:
            is_saved = bool(dict(phase_data.get(phase, {})).get("status")) or bool(saved_editor_phases.get(phase))
            ui_ready = bool(ui_ready_phases.get(phase)) or str(ui_statuses.get(phase, "")).upper() == "READY"
            if not is_saved:
                missing.append(f"guardar fase:{phase}" if ui_ready else f"fase:{phase}")

        intent_data = dict(dict(phase_data.get("intent", {})).get("data", {})).get("intent", {})
        lyrics_data = dict(dict(phase_data.get("lyrics", {})).get("data", {}))
        music_data = dict(dict(phase_data.get("music-plan", {})).get("data", {})).get("musicPlan", {})
        voice_data = dict(dict(phase_data.get("voice", {})).get("data", {})).get("voice", {})

        if isinstance(intent_data, dict):
            for field in ("description", "language", "bpm", "key"):
                if field in intent_data and not str(intent_data.get(field, "")).strip():
                    warnings.append(f"intent.{field} vacio")
        lyric_sections = lyrics_data.get("lyricSections", [])
        lyrics_editor = dict(lyrics_data.get("lyricsEditor", {}))
        if (
            phase_data.get("lyrics")
            and not lyric_sections
            and not str(lyrics_editor.get("content", "")).strip()
            and "fase:lyrics" not in missing
            and "guardar fase:lyrics" not in missing
        ):
            missing.append("lyrics.content")

        if isinstance(music_data, dict) and music_data:
            for field in ("bpm", "key", "timeSignature"):
                if not str(music_data.get(field, "")).strip():
                    missing.append(f"music-plan.{field}")
            sections = music_data.get("sections", [])
            if not isinstance(sections, list) or not sections:
                missing.append("music-plan.sections")
            else:
                duration = sum(int(dict(section).get("seconds") or dict(section).get("duration") or 0) for section in sections)
                if duration <= 0:
                    missing.append("music-plan.duration")
        elif phase_data.get("music-plan") and "fase:music-plan" not in missing and "guardar fase:music-plan" not in missing:
            missing.append("music-plan.data")

        if isinstance(voice_data, dict) and voice_data:
            if not str(voice_data.get("mainVoice", "") or voice_data.get("style", "")).strip():
                warnings.append("voice.mainVoice vacio")

        if not professional_project:
            missing.append("production.project")
        elif str(professional_next.get("status", "")) != "completed":
            warnings.append(f"production.next:{professional_next.get('missing_label', 'siguiente fase')}")

        blocking = [item for item in missing if not item.startswith("production.")]
        status = "ready_for_production" if not blocking else "needs_user_input"
        if status == "ready_for_production" and not professional_project:
            status = "needs_production_preparation"

        if blocking:
            next_action = f"Completar {blocking[0]} antes de continuar."
        elif not professional_project:
            next_action = "Preparar Production para el proyecto activo."
        else:
            next_action = str(professional_next.get("recommendation") or "Ejecutar la siguiente tarea de Production.")

        project_name = str(project.get("project_name") or set_data.get("project_name") or "Proyecto activo")
        summary = (
            f"Revision tecnica de {project_name}: {status}. "
            f"Faltantes: {', '.join(missing) if missing else 'ninguno'}. "
            f"Siguiente accion: {next_action}"
        )
        return {
            "status": status,
            "source_of_truth": "sqlite",
            "project_id": str(project.get("project_id") or set_data.get("set_id") or ""),
            "project_name": project_name,
            "missing_items": missing,
            "warnings": warnings,
            "next_action": next_action,
            "summary": summary,
            "gemma_instruction": self._gemma_instruction(status, missing, warnings, next_action),
        }

    def _gemma_instruction(
        self,
        status: str,
        missing: list[str],
        warnings: list[str],
        next_action: str,
    ) -> str:
        if missing:
            return (
                "Si: estas en el proyecto activo. La revision tecnica indica que falta completar "
                f"{', '.join(missing)}. Siguiente paso: {next_action}"
            )
        if warnings:
            return (
                "El proyecto esta usable. La revision tecnica marco esta advertencia "
                f"({warnings[0]}). Siguiente paso: {next_action}"
            )
        return f"Tecnicamente el proyecto esta listo para continuar. Siguiente paso: {next_action}"
