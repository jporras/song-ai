"""Explicit tool dispatch to existing use cases; model proposals never execute here."""
from copy import deepcopy
from dataclasses import dataclass
from typing import Callable


@dataclass(frozen=True)
class MusicTool:
    id: str
    label: str
    effect: str
    parameters: dict
    required: tuple = ()
    controls: tuple = ()


class MusicToolRegistry:
    def __init__(self):
        self._tools = {}
        self._handlers = {}

    def register(self, tool: MusicTool, handler: Callable):
        if tool.id in self._tools:
            raise ValueError("La herramienta ya esta registrada.")
        if tool.effect not in {"read", "propose", "edit", "confirm", "reject", "execute", "cancel", "restore"}:
            raise ValueError("Efecto de herramienta desconocido.")
        self._tools[tool.id], self._handlers[tool.id] = tool, handler

    def resolve(self, tool_id):
        if not isinstance(tool_id, str) or tool_id not in self._tools:
            raise ValueError("La herramienta solicitada no existe.")
        return self._tools[tool_id], self._handlers[tool_id]

    def catalog(self):
        names = {str: "string", dict: "object", bool: "boolean"}
        return [{"id": tool.id, "label": tool.label, "effect": tool.effect,
                 "parameters": {key: {"type": names[type_], "required": key in tool.required}
                                for key, type_ in tool.parameters.items()},
                 "control_ids": list(tool.controls), "requires_revision": tool.effect != "read",
                 "requires_user_authorization": tool.effect != "read",
                 "model_can_execute": False}
                for tool in self._tools.values()]


class MusicActionRouter:
    def __init__(self, store, registry):
        self.store, self.registry = store, registry

    def execute(self, song_id, request):
        if not isinstance(request, dict) or set(request) - {"tool_id", "revision_id", "user_authorized", "parameters"}:
            raise ValueError("Revisa el contrato de la accion musical.")
        tool, handler = self.registry.resolve(request.get("tool_id"))
        parameters = request.get("parameters", {})
        if not isinstance(parameters, dict) or set(parameters) - set(tool.parameters):
            raise ValueError("Parametros desconocidos para esta herramienta.")
        for key in tool.required:
            if key not in parameters:
                raise ValueError("Falta un parametro obligatorio: " + key)
        for key, value in parameters.items():
            if type(value) is not tool.parameters[key] or (isinstance(value, str) and not value.strip()):
                raise ValueError("Tipo o valor invalido para: " + key)
        project = self.store.get_song_project(song_id)
        if project is None:
            raise ValueError("Proyecto no encontrado.")
        current = (project.get("spec") or {}).get("revision", {}).get("revision_id")
        if tool.effect != "read":
            if request.get("user_authorized") is not True:
                raise ValueError("Revisa la accion y autoriza su ejecucion explicitamente.")
            if not current or request.get("revision_id") != current:
                raise ValueError("La ficha cambio. Recarga antes de ejecutar la accion.")
        result = handler(song_id, current, deepcopy(parameters))
        if tool.effect != "read":
            self.store.create_song_event(song_id=song_id, phase="SONG_SPEC_COLLECTION",
                status="completed", progress=100, active_model="user", message="Accion musical enviada al caso de uso.",
                payload={"music_action": {"tool_id": tool.id, "source_revision_id": current,
                         "effect": tool.effect, "parameters": deepcopy(parameters),
                         "authorization": "explicit_user_action", "result_quality_verified": False}})
        return {"tool_id": tool.id, "source_revision_id": current, "result": result}


def local_music_tools(service):
    """Composition only: no provider construction or engine logic in the router."""
    from application.music_spec_edit import EditMusicSpec
    editable_controls = tuple(sorted(EditMusicSpec(service.storage).editable_fields()))
    registry = MusicToolRegistry()
    entries = [
        (MusicTool("spec.read", "Leer la ficha", "read", {}),
         lambda song, revision, params: service.get_professional_specification(song)),
        (MusicTool("spec.propose", "Solicitar propuesta tecnica", "propose", {}),
         lambda song, revision, params: service.propose_song_specification(song)),
        (MusicTool("spec.edit", "Guardar decisiones revisadas", "edit", {"values": dict}, ("values",), editable_controls),
         lambda song, revision, params: service.edit_music_spec(song, {"revision_id": revision, **params})),
        (MusicTool("spec.confirm", "Confirmar la ficha", "confirm", {}),
         lambda song, revision, params: service.confirm_professional_specification(song, {"revision_id": revision})),
        (MusicTool("spec.reject_proposal", "Rechazar la propuesta tecnica", "reject", {"task_id": str}, ("task_id",)),
         lambda song, revision, params: service.reject_song_spec_proposal(song, revision, params['task_id'])),
        (MusicTool("spec.restore", "Recuperar una revision", "restore", {"source_revision_id": str}, ("source_revision_id",)),
         lambda song, revision, params: service.restore_music_spec(song, {"revision_id": revision, **params})),
        (MusicTool("plan.read", "Leer el plan ACE-Step", "read", {}),
         lambda song, revision, params: service.latest_ace_step_plan(song)),
        (MusicTool("plan.prepare", "Preparar el plan ACE-Step", "propose", {"lyrics": str}),
         lambda song, revision, params: service.prepare_ace_step_plan(song, params)),
        (MusicTool("plan.approve", "Aprobar el plan y su letra", "confirm",
                   {"plan_id": str, "plan_sha256": str, "lyrics_confirmed": bool},
                   ("plan_id", "plan_sha256", "lyrics_confirmed")),
         lambda song, revision, params: service.approve_ace_step_plan(song, params.pop("plan_id"), params)),
        (MusicTool("candidate.start", "Generar audio autorizado", "execute",
                   {"plan_sha256": str, "exploratory_audio_authorized": bool, "request_id": str},
                   ("plan_sha256", "exploratory_audio_authorized")),
         lambda song, revision, params: service.ace_candidate_jobs.start(song, params)),
        (MusicTool("candidate.read", "Consultar la generacion", "read", {"task_id": str}, ("task_id",)),
         lambda song, revision, params: service.ace_candidate_jobs.get(song, params["task_id"])),
        (MusicTool("candidate.cancel", "Cancelar la generacion", "cancel", {"task_id": str}, ("task_id",)),
         lambda song, revision, params: service.ace_candidate_jobs.cancel(song, params["task_id"])),
    ]
    for tool, handler in entries:
        registry.register(tool, handler)
    return registry
