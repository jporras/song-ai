from pathlib import Path
import os
from threading import Lock, Thread
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from application.song_service import SongService
from bootstrap.docker_bootstrap import run_bootstrap
from config.settings import Settings
from core.storage import StorageManager


PROJECT_ROOT = Path(__file__).resolve().parents[3]
FRONTEND_SOURCE_DIR = PROJECT_ROOT / "frontend"
FRONTEND_DIST_DIR = FRONTEND_SOURCE_DIR / "dist"
FRONTEND_DIR = FRONTEND_DIST_DIR if FRONTEND_DIST_DIR.exists() else FRONTEND_SOURCE_DIR

settings = Settings.load()
storage = StorageManager(settings.data_dir)
service = SongService(storage, settings)
service.bootstrap()


class BootstrapRunner:
    def __init__(self) -> None:
        self.lock = Lock()
        self.state: dict[str, Any] = {
            "status": "idle",
            "message": "Bootstrap no iniciado desde la UI.",
            "result": {},
        }

    def status(self) -> dict[str, Any]:
        with self.lock:
            return dict(self.state)

    def start(self, upgrade: bool = False) -> dict[str, Any]:
        with self.lock:
            if self.state["status"] == "running":
                return dict(self.state)
            self.state = {
                "status": "running",
                "message": "Bootstrap actualizando dependencias en segundo plano." if upgrade else "Bootstrap ejecutandose en segundo plano.",
                "upgrade": upgrade,
                "result": {},
            }
        thread = Thread(target=self._run, kwargs={"upgrade": upgrade}, daemon=True)
        thread.start()
        return self.status()

    def _run(self, upgrade: bool = False) -> None:
        try:
            result = run_bootstrap(force=True, upgrade=upgrade)
            state = {
                "status": "ready",
                "message": "Bootstrap actualizado." if upgrade else "Bootstrap finalizado.",
                "upgrade": upgrade,
                "result": result,
            }
        except Exception as error:
            state = {
                "status": "error",
                "message": str(error),
                "upgrade": upgrade,
                "result": {},
            }
        with self.lock:
            self.state = state


bootstrap_runner = BootstrapRunner()

app = FastAPI(title="Song AI Generator API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def start_bootstrap_on_startup() -> None:
    if os.getenv("SONG_AI_BOOTSTRAP_ON_START", "false").strip().lower() in {"1", "true", "yes", "on"}:
        bootstrap_runner.start()


def ok(data: Any) -> dict[str, Any]:
    return {"ok": True, "data": data}


def run_action(action) -> dict[str, Any]:
    try:
        return ok(action())
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@app.get("/api/options")
def get_options() -> dict[str, Any]:
    return ok(service.options())


@app.get("/api/drafts")
def get_drafts() -> dict[str, Any]:
    return ok(service.list_drafts())


@app.get("/api/sets")
def get_sets() -> dict[str, Any]:
    return ok(service.list_sets())


@app.get("/api/sets/{set_id}")
def get_set(set_id: str) -> dict[str, Any]:
    return run_action(lambda: service.get_set(set_id))


@app.get("/api/favorites")
def get_favorites() -> dict[str, Any]:
    return ok(service.list_favorites())


@app.get("/api/providers")
def get_providers() -> dict[str, Any]:
    return ok(service.providers())


@app.get("/api/models/status")
def get_model_status() -> dict[str, Any]:
    return ok(service.model_status())


@app.get("/api/studio/status")
def get_studio_status() -> dict[str, Any]:
    return ok(service.studio_status())


@app.get("/api/local-pipeline/status")
def get_local_pipeline_status() -> dict[str, Any]:
    return ok(service.local_pipeline_status())


@app.get("/api/system/status")
def get_system_status() -> dict[str, Any]:
    return ok(service.system_status(bootstrap_runner.status()))


@app.post("/api/system/bootstrap/restart")
def restart_bootstrap() -> dict[str, Any]:
    return ok(bootstrap_runner.start())


@app.post("/api/system/bootstrap/upgrade")
def upgrade_bootstrap() -> dict[str, Any]:
    return ok(bootstrap_runner.start(upgrade=True))


@app.get("/api/projects/phases")
def get_project_phases(set_id: str | None = None) -> dict[str, Any]:
    return ok(service.project_phase_status(set_id))


@app.get("/api/pro/phases")
def get_professional_phases() -> dict[str, Any]:
    return ok(service.professional_phases())


@app.get("/api/pro/projects")
def get_professional_projects() -> dict[str, Any]:
    return ok(service.list_professional_projects())


@app.post("/api/pro/projects")
def create_professional_project(payload: dict[str, Any]) -> dict[str, Any]:
    return run_action(lambda: service.create_professional_project(payload))


@app.get("/api/pro/projects/{song_id}")
def get_professional_project(song_id: str) -> dict[str, Any]:
    return run_action(lambda: service.get_professional_project(song_id))


@app.get("/api/pro/projects/{song_id}/events")
def get_professional_project_events(song_id: str) -> dict[str, Any]:
    return run_action(lambda: service.list_professional_project_events(song_id))


@app.post("/api/pro/projects/{song_id}/spec/messages")
def collect_professional_spec(song_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    return run_action(lambda: service.collect_professional_spec(song_id, payload))


@app.post("/api/pro/projects/{song_id}/lyrics")
def generate_professional_lyrics(song_id: str) -> dict[str, Any]:
    return run_action(lambda: service.generate_professional_lyrics(song_id))


@app.get("/api/pro/projects/{song_id}/lyrics")
def get_professional_lyrics(song_id: str) -> dict[str, Any]:
    return run_action(lambda: service.get_professional_lyrics(song_id))


@app.put("/api/pro/projects/{song_id}/lyrics")
def update_professional_lyrics(song_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    return run_action(lambda: service.update_professional_lyrics(song_id, payload))


@app.post("/api/pro/projects/{song_id}/lyrics/review")
def review_professional_lyrics(song_id: str) -> dict[str, Any]:
    return run_action(lambda: service.review_professional_lyrics(song_id))


@app.post("/api/pro/projects/{song_id}/music-plan")
def generate_professional_music_plan(song_id: str) -> dict[str, Any]:
    return run_action(lambda: service.generate_professional_music_plan(song_id))


@app.get("/api/pro/projects/{song_id}/music-plan")
def get_professional_music_plan(song_id: str) -> dict[str, Any]:
    return run_action(lambda: service.get_professional_music_plan(song_id))


@app.get("/api/projects/{set_id}")
def get_project(set_id: str) -> dict[str, Any]:
    return run_action(lambda: service.get_project(set_id))


@app.get("/api/orchestration/status")
def get_orchestration_status() -> dict[str, Any]:
    return ok(service.orchestration_status())


@app.get("/api/tasks")
def get_tasks() -> dict[str, Any]:
    return ok(service.list_tasks())


@app.get("/api/model-runs")
def get_model_runs() -> dict[str, Any]:
    return ok(service.list_model_runs())


@app.get("/api/project-events")
def get_project_events(project_id: str | None = None) -> dict[str, Any]:
    return ok(service.list_project_events(project_id))


@app.get("/api/json-configs")
def get_json_configs() -> dict[str, Any]:
    return ok(service.json_configs())


@app.post("/api/instrumentals")
def create_instrumental(payload: dict[str, Any]) -> dict[str, Any]:
    return run_action(lambda: service.create_instrumental(payload))


@app.post("/api/melodies")
def create_melody(payload: dict[str, Any]) -> dict[str, Any]:
    return run_action(lambda: service.create_melody(payload))


@app.post("/api/lyrics")
def create_lyrics(payload: dict[str, Any]) -> dict[str, Any]:
    return run_action(lambda: service.create_lyrics(payload))


@app.get("/api/lyrics/{asset_id}")
def get_lyrics(asset_id: str) -> dict[str, Any]:
    return run_action(lambda: service.get_lyrics(asset_id))


@app.put("/api/lyrics/{asset_id}")
def update_lyrics(asset_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    return run_action(lambda: service.update_lyrics(asset_id, payload))


@app.post("/api/favorites")
def favorite_asset(payload: dict[str, Any]) -> dict[str, Any]:
    return run_action(lambda: service.favorite_asset(payload))


@app.post("/api/sets")
def create_set(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    return run_action(lambda: service.create_set(payload or {}))


@app.post("/api/presets/lullaby/mp3")
def create_default_lullaby_mp3() -> dict[str, Any]:
    return run_action(service.create_default_lullaby_mp3)


@app.post("/api/sets/export")
def export_sets_to_json() -> dict[str, Any]:
    return run_action(service.export_sets_to_json)


@app.post("/api/assistant/gemma")
def run_gemma_assistant(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    return run_action(lambda: service.gemma_assistant(payload or {}))


@app.post("/api/assistant/qwen")
def run_qwen_technical_assistant(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    return run_action(lambda: service.qwen_technical_assistant(payload or {}))


@app.post("/api/orchestration/handoff")
def run_model_handoff(payload: dict[str, Any]) -> dict[str, Any]:
    return run_action(lambda: service.run_model_handoff(payload))


@app.post("/api/samples")
def create_sample() -> dict[str, Any]:
    return run_action(service.create_sample)


@app.post("/api/songs")
def create_song() -> dict[str, Any]:
    return run_action(service.create_song)


@app.post("/api/mix")
def prepare_mix() -> dict[str, Any]:
    return run_action(service.prepare_mix)


@app.post("/api/exports")
def prepare_exports() -> dict[str, Any]:
    return run_action(service.prepare_exports)


@app.post("/api/audio-exports")
def generate_audio_exports() -> dict[str, Any]:
    return run_action(service.generate_audio_exports)


@app.post("/api/local-final-song")
def generate_local_final_song() -> dict[str, Any]:
    return run_action(service.generate_local_final_song)


@app.get("/api/audio-exports/latest/download")
def download_latest_audio_export(format: str = "mp3") -> FileResponse:
    try:
        path, filename = service.latest_audio_export_file(format)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    media_type = "audio/mpeg" if format.lower().strip().lstrip(".") == "mp3" else "audio/wav"
    return FileResponse(path, media_type=media_type, filename=filename)


@app.post("/api/templates")
def save_template() -> dict[str, Any]:
    return run_action(service.save_template)


if FRONTEND_DIR.exists():
    assets_dir = FRONTEND_DIR / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")


@app.get("/{path:path}")
def serve_frontend(path: str) -> FileResponse:
    requested_path = (FRONTEND_DIR / path).resolve()
    frontend_root = FRONTEND_DIR.resolve()
    if requested_path.is_file() and str(requested_path).startswith(str(frontend_root)):
        return FileResponse(requested_path)
    return FileResponse(FRONTEND_DIR / "index.html")
