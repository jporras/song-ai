"""Local specification queries and confirmation, independent of paid workflows."""
from application.song_specification_service import SongSpecificationService
from models.song_workflow import PHASE_LABELS, PHASE_SEQUENCE, SongPhase, SongPhaseStatus
from typing import Protocol


class MusicSpecRevisionStore(Protocol):
    def get_song_project(self, song_id): ...
    def list_song_spec_revisions(self, song_id): ...
    def upsert_song_spec(self, **kwargs): ...
    def create_song_event(self, **kwargs): ...
    def update_song_project_phase(self, song_id, phase, status): ...


def require_confirmed_music_spec(project):
    record = project.get('spec')
    if not isinstance(record, dict):
        raise ValueError('Completa la ficha de la cancion antes de continuar.')
    revision = record.get('revision', {})
    if revision.get('user_confirmation_status') != 'confirmed':
        raise ValueError('Revisa y confirma la ficha completa de la cancion antes de continuar.')
    if not revision.get('deterministic_valid') or record.get('missing_fields'):
        raise ValueError('La ficha confirmada tiene datos pendientes; crea y confirma una revision valida.')
    return record


class MusicSpecRevisionService:
    def __init__(self, storage: MusicSpecRevisionStore):
        self.storage = storage
        self.song_specifications = SongSpecificationService()

    def confirm_song_specification(self, song_id: str, payload: dict[str, object]) -> dict[str, object]:
        project = self.storage.get_song_project(song_id)
        if project is None:
            raise ValueError("Proyecto profesional no encontrado.")
        record = project.get("spec")
        if not isinstance(record, dict):
            raise ValueError("La especificacion aun no existe.")
        revision = dict(record.get("revision", {}))
        requested_revision = str(payload.get("revision_id", "")).strip()
        if not requested_revision or requested_revision != str(revision.get("revision_id", "")):
            raise ValueError("La revision cambio. Recarga la ficha antes de confirmarla.")
        if not bool(revision.get("deterministic_valid")) or record.get("missing_fields"):
            raise ValueError("La especificacion tiene datos pendientes y no se puede confirmar.")
        confirmed = self.storage.upsert_song_spec(
            song_id=song_id,
            json_spec=dict(record.get("json_spec", {})),
            approved_by_qwen=bool(record.get("approved_by_qwen")),
            missing_fields=list(record.get("missing_fields", [])),
            schema_version=str(revision.get("schema_version", "1.0")),
            technical_review_mode=str(revision.get("technical_review_mode", "rule_validation")),
            user_confirmation_status="confirmed",
            deterministic_valid=revision.get('deterministic_valid') is True,
            expected_revision_id=requested_revision,
        )
        self.storage.create_song_event(
            song_id=song_id,
            phase=SongPhase.SONG_SPEC_COLLECTION.value,
            status=SongPhaseStatus.READY.value,
            progress=100,
            message="El usuario confirmo la revision activa de la especificacion.",
            active_model="user",
            payload={"confirmed_revision_id": requested_revision, "active_revision": confirmed.get("revision", {})},
        )
        project = self.storage.update_song_project_phase(
            song_id,
            SongPhase.LYRICS_GENERATION.value,
            SongPhaseStatus.READY.value,
        )
        response = self.get_song_specification(song_id)
        response["project"] = project
        response["progress"] = self.progress_for(project)
        return response

    def get_song_specification(self, song_id: str) -> dict[str, object]:
        project = self.storage.get_song_project(song_id)
        if project is None:
            raise ValueError("Proyecto profesional no encontrado.")
        record = project.get("spec")
        spec = dict(record.get("json_spec", {})) if isinstance(record, dict) else {}
        return {
            "song_id": song_id,
            "spec": record,
            "catalog": self.song_specifications.catalog(spec),
            "revisions": self.storage.list_song_spec_revisions(song_id),
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
