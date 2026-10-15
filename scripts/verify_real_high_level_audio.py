"""Run high-level ACE-Step through real Song-AI plans/jobs on an isolated QA copy."""
import json
import argparse
import shutil
import sys
import time
from copy import deepcopy
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'backend'))
from core.storage import StorageManager
from config.settings import Settings
from config.resource_settings import ResourceMonitorSettings
from application.song_service import SongService


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--task', choices=('text2music','cover','repaint','lego','extract','complete'), default='text2music')
    parser.add_argument('--api', choices=('direct','high_level'), default='high_level')
    parser.add_argument('--source', type=Path)
    parser.add_argument('--instruction', default='')
    parser.add_argument('--tracks', default='')
    parser.add_argument('--prepare-only', action='store_true')
    args = parser.parse_args()
    if args.task != 'text2music' and not args.source:
        parser.error('Las tareas de edición requieren --source verificada.')
    directory = ROOT/'data'/('qa_high_level_' + str(time.time_ns()))
    shutil.copytree(ROOT/'data/qa_builder_batch_20261009', directory)
    store = StorageManager(directory)
    settings = replace(Settings.load(), data_dir=directory,
        resource_monitor=replace(ResourceMonitorSettings.load(ROOT), audio_start_delay_seconds=0))
    service = SongService(store, settings)
    song_id = 'song_d0d582e3925a'
    project = store.get_song_project(song_id)
    original_spec = project['spec']['json_spec']
    spec = deepcopy(original_spec)
    # Explicit QA scenario; the original project and its revision are untouched.
    base = args.task in ('lego','extract','complete')
    spec.update(task_type=args.task, generation_api=args.api,
                ace_step_config='acestep-v15-base' if base else 'acestep-v15-turbo', duration_seconds=15,
                inference_steps=32 if base else 8, seed=42)
    for key in ('src_audio','source_artifact_id','reference_audio','reference_artifact_id'):
        spec.pop(key,None)
    if args.source:
        artifact = service.import_source_audio(song_id, args.source.name, args.source.read_bytes(), True)['artifact']
        spec.update(source_artifact_id=artifact['artifact_id'],src_audio=artifact['file_path'])
    if args.task in ('repaint','lego'):
        spec.update(repainting_start=5,repainting_end=10,chunk_mask_mode='explicit')
    if base:
        spec.update(instruction=args.instruction,target_tracks=args.tracks.split(',') if args.tracks else [])
    provenance = spec.setdefault('_provenance', {})
    for field, value in spec.items():
        if not field.startswith('_') and (field not in original_spec or value != original_spec[field]):
            provenance[field] = {'source': 'explicit_technical_qa_scenario',
                'confirmation': 'technical_qa_only',
                'note': 'Isolated verification value; not an original USER creative decision.'}
    record = store.upsert_song_spec(song_id, spec, False, [],
        deterministic_valid=project['spec']['revision']['deterministic_valid'],
        user_confirmation_status='confirmed', technical_review_mode='explicit_qa_high_level_scenario')
    lyrics = spec['_lyrics_document']['markdown']
    review = service._ace_plan_review()
    item = review.prepare(song_id, lyrics)
    review.approve(song_id, item['plan_id'], {'plan_sha256':item['plan']['plan_sha256'], 'lyrics_confirmed':True})
    if args.prepare_only:
        summary={'qa_directory':str(directory),'song_id':song_id,'plan_id':item['plan_id'],
                 'task_type':args.task,'plan_sha256':item['plan']['plan_sha256'],'status':'prepared_not_executed'}
        (directory/'prepared.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
        print(json.dumps(summary),flush=True)
        return 0
    task = service.ace_candidate_jobs.start(song_id, {'plan_sha256':item['plan']['plan_sha256'],
        'exploratory_audio_authorized':True,'request_id':'qa-high-level-1'})
    summary={'qa_directory':str(directory),'song_id':song_id,'task_id':task['task_id'],
        'plan_id':item['plan_id'],'revision_id':record['revision']['revision_id'], 'generation_api':args.api,'task_type':args.task}
    (ROOT/'data/runtime/high_level_active_20261009.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    print(json.dumps(summary),flush=True)
    while task['status'] in {'pending','running','cancelling'}:
        time.sleep(2)
        task=service.ace_candidate_jobs.get(song_id,task['task_id'])
    summary.update(status=task['status'], result=task.get('result'))
    (directory/'result.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'status':task['status'],'qa_directory':str(directory)}),flush=True)
    return 0 if task['status']=='completed' else 1


if __name__ == '__main__':
    raise SystemExit(main())
