"""Verify an existing QA final export over ASGI without starting models."""
import argparse
import hashlib
import json
import os
import sys
import zipfile
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'backend'))


def checksum(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('qa_root', type=Path)
    parser.add_argument('song_id')
    args = parser.parse_args()
    qa_root = args.qa_root.resolve()
    if qa_root.parent != (ROOT / 'data').resolve() or not qa_root.name.startswith('qa_'):
        raise ValueError('Se requiere una copia QA dentro de data/.')
    project = qa_root / 'projects' / args.song_id
    manifest = json.loads((project / 'export_manifest.json').read_text(encoding='utf-8'))
    if manifest.get('status') != 'export_ready' or manifest.get('song_id') != args.song_id:
        raise ValueError('Manifest no corresponde al proyecto QA.')
    artifacts = {entry['type']: entry for entry in manifest['artifacts']}
    required = {'song_spec', 'ace_plan_json', 'lyrics_markdown', 'final_song_wav',
                'final_song_mp3', 'final_song_flac', 'project_zip'}
    if not required.issubset(artifacts):
        raise ValueError('Faltan artefactos en el manifest.')
    zip_path = Path(artifacts['project_zip']['file_path']).resolve()
    if project.resolve() not in zip_path.parents:
        raise ValueError('ZIP fuera del proyecto QA.')
    with zipfile.ZipFile(zip_path) as archive:
        if archive.testzip() is not None:
            raise ValueError('ZIP corrupto.')
        names = set(archive.namelist())
        for kind in required - {'project_zip'}:
            path = Path(artifacts[kind]['file_path']).resolve()
            if project.resolve() not in path.parents or str(path.relative_to(project.resolve())).replace('\\', '/') not in names:
                raise ValueError(f'{kind} falta dentro del ZIP.')

    os.environ.update(SONG_AI_LLM_AUTOSTART='false', SONG_AI_STOP_LLM_ON_EXIT='false',
                      SONG_AI_BOOTSTRAP_ON_START='false', SONG_AI_RESOURCE_MONITOR_ENABLED='false')
    from config.settings import Settings
    settings = Settings.load()
    configured = replace(settings, data_dir=qa_root,
        local_models=replace(settings.local_models, llama_cpp_enabled=False),
        resource_monitor=replace(settings.resource_monitor, enabled=False,
                                 stop_llm_command='', start_llm_command=''))
    Settings.load = classmethod(lambda cls: configured)
    from adapters.http.fastapi_app import app
    from fastapi.testclient import TestClient
    from core.storage import StorageManager
    store = StorageManager(qa_root)
    checked = []
    client = TestClient(app)
    try:
        for kind in ('final_song_mp3', 'final_song_flac', 'project_zip'):
            response = client.get(f'/api/pro/projects/{args.song_id}/artifacts/{kind}/download')
            if response.status_code != 200:
                raise ValueError(f'{kind}: HTTP {response.status_code}: {response.text[:180]}')
            recorded = store.verify_song_artifact(args.song_id, kind)
            digest = checksum(response.content)
            if recorded['artifact_status'] != 'GENERATED' or digest != recorded['metadata']['checksum']:
                raise ValueError(f'{kind}: descarga distinta del checksum SQLite.')
            if 'attachment;' not in response.headers.get('content-disposition', ''):
                raise ValueError(f'{kind}: falta cabecera de descarga.')
            checked.append({'type': kind, 'bytes': len(response.content), 'sha256': digest,
                            'content_type': response.headers.get('content-type', '')})
    finally:
        client.close()
    report = {'status': 'verified', 'scope': 'QA_real_audio_manifest_zip_and_ASGI_download',
              'song_id': args.song_id, 'zip_members': sorted(names), 'downloads': checked,
              'audio_acceptance_recorded': False}
    (qa_root / 'final_export_postflight_20261015.json').write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
