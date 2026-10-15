"""Verify real candidate bytes through ASGI, with model startup disabled."""
import argparse
import hashlib
import json
import os
import sys
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'backend'))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('result', type=Path)
    args = parser.parse_args()
    result = json.loads(args.result.read_text(encoding='utf-8'))
    if result.get('status') != 'completed':
        raise ValueError('Candidate job must be completed.')
    os.environ.update(SONG_AI_LLM_AUTOSTART='false', SONG_AI_STOP_LLM_ON_EXIT='false',
                      SONG_AI_BOOTSTRAP_ON_START='false', SONG_AI_RESOURCE_MONITOR_ENABLED='false')
    from config.settings import Settings
    original = Settings.load()
    configured = replace(original, data_dir=Path(result['qa_directory']),
        local_models=replace(original.local_models, llama_cpp_enabled=False),
        resource_monitor=replace(original.resource_monitor, enabled=False, stop_llm_command='', start_llm_command=''))
    Settings.load = classmethod(lambda cls: configured)
    from adapters.http.fastapi_app import app
    from fastapi.testclient import TestClient
    checksum = result['result']['artifact']['metadata']['checksum']
    endpoint = f"/api/pro/projects/{result['song_id']}/ace-candidates/{result['task_id']}/audio"
    # No lifespan entered: no model bootstrap, server or external service needed.
    client = TestClient(app)
    try:
        response = client.get(endpoint, params={'audio_sha256':checksum, 'download':'true'})
        if response.status_code != 200 or hashlib.sha256(response.content).hexdigest() != checksum:
            raise ValueError('Download failed or response bytes differ from the persisted checksum.')
        disposition = response.headers.get('content-disposition', '')
        if 'attachment;' not in disposition or response.headers.get('content-type') != 'audio/wav':
            raise ValueError('Expected WAV attachment headers.')
        rejected = client.get(endpoint, params={'audio_sha256':'0'*64, 'download':'true'})
        if rejected.status_code != 400:
            raise ValueError('A stale checksum must be rejected.')
        report = {'status':'verified', 'scope':'real_ASGI_download_not_browser_or_listening',
                  'bytes':len(response.content), 'sha256':checksum,
                  'content_disposition':disposition, 'wrong_checksum_status':rejected.status_code,
                  'acceptance_recorded':False}
        (args.result.parent/'download_postflight.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
        print(json.dumps(report))
    finally:
        client.close()


if __name__ == '__main__':
    main()
