from __future__ import annotations

from pathlib import Path
import re
import zipfile

from core.storage import StorageManager
from models.song_workflow import SongPhase, SongPhaseStatus


class ProfessionalExportService:
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

    def export(self, song_id: str) -> dict[str, object]:
        project = self.storage.get_song_project(song_id)
        if project is None:
            raise ValueError("Proyecto profesional no encontrado.")
        artifacts = self._existing_artifacts(project)
        required = {"song_spec", "lyrics_json", "lyrics_approved_json", "music_plan_json", "midi", "instrumental_wav", "vocals_wav", "mix_wav", "final_song_wav", "final_song_mp3", "final_song_flac"}
        available_types = {str(artifact["type"]) for artifact in artifacts}
        missing = sorted(required - available_types)
        if missing:
            raise ValueError("No se puede exportar todavia. Falta: " + ", ".join(missing))

        project_dir = self.storage.data_dir / "projects" / song_id
        zip_artifact = self._create_project_zip(song_id, project_dir, artifacts)
        artifacts = self._existing_artifacts(self.storage.get_song_project(song_id) or project)
        manifest_path = project_dir / "export_manifest.json"
        title = str(project.get("title", song_id))
        manifest = {
            "song_id": song_id,
            "title": title,
            "status": "export_ready",
            "source_of_truth": "sqlite",
            "artifacts": [self._artifact_export_entry(song_id, artifact) for artifact in artifacts],
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
            "progress": {"current": 11, "total": 11, "label": "11. Export", "status": "completed"},
        }

    def _create_project_zip(self, song_id: str, project_dir: Path, artifacts: list[dict[str, object]]) -> dict[str, object]:
        zip_path = project_dir / "project_export.zip"
        with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zip_file:
            seen: set[Path] = set()
            for artifact in artifacts:
                path = Path(str(artifact["file_path"]))
                if not path.exists() or path in seen:
                    continue
                seen.add(path)
                zip_file.write(path, path.relative_to(project_dir))
        return self.storage.create_song_artifact(
            artifact_id=f"{song_id}_project_zip",
            song_id=song_id,
            phase=SongPhase.EXPORT.value,
            artifact_type="project_zip",
            file_path=str(zip_path),
            metadata={"contains": len(artifacts), "source_of_truth": "sqlite"},
        )

    def get(self, song_id: str) -> dict[str, object]:
        project = self.storage.get_song_project(song_id)
        if project is None:
            raise ValueError("Proyecto profesional no encontrado.")
        manifest_path = self.storage.data_dir / "projects" / song_id / "export_manifest.json"
        if manifest_path.exists():
            manifest = self.storage.read_json(manifest_path)
            return {
                "song_id": song_id,
                "manifest": str(manifest_path),
                "artifacts": manifest.get("artifacts", []),
            }
        return {
            "song_id": song_id,
            "manifest": "",
            "artifacts": [self._artifact_export_entry(song_id, artifact) for artifact in self._existing_artifacts(project)],
        }

    def download_file(self, song_id: str, artifact_type: str) -> tuple[Path, str, str]:
        project = self.storage.get_song_project(song_id)
        if project is None:
            raise ValueError("Proyecto profesional no encontrado.")
        artifacts = self._existing_artifacts(project)
        matches = [artifact for artifact in artifacts if str(artifact["type"]) == artifact_type]
        if not matches:
            raise ValueError(f"No existe artefacto exportable de tipo {artifact_type}.")
        artifact = matches[-1]
        path = Path(str(artifact["file_path"])).resolve()
        project_dir = (self.storage.data_dir / "projects" / song_id).resolve()
        if not str(path).startswith(str(project_dir)) or not path.exists():
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

    def _artifact_export_entry(self, song_id: str, artifact: dict[str, object]) -> dict[str, object]:
        artifact_type = str(artifact["type"])
        path = Path(str(artifact["file_path"]))
        return {
            "artifact_id": str(artifact["artifact_id"]),
            "type": artifact_type,
            "phase": str(artifact["phase"]),
            "file_path": str(path),
            "size_bytes": path.stat().st_size if path.exists() else 0,
            "download_url": f"/api/pro/projects/{song_id}/artifacts/{artifact_type}/download",
            "metadata": dict(artifact.get("metadata", {})),
            "created_at": str(artifact.get("created_at", "")),
        }

    def _safe_name(self, value: str) -> str:
        normalized = re.sub(r"[^A-Za-z0-9._-]+", "_", value.strip()).strip("._-")
        return normalized or "song-ai"
