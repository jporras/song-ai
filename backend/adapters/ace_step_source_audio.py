"""Resolve source audio from project artifacts; never trust an arbitrary request path."""
from pathlib import Path

from adapters.sample_audio_evidence import inspect_sample_wav


class AceStepSourceAudio:
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir

    def inspect(self, project: dict, artifact_id: str, requested_path: str) -> dict:
        matches = [item for item in project.get("artifacts", [])
                   if item.get("artifact_id") == artifact_id and item.get("song_id") == project.get("id")]
        if len(matches) != 1:
            raise ValueError("Selecciona un artefacto de audio del proyecto activo.")
        path = Path(matches[0]["file_path"])
        if path.resolve() != Path(requested_path).resolve():
            raise ValueError("La ruta fuente no coincide con el artefacto seleccionado.")
        directory = self.data_dir / "projects" / str(project["id"])
        try:
            evidence = inspect_sample_wav(path, directory)
        except ValueError as error:
            raise ValueError(str(error).replace("del sample", "fuente")) from error
        return {**evidence, "artifact_id": artifact_id, "song_id": project["id"],
                "file_path": str(path.resolve()), "technical_integrity_verified": True,
                "musical_quality_verified": False}
