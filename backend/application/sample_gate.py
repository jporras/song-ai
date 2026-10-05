"""Shared final-generation checks against the active persisted set and sample."""
from typing import Protocol


class SampleGateStore(Protocol):
    def get_indexed_set(self, set_id: str) -> dict | None: ...
    def validate_song_set_assets(self, instrumental_id: str, melody_id: str, lyrics_id: str): ...
    def set_generation_fingerprint(self, set_id: str) -> str: ...
    def list_samples_for_set(self, set_id: str) -> list[dict]: ...
    def verify_sample_audio(self, sample: dict) -> dict: ...


class SampleGate:
    def __init__(self, store: SampleGateStore):
        self.store = store

    def require_for_project(self, project: dict, *, real_output: bool = True) -> dict:
        owner = str(project.get("user_id", ""))
        if not owner.startswith("set:") or not owner[4:].strip():
            raise ValueError("Vincula el proyecto a un set valido y genera su sample antes de producir la cancion completa.")
        return self.require_for_set(owner[4:].strip(), real_output=real_output)

    def require_for_set(self, set_id: str, *, real_output: bool, sample_id: str | None = None) -> dict:
        song_set = self.store.get_indexed_set(set_id)
        if song_set is None:
            raise ValueError("El proyecto necesita un set valido en SQLite antes de producir la cancion completa.")
        self.store.validate_song_set_assets(*(str(song_set[key]) for key in
                                             ("instrumental_id", "melody_id", "lyrics_id")))
        fingerprint = self.store.set_generation_fingerprint(set_id)
        samples = self.store.list_samples_for_set(set_id)
        failure = "Primero crea y revisa un sample del set activo."
        for sample in samples:
            if sample_id is not None and str(sample.get("sample_id")) != sample_id:
                continue
            if sample.get("set_id") != set_id:
                continue
            if sample.get("approval_status") != "approved":
                failure = "Primero escucha y aprueba el sample del set activo."
                continue
            if sample.get("approved_set_fingerprint") != fingerprint:
                failure = "El sample aprobado esta desactualizado. Regeneralo y vuelve a aprobarlo."
                continue
            if sample.get("audio_evidence"):
                try:
                    evidence = self.store.verify_sample_audio(sample)
                    if sample.get("approved_audio_sha256") != evidence.get("sha256"):
                        raise ValueError("El audio actual no coincide con el sample aprobado; vuelve a aprobarlo.")
                except ValueError as error:
                    failure = str(error)
                    continue
            if real_output:
                # Real-sample provenance and artifact verification are not implemented yet.
                # Fail closed until that contract can be checked from SQLite and the audio.
                raise ValueError("La produccion real requiere un sample de audio real verificado y aprobado. "
                                 "El checkpoint actual no acredita esa calidad; completa la generacion y verificacion del sample real.")
            return sample
        raise ValueError(failure)
