from pathlib import Path

from datetime import datetime, timezone

from audio.formats import planned_final_mix_exports, planned_stem_exports
from core.storage import StorageManager
from utils.ids import generate_id
from application.final_production_gate import FinalProductionGate


class FullSongBuilder:
    def __init__(self, storage: StorageManager) -> None:
        self.storage = storage

    def create_from_latest_sample(self) -> Path:
        song_set = self.storage.get_latest_song_set()
        if song_set is None:
            raise ValueError("No hay set valido. Prepara instrumental, melodia vocal y letra antes de crear la cancion.")
        return self.create_for_set(str(song_set["set_id"]))

    def create_for_set(self, set_id: str, sample_id: str | None = None) -> Path:
        linked = [project for project in self.storage.list_song_projects()
                  if project.get("user_id") == f"set:{set_id}"]
        if len(linked) != 1:
            raise ValueError("Prepara una ficha unica vinculada al set y confirma el request antes de crear la cancion.")
        project = self.storage.get_song_project(str(linked[0]["id"]))
        FinalProductionGate(self.storage).require_for_project(project)
        if sample_id:
            samples = [sample for sample in self.storage.list_samples_for_set(set_id)
                       if sample.get("sample_id") == sample_id]
            if not samples:
                raise ValueError("El sample indicado no pertenece al set activo.")

        song_id = generate_id("song")
        song_dir = self.storage.data_dir / "songs" / song_id
        exports_dir = song_dir / "exports"
        stems_dir = song_dir / "stems"
        song_dir.mkdir(parents=True, exist_ok=True)
        exports_dir.mkdir(parents=True, exist_ok=True)
        stems_dir.mkdir(parents=True, exist_ok=True)
        self.storage.save_legacy_song(
            {
                "song_id": song_id,
                "sample_id": sample_id or "",
                "sample_evidence_status": "not_required_unverified",
                "set_id": set_id,
                "source_project_id": project["id"],
                "request_revision_id": project["spec"]["revision"]["revision_id"],
                "request_fingerprint": self.storage.set_generation_fingerprint(set_id),
                "provider": "mock-local",
                "status": "mock_complete_song_pipeline",
                "scope": "complete_lullaby_or_children_emotional_song",
                "priority_order": [
                    "good_lyrics",
                    "emotional_intent",
                    "musical_structure",
                    "coherent_soundtrack",
                    "sung_voice",
                    "final_mix",
                ],
                "required_pipeline": {
                    "interpreter": "Gemma 2 2B IT GGUF via llama.cpp",
                    "lyrics": "Gemma 2 2B IT GGUF via llama.cpp",
                    "technical": "Qwen3 4B GGUF via llama.cpp",
                    "soundtrack": "MusicGen small, MusicGen medium if hardware allows",
                    "singing_voice": "RVC / ACE-Step, so-vits-svc optional",
                    "stems": "Demucs",
                    "mixer": "ffmpeg",
                },
                "restrictions": {
                    "not_short_format": True,
                    "avoid_poor_repetition": True,
                    "voice_must_be_sung": True,
                    "video_optional": True,
                    "load_models_on_demand": True,
                },
                "exports_dir": str(exports_dir),
                "stems_dir": str(stems_dir),
                "planned_exports": planned_final_mix_exports(),
                "planned_stems": planned_stem_exports(),
                "mock_exports": [
                    "exports/final_mix.mock.txt",
                    "exports/README.md",
                ],
                "created_at": datetime.now(timezone.utc).isoformat(),
            },
            song_dir / "song.json",
        )
        (exports_dir / "final_mix.mock.txt").write_text(
            "Mock full song placeholder.\n"
            f"Sample opcional: {sample_id or 'ninguno'} (sin acreditar calidad)\n"
            f"Set: {set_id}\n"
            "Scope: complete lullaby / emotional children song.\n"
            "Pipeline: lyrics, structure, soundtrack, sung voice, stems, mix, WAV/MP3 export.\n"
            "Video is optional and not required for song completion.\n",
            encoding="utf-8",
        )
        (exports_dir / "README.md").write_text(
            "# Song Exports\n\n"
            "Aqui quedaran los archivos reales cuando exista el pipeline de audio:\n\n"
            "- `final_mix.mp3`\n"
            "- `final_mix.m4a`\n"
            "- `final_mix.ogg`\n"
            "- `final_mix.wav`\n"
            "- `final_mix.flac`\n"
            "- `final_mix.aiff`\n"
            "- `lyrics.md`\n"
            "- `manifest.json`\n\n"
            "MP3/M4A/OGG son formatos comprimidos para distribucion. WAV/FLAC/AIFF son formatos de alta calidad o lossless.\n\n"
            "La cancion final debe ser una pieza completa con letra original, estructura musical, soundtrack, voz cantada y mezcla.\n"
            "No se considera completo un Short, una repeticion simple o TTS hablado.\n\n"
            "En esta fase mock solo se genera `final_mix.mock.txt`.\n",
            encoding="utf-8",
        )
        (stems_dir / "README.md").write_text(
            "# Song Stems\n\n"
            "Aqui quedaran stems reales cuando exista el pipeline de audio:\n\n"
            "- `instrumental.wav`\n"
            "- `vocals.wav`\n"
            "- `melody_guide.wav`\n"
            "- `drums.wav`\n"
            "- `bass.wav`\n"
            "- `music.wav`\n"
            "- versiones `.flac` cuando se requiera compresion lossless.\n"
            "- `demucs/` para separaciones futuras cuando el pipeline use Demucs.\n",
            encoding="utf-8",
        )
        return song_dir

