"""Cancel the real loaded Turbo worker through the application's process service.

Uses a copy of accepted Isabella inputs; never publishes or edits its project.
"""
import json
import sys
import time
import urllib.request
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'backend'))
import psutil
from core.storage import StorageManager
from audio.ace_step_profiles import resolve_ace_step_profile
from config.resource_settings import ResourceMonitorSettings
from application.local_audio_process_service import LocalAudioProcessService
from application.audio_cancellation import AudioCancelled


def main():
    directory = ROOT / 'data/qa_real_cancel_20261009'
    directory.mkdir(parents=True, exist_ok=True)
    store = StorageManager(directory)
    project = store.create_song_project('QA cancelación con pesos', 'qa-cancellation')
    project['spec'] = {'duration_seconds': 120}
    source = ROOT / 'data/projects/song_2ea83a928856/candidates/ace_candidate_1e794dcb99dc4591b673eec8f423db74'
    prompt, lyrics = directory / 'caption.txt', directory / 'lyrics.md'
    prompt.write_bytes((source / 'ace_plan_caption.txt').read_bytes())
    lyrics.write_bytes((source / 'ace_plan_lyrics.md').read_bytes())
    diagnostics, output = directory / 'diagnostics.json', directory / 'not_a_candidate.wav'
    # One directory per attempt prevents an old loaded marker cancelling a new worker.
    attempt = directory / str(time.time_ns())
    attempt.mkdir()
    diagnostics, output = attempt / 'diagnostics.json', attempt / 'not_a_candidate.wav'
    settings = replace(ResourceMonitorSettings.load(ROOT), audio_start_delay_seconds=0)
    service = LocalAudioProcessService(store, timeout_seconds=900, resource_settings=settings)
    profile = resolve_ace_step_profile('turbo')
    loaded = {}
    def cancel_after_load():
        if diagnostics.exists():
            try:
                observed = json.loads(diagnostics.read_text(encoding='utf-8'))
            except (ValueError, OSError):
                return
            if observed.get('status') == 'pipeline_loaded':
                loaded.update(observed)
                raise AudioCancelled('QA: cancelación después de cargar pesos reales')
    argv = [sys.executable, str(ROOT/'tools/acestep_generate.py'), '--prompt', str(prompt),
            '--lyrics', str(lyrics), '--output', str(output), '--diagnostics', str(diagnostics),
            '--checkpoint-path', profile.checkpoint_root, '--config-path', profile.config_path,
            '--device', 'xpu', '--require-device', 'true', '--duration', '120', '--infer-step', '8',
            '--bpm', '72', '--vocal-language', 'es', '--torch-threads', '4',
            '--output-type', 'exploratory_candidate']
    result = {'scope':'real_weights_cancellation_not_audio_quality', 'before_ram_mb':round(psutil.virtual_memory().available/1024**2), 'attempt':str(attempt)}
    try:
        service._run_command(project, attempt, prompt, lyrics, output, attempt/'generation.log',
                             diagnostics, profile, process_arguments=argv,
                             cancellation_check=cancel_after_load)
        result['status'] = 'unexpected_completion'
    except AudioCancelled:
        result['status'] = 'cancelled_after_real_load'
    except Exception as error:
        result.update(status='failed', error=str(error))
    result['loaded_status'] = loaded.get('status')
    result['after_ram_mb'] = round(psutil.virtual_memory().available/1024**2)
    result['output_exists'] = output.exists()
    events = store.get_song_project(project['id']).get('events', [])
    worker_pids = [event.get('payload', {}).get('pid') for event in events
                   if event.get('payload', {}).get('pid')]
    result['worker_pids'] = worker_pids
    result['workers_terminated'] = bool(worker_pids) and all(not psutil.pid_exists(pid) for pid in worker_pids)
    result['text_servers'] = {}
    for role, port in [('gemma',8081),('qwen',8082)]:
        deadline = time.monotonic() + 90
        result['text_servers'][role] = 'not_ready_within_deadline'
        while time.monotonic() < deadline:
            try:
                with urllib.request.urlopen(f'http://127.0.0.1:{port}/health',timeout=5) as response:
                    if response.status == 200:
                        result['text_servers'][role] = 200
                        break
            except Exception:
                pass
            time.sleep(1)
    (attempt/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False),flush=True)
    return 0 if result['status']=='cancelled_after_real_load' else 1


if __name__ == '__main__':
    raise SystemExit(main())
