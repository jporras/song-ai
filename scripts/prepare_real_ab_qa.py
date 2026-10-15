"""Import completed real QA evidence for playback comparison, without inference."""
import json
import shutil
import sys
from copy import deepcopy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'backend'))
from core.storage import StorageManager
from adapters.sample_audio_evidence import inspect_sample_wav

target = ROOT/'data/qa_high_level_1791604384966484400'
source = ROOT/'data/qa_high_level_1791603499514019000'
result = json.loads((source/'result.json').read_text(encoding='utf-8'))
if result['status'] != 'completed':
    raise ValueError('Only completed real QA evidence can be imported.')
store = StorageManager(target)
task_id = 'qa_import_real_lego_1791603499514019000'
if not any(t['task_id'] == task_id for t in store.list_tasks()):
    original = next(t for t in StorageManager(source).list_tasks() if t['task_id'] == result['task_id'])
    copied = deepcopy(result['result'])
    artifact = copied['artifact']
    destination = target/'projects'/result['song_id']/'candidates'/artifact['artifact_id']
    shutil.copytree(Path(artifact['file_path']).parent, destination)
    audio = destination/'candidate.wav'
    evidence = inspect_sample_wav(audio,destination)
    if evidence['sha256'] != artifact['metadata']['checksum']:
        raise ValueError('Imported audio checksum differs from the real artifact.')
    artifact['file_path'] = str(audio)
    artifact['metadata']['audio_evidence'] = evidence
    origin = {'qa_directory':str(source), 'task_id':result['task_id'],
              'plan_id':result['plan_id'], 'import_only':True, 'new_generation':False}
    artifact['metadata']['qa_import_origin'] = origin
    payload = deepcopy(original['payload'])
    payload['qa_import_origin'] = origin
    store.create_task(task_id, original['task_type'], 'music', payload, 'Imported real QA evidence for A/B playback.')
    store.update_task(task_id,'completed',100,'Imported real QA artifact; no new inference or acceptance.',copied)
print(json.dumps({'task_id':task_id,'qa_directory':str(target),'source_directory':str(source)}))
