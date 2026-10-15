"""Continue one audio case only after the preceding isolated job finishes."""
import json
import argparse
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument('--previous', type=Path, default=ROOT/'data/qa_high_level_1791602787119137000/result.json')
parser.add_argument('--remaining-base', action='store_true')
parser.add_argument('--wait-seconds', type=int, default=1200)
args = parser.parse_args()
previous = args.previous
deadline = time.monotonic() + args.wait_seconds
while not previous.exists() and time.monotonic() < deadline:
    time.sleep(2)
if not previous.exists():
    raise SystemExit('Preceding job did not finish within the waiting budget; no next job started.')
result = json.loads(previous.read_text(encoding='utf-8'))
if result.get('status') != 'completed':
    raise SystemExit('Preceding job failed; review its result before continuing.')
source = ROOT/'data/runtime/isabella_qa_15s.wav'
if args.remaining_base:
    cases = [('extract', 'Extract the vocals track from the audio:', 'vocals'),
             ('complete', 'Complete the input track with drums:', 'drums')]
else:
    cases = [('repaint', '', '')]
for task, instruction, tracks in cases:
    subprocess.run([sys.executable, str(ROOT/'scripts/measure_real_audio_result.py'),
        str(previous), '--source', str(source)], cwd=ROOT, check=True)
    signal = json.loads((previous.parent/'signal_postflight.json').read_text(encoding='utf-8'))
    if signal['signal'].get('digital_silence') is not False:
        raise SystemExit('Previous audio signal requires review; no next job started.')
    command = [sys.executable, str(ROOT/'scripts/verify_real_high_level_audio.py'),
               '--task', task, '--api', 'direct', '--source', str(source)]
    if instruction:
        command.extend(['--instruction', instruction, '--tracks', tracks])
    print(f'Preceding job completed and measured; starting isolated {task}.', flush=True)
    completed = subprocess.run(command, cwd=ROOT, check=False)
    if completed.returncode:
        raise SystemExit(completed.returncode)
    active = json.loads((ROOT/'data/runtime/high_level_active_20261009.json').read_text(encoding='utf-8'))
    if active.get('task_type') != task:
        raise SystemExit('Active QA pointer differs from the completed case; review before continuing.')
    previous = Path(active['qa_directory'])/'result.json'
subprocess.run([sys.executable, str(ROOT/'scripts/measure_real_audio_result.py'),
    str(previous), '--source', str(source)], cwd=ROOT, check=True)
