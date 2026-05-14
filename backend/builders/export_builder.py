from pathlib import Path
import shutil
import subprocess

from audio.formats import planned_final_mix_exports, planned_stem_exports
from audio.mock_song_renderer import MockSongRenderer, MockSongRenderContext
from core.storage import StorageManager


class ExportBuilder:
    def __init__(self, storage: StorageManager) -> None:
        self.storage = storage
        self.renderer = MockSongRenderer()

    def prepare_latest_song_exports(self) -> Path:
        latest_song = self.storage.get_latest_song()
        if latest_song is None:
            raise ValueError("No hay cancion completa para exportar.")

        song_dir = Path(str(latest_song["path"]))
        exports_dir = song_dir / "exports"
        stems_dir = song_dir / "stems"
        exports_dir.mkdir(parents=True, exist_ok=True)
        stems_dir.mkdir(parents=True, exist_ok=True)

        context = self._load_render_context(latest_song)

        self.storage.write_json(
            exports_dir / "manifest.json",
            {
                "song_id": latest_song["song_id"],
                "set_id": latest_song.get("set_id", ""),
                "project_name": context.project_name,
                "mode": "mock_song_export",
                "final_mix_formats": planned_final_mix_exports(),
                "stem_formats": planned_stem_exports(),
                "intent_snapshot": {
                    "instrumental": context.instrumental_intent,
                    "melody": context.melody_intent,
                    "lyrics": context.lyrics_intent,
                },
            },
        )
        (exports_dir / "lyrics.md").write_text(context.lyrics_markdown.rstrip() + "\n", encoding="utf-8")
        return exports_dir

    def generate_latest_song_audio_exports(self) -> Path:
        latest_song = self.storage.get_latest_song()
        if latest_song is None:
            raise ValueError("No hay cancion completa para exportar.")

        song_dir = Path(str(latest_song["path"]))
        exports_dir = self.prepare_latest_song_exports()
        stems_dir = song_dir / "stems"
        mp3_path = exports_dir / "final_mix.mp3"
        pending_path = exports_dir / "final_mix.mp3.pending.txt"
        if mp3_path.exists():
            mp3_path.unlink()
        if pending_path.exists():
            pending_path.unlink()
        render = self.renderer.render(self._load_render_context(latest_song), exports_dir, stems_dir)
        wav_path = Path(str(render["wav"]))

        ffmpeg_path = shutil.which("ffmpeg")
        mp3_generated = False
        if ffmpeg_path:
            try:
                subprocess.run(
                    [
                        ffmpeg_path,
                        "-y",
                        "-hide_banner",
                        "-loglevel",
                        "error",
                        "-i",
                        str(wav_path),
                        str(mp3_path),
                    ],
                    check=True,
                )
                mp3_generated = True
            except subprocess.CalledProcessError:
                mp3_generated = False

        if not mp3_generated:
            pending_path.write_text(
                "MP3 pendiente: instala ffmpeg o usa el contenedor con ffmpeg para convertir final_mix.wav.\n",
                encoding="utf-8",
            )

        self.storage.write_json(
            exports_dir / "audio_export_manifest.json",
            {
                "song_id": latest_song["song_id"],
                "set_id": latest_song.get("set_id", ""),
                "mode": render["mode"],
                "source_song_dir": str(song_dir),
                "wav": str(wav_path),
                "mp3": str(mp3_path) if mp3_generated else "",
                "mp3_pending": not mp3_generated,
                "ffmpeg_available": ffmpeg_path is not None,
                "ffmpeg_path": ffmpeg_path or "",
                "duration_seconds": render["duration_seconds"],
                "lyric_lines_used": render["lyric_lines_used"],
                "stems": render["stems"],
                "note": render["note"],
            },
        )
        return exports_dir

    def _load_render_context(self, song: dict[str, object]) -> MockSongRenderContext:
        return self.load_render_context(song)

    def load_render_context(self, song: dict[str, object]) -> MockSongRenderContext:
        set_id = str(song.get("set_id", ""))
        song_set = self.storage.get_indexed_set(set_id)
        if song_set is None:
            set_path = self.storage.data_dir / "sets" / set_id / "set.json"
            if not set_path.exists():
                raise ValueError("Set no encontrado para exportar audio.")
            song_set = self.storage.read_json(set_path)

        instrumental = self.storage.get_asset_draft_detail(str(song_set["instrumental_id"]))
        melody = self.storage.get_asset_draft_detail(str(song_set["melody_id"]))
        lyrics = self.storage.get_asset_draft_detail(str(song_set["lyrics_id"]))
        lyrics_markdown = str(lyrics.get("content", "")).strip()
        if not lyrics_markdown:
            raise ValueError("El set no tiene lyrics.md valido para exportar la cancion.")

        return MockSongRenderContext(
            project_name=str(song_set.get("project_name", set_id)),
            description=str(song_set.get("description", "")),
            instrumental_intent=dict(instrumental.get("intent", {})),
            melody_intent=dict(melody.get("intent", {})),
            lyrics_intent=dict(lyrics.get("intent", {})),
            lyrics_markdown=lyrics_markdown,
        )
