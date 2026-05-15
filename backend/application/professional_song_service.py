from __future__ import annotations

from core.storage import StorageManager
from models.song_workflow import PHASE_LABELS, PHASE_SEQUENCE


class ProfessionalSongService:
    def __init__(self, storage: StorageManager) -> None:
        self.storage = storage

    def phases(self) -> list[dict[str, object]]:
        total = len(PHASE_SEQUENCE)
        return [
            {
                "number": index,
                "total": total,
                "phase": phase.value,
                "label": PHASE_LABELS[phase],
                "required": phase.value != "VOICE_CONVERSION",
            }
            for index, phase in enumerate(PHASE_SEQUENCE, start=1)
        ]

    def create_project(self, payload: dict[str, object]) -> dict[str, object]:
        title = str(payload.get("title") or payload.get("project_name") or "Nueva cancion")
        user_id = str(payload.get("user_id") or "local-user")
        project = self.storage.create_song_project(title=title, user_id=user_id)
        return {
            "project": project,
            "phases": self.phases(),
            "progress": self.progress_for(project),
        }

    def list_projects(self) -> dict[str, object]:
        projects = self.storage.list_song_projects()
        return {
            "projects": projects,
            "phases": self.phases(),
        }

    def get_project(self, song_id: str) -> dict[str, object]:
        project = self.storage.get_song_project(song_id)
        if project is None:
            raise ValueError("Proyecto profesional no encontrado.")
        return {
            "project": project,
            "phases": self.phases(),
            "progress": self.progress_for(project),
        }

    def list_events(self, song_id: str) -> dict[str, object]:
        if self.storage.get_song_project(song_id) is None:
            raise ValueError("Proyecto profesional no encontrado.")
        return {
            "song_id": song_id,
            "events": self.storage.list_song_project_events(song_id),
        }

    def progress_for(self, project: dict[str, object]) -> dict[str, object]:
        current_phase = str(project.get("current_phase", PHASE_SEQUENCE[0].value))
        total = len(PHASE_SEQUENCE)
        index_by_phase = {phase.value: index for index, phase in enumerate(PHASE_SEQUENCE, start=1)}
        current_number = index_by_phase.get(current_phase, 1)
        return {
            "current": current_number,
            "total": total,
            "label": PHASE_LABELS.get(PHASE_SEQUENCE[current_number - 1], "Fase desconocida"),
            "status": str(project.get("status", "pending")),
        }
