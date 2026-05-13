from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from application.song_service import SongService
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

app = FastAPI(title="Song AI Generator API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


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


@app.post("/api/favorites")
def favorite_asset(payload: dict[str, Any]) -> dict[str, Any]:
    return run_action(lambda: service.favorite_asset(payload))


@app.post("/api/sets")
def create_set(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    return run_action(lambda: service.create_set(payload or {}))


@app.post("/api/sets/export")
def export_sets_to_json() -> dict[str, Any]:
    return run_action(service.export_sets_to_json)


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
