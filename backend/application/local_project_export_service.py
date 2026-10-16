from __future__ import annotations

from pathlib import Path
import re
import zipfile

from core.storage import StorageManager
from models.song_workflow import SongPhase, SongPhaseStatus
from application.final_production_gate import FinalProductionGate


class LocalProjectExportService:
    NON_FINAL_VOCAL_MODES = {"procedural_vocal_guide"}
    MEDIA_TYPES = {
        ".json": "application/json",
        ".md": "text/markdown",
        ".mid": "audio/midi",
        ".midi": "audio/midi",
        ".wav": "audio/wav",
        ".mp3": "audio/mpeg",
        ".flac": "audio/flac",
        ".zip": "application/zip",
        ".log": "text/plain",
    }

    def __init__(self, storage: StorageManager) -> None:
        self.storage = storage

    def list_artifacts(self, song_id: str) -> dict:
        project = self.storage.get_song_project(song_id)
        if project is None:
            raise ValueError('Proyecto no encontrado.')
        return {'song_id': song_id, 'artifacts': [self.storage.verify_song_artifact(
            song_id, str(artifact.get('type', ''))) for artifact in project.get('artifacts', [])]}

    def export(self, song_id: str) -> dict[str, object]:
        project = self.storage.get_song_project(song_id)
        if project is None:
            raise ValueError("Proyecto profesional no encontrado.")
        FinalProductionGate(self.storage).require_for_project(project)
        self._prepare_ace_export(project)
        project = self.storage.get_song_project(song_id) or project
        artifacts = self._owned_export_artifacts(song_id, project)
        required = self._required_artifacts(artifacts)
        available_types = {str(artifact["type"]) for artifact in artifacts}
        missing = sorted(required - available_types)
        if missing:
            raise ValueError("No se puede exportar todavia. Falta: " + ", ".join(missing))
        quality = self._quality_report(artifacts)
        if not bool(quality["export_ready"]):
            raise ValueError(str(quality["message"]))
        self._verify_export_artifacts(song_id, artifacts)

        project_dir = self.storage.data_dir / "projects" / song_id
        zip_artifact = self._create_project_zip(song_id, project_dir, artifacts)
        artifacts = self._owned_export_artifacts(song_id, self.storage.get_song_project(song_id) or project)
        quality = self._quality_report(artifacts)
        manifest_path = project_dir / "export_manifest.json"
        title = str(project.get("title", song_id))
        manifest = {
            "song_id": song_id,
            "title": title,
            "status": "export_ready",
            "source_of_truth": "sqlite",
            "quality": quality,
            "artifacts": [self._artifact_export_entry(song_id, artifact, quality) for artifact in artifacts],
        }
        self.storage.write_json(manifest_path, manifest)
        manifest_artifact = self.storage.create_song_artifact(
            artifact_id=f"{song_id}_export_manifest",
            song_id=song_id,
            phase=SongPhase.EXPORT.value,
            artifact_type="export_manifest_json",
            file_path=str(Path(manifest_path)),
            metadata={"artifact_count": len(artifacts), "source_of_truth": "sqlite"},
        )
        self.storage.create_song_event(
            song_id=song_id,
            phase=SongPhase.EXPORT.value,
            status=SongPhaseStatus.COMPLETED.value,
            progress=100,
            message="Export listo: artefactos finales disponibles para descarga.",
            active_model="export-service",
            payload={"manifest": str(manifest_path), "artifact_count": len(artifacts), "project_zip": zip_artifact["file_path"]},
            artifact_id=str(manifest_artifact["artifact_id"]),
        )
        project = self.storage.update_song_project_phase(song_id, SongPhase.EXPORT.value, SongPhaseStatus.COMPLETED.value)
        return {
            "project": project,
            "manifest": str(manifest_path),
            "artifacts": manifest["artifacts"],
            "quality": quality,
            "progress": {"current": 11, "total": 11, "label": "11. Export", "status": "completed"},
        }

    def _prepare_ace_export(self, project: dict[str, object]) -> None:
        final_wav = self._latest_final_full_song_artifact(list(project.get("artifacts", [])))
        metadata = dict(final_wav.get("metadata", {})) if final_wav else {}
        plan_id = str(metadata.get("ace_plan_id", ""))
        if not plan_id:
            return
        from adapters.ace_step_source_audio import AceStepSourceAudio
        from adapters.sqlite.ace_step_plan_repository import AceStepPlanRepository
        from application.ace_step_plan_compiler import PreviewAceStepPlan
        from application.ace_step_plan_review import ReviewAceStepPlan
        from application.music_spec_snapshot_export import export_music_spec

        song_id = str(project["id"])
        review = ReviewAceStepPlan(
            PreviewAceStepPlan(self.storage, AceStepSourceAudio(self.storage.data_dir)),
            AceStepPlanRepository(self.storage.db_path),
        )
        item = review.latest(song_id)
        plan = dict(item.get("plan", {})) if item else {}
        revision_id = str(dict(project["spec"])["revision"]["revision_id"])
        if (not item or item.get("effective_status") != "approved"
                or item.get("plan_id") != plan_id
                or plan.get("plan_sha256") != metadata.get("ace_plan_sha256")
                or plan.get("spec_revision_id") != revision_id
                or metadata.get("spec_revision_id") != revision_id):
            raise ValueError("El audio final no corresponde al plan ACE-Step aprobado y vigente.")

        folder = self.storage.data_dir / "projects" / song_id
        export_music_spec(self.storage, song_id)
        lyrics_path = folder / "lyrics.md"
        if not lyrics_path.is_file() or lyrics_path.read_text(encoding="utf-8") != plan["payload"]["lyrics"]:
            raise ValueError("La letra exportada no coincide con el plan ACE-Step aprobado.")
        plan_path = folder / "ace_plan.json"
        self.storage.write_json(plan_path, item)
        for kind, path in (("song_spec", folder / "song_spec.json"),
                           ("ace_plan_json", plan_path),
                           ("lyrics_markdown", lyrics_path)):
            self.storage.create_song_artifact(
                artifact_id=f"{song_id}_{kind}", song_id=song_id, phase=SongPhase.EXPORT.value,
                artifact_type=kind, file_path=str(path),
                metadata={"source_of_truth": "sqlite", "spec_revision_id": revision_id,
                          "ace_plan_id": plan_id, "ace_plan_sha256": plan["plan_sha256"],
                          "quality_status": "final_candidate_not_accepted"},
            )

    def _create_project_zip(self, song_id: str, project_dir: Path, artifacts: list[dict[str, object]]) -> dict[str, object]:
        project_root = project_dir.resolve()
        zip_path = project_root / "project_export.zip"
        with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zip_file:
            seen: set[Path] = set()
            for artifact in artifacts:
                artifact_type = str(artifact.get("type", ""))
                if artifact_type in {"project_zip", "export_manifest_json"}:
                    continue
                path = Path(str(artifact["file_path"])).resolve()
                if not path.exists() or path in seen:
                    continue
                if path == zip_path:
                    continue
                seen.add(path)
                zip_file.write(path, path.relative_to(project_root))
        return self.storage.create_song_artifact(
            artifact_id=f"{song_id}_project_zip",
            song_id=song_id,
            phase=SongPhase.EXPORT.value,
            artifact_type="project_zip",
            file_path=str(zip_path),
            metadata={"contains": len(artifacts), "source_of_truth": "sqlite"},
        )

    def _verify_export_artifacts(self, song_id: str, artifacts: list[dict[str, object]]) -> None:
        project_root = (self.storage.data_dir / "projects" / song_id).resolve()
        for artifact in artifacts:
            path = Path(str(artifact["file_path"])).resolve()
            if project_root not in path.parents or not path.is_file():
                raise ValueError("El artefacto exportable no existe dentro del proyecto activo.")
            expected = str(dict(artifact.get("metadata", {})).get("checksum", ""))
            if not expected or self.storage.file_checksum(path) != expected:
                raise ValueError("El checksum del artefacto exportable no coincide con SQLite: "
                                 + str(artifact.get("type", "")))

    def _owned_export_artifacts(self, song_id: str, project: dict[str, object]) -> list[dict[str, object]]:
        project_root = (self.storage.data_dir / "projects" / song_id).resolve()
        return [artifact for artifact in self._existing_artifacts(project)
                if project_root in Path(str(artifact["file_path"])).resolve().parents]

    def get(self, song_id: str) -> dict[str, object]:
        project = self.storage.get_song_project(song_id)
        if project is None:
            raise ValueError("Proyecto profesional no encontrado.")
        artifacts = self._existing_artifacts(project)
        quality = self._quality_report(artifacts)
        try:
            FinalProductionGate(self.storage).require_for_project(project)
        except ValueError as error:
            quality = {**quality, "export_ready": False, "message": str(error)}
        manifest_path = self.storage.data_dir / "projects" / song_id / "export_manifest.json"
        if manifest_path.exists():
            return {
                "song_id": song_id,
                "manifest": str(manifest_path),
                "quality": quality,
                "artifacts": [self._artifact_export_entry(song_id, artifact, quality) for artifact in artifacts],
            }
        return {
            "song_id": song_id,
            "manifest": "",
            "quality": quality,
            "artifacts": [self._artifact_export_entry(song_id, artifact, quality) for artifact in artifacts],
        }

    def download_file(self, song_id: str, artifact_type: str) -> tuple[Path, str, str]:
        project = self.storage.get_song_project(song_id)
        if project is None:
            raise ValueError("Proyecto profesional no encontrado.")
        if self._is_final_download(artifact_type):
            FinalProductionGate(self.storage).require_for_project(project)
        artifacts = self._existing_artifacts(project)
        quality = self._quality_report(artifacts)
        if self._is_final_download(artifact_type) and not bool(quality["export_ready"]):
            raise ValueError(str(quality["message"]))
        matches = [artifact for artifact in artifacts if str(artifact["type"]) == artifact_type]
        if not matches:
            raise ValueError(f"No existe artefacto exportable de tipo {artifact_type}.")
        verification = self.storage.verify_song_artifact(song_id, artifact_type)
        if str(verification.get("artifact_status", "")) != "GENERATED":
            raise ValueError(str(verification.get("message", "El artefacto no esta disponible para descarga.")))
        artifact = matches[-1]
        path = Path(str(artifact["file_path"])).resolve()
        project_dir = (self.storage.data_dir / "projects" / song_id).resolve()
        if project_dir not in path.parents or not path.is_file():
            raise ValueError("El artefacto no existe dentro del proyecto activo.")
        extension = path.suffix.lower()
        filename = f"{self._safe_name(str(project.get('title', song_id)))}-{artifact_type}{extension}"
        return path, filename, self.MEDIA_TYPES.get(extension, "application/octet-stream")

    def _existing_artifacts(self, project: dict[str, object]) -> list[dict[str, object]]:
        artifacts = []
        for artifact in list(project.get("artifacts", [])):
            path = Path(str(dict(artifact).get("file_path", "")))
            if path.exists():
                artifacts.append(dict(artifact))
        return artifacts

    def _artifact_export_entry(
        self,
        song_id: str,
        artifact: dict[str, object],
        quality: dict[str, object] | None = None,
    ) -> dict[str, object]:
        artifact_type = str(artifact["type"])
        path = Path(str(artifact["file_path"]))
        final_blocked = bool(quality) and self._is_final_download(artifact_type) and not bool(quality.get("export_ready"))
        metadata = dict(artifact.get("metadata", {}))
        if final_blocked:
            metadata["quality_blocked"] = True
            metadata["quality_message"] = str(quality.get("message", ""))
        return {
            "artifact_id": str(artifact["artifact_id"]),
            "type": artifact_type,
            "phase": str(artifact["phase"]),
            "file_path": str(path),
            "size_bytes": path.stat().st_size if path.exists() else 0,
            "download_url": "" if final_blocked else f"/api/pro/projects/{song_id}/artifacts/{artifact_type}/download",
            "metadata": metadata,
            "created_at": str(artifact.get("created_at", "")),
        }

    def _quality_report(self, artifacts: list[dict[str, object]]) -> dict[str, object]:
        full_song = self._latest_final_full_song_artifact(artifacts)
        if full_song:
            mode = str(dict(full_song.get("metadata", {})).get("generation_mode", "local_full_song_command"))
            return {
                "export_ready": True,
                "vocal_mode": "full_song_provider",
                "generation_mode": mode,
                "message": "Audio generado por un provider full-song local. Su procedencia no acredita calidad audible ni aceptacion del usuario.",
            }
        vocals = self._latest_artifact(artifacts, "vocals_wav")
        if not vocals:
            return {
                "export_ready": False,
                "vocal_mode": "",
                "message": "No se puede exportar como final: falta vocals.wav.",
            }
        metadata = dict(vocals.get("metadata", {}))
        mode = str(metadata.get("mode", "unknown"))
        if mode in self.NON_FINAL_VOCAL_MODES:
            return {
                "export_ready": False,
                "vocal_mode": mode,
                "message": (
                    "No se puede exportar como final: vocals.wav es una guia vocal procedural, "
                    "no una voz cantada real. Configura SONG_AI_SINGING_VOICE_COMMAND o usa un provider full-song real."
                ),
            }
        return {
            "export_ready": True,
            "vocal_mode": mode,
            "message": "Voz generada por un provider local configurado. Su procedencia no acredita calidad audible ni aceptacion del usuario.",
        }

    def _latest_artifact(self, artifacts: list[dict[str, object]], artifact_type: str) -> dict[str, object] | None:
        matches = [artifact for artifact in artifacts if str(artifact.get("type", "")) == artifact_type]
        return matches[-1] if matches else None

    def _latest_final_full_song_artifact(self, artifacts: list[dict[str, object]]) -> dict[str, object] | None:
        matches = [
            artifact
            for artifact in artifacts
            if str(artifact.get("type", "")) == "final_song_wav"
            and dict(artifact.get("metadata", {})).get("generation_mode") == "local_full_song_command"
        ]
        return matches[-1] if matches else None

    def _required_artifacts(self, artifacts: list[dict[str, object]]) -> set[str]:
        base = {"song_spec", "lyrics_json", "lyrics_approved_json", "music_plan_json", "midi"}
        final = {"final_song_wav", "final_song_mp3", "final_song_flac"}
        full_song = self._latest_final_full_song_artifact(artifacts)
        if full_song and dict(full_song.get("metadata", {})).get("ace_plan_id"):
            return {"song_spec", "ace_plan_json", "lyrics_markdown"} | final
        if full_song:
            return base | final
        return base | {"instrumental_wav", "vocals_wav", "mix_wav"} | final

    def _is_final_download(self, artifact_type: str) -> bool:
        return artifact_type in {"final_song_mp3", "final_song_wav", "final_song_flac", "project_zip"}

    def _safe_name(self, value: str) -> str:
        normalized = re.sub(r"[^A-Za-z0-9._-]+", "_", value.strip()).strip("._-")
        return normalized or "song-ai"
