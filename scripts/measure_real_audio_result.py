"""Measure an isolated completed job without loading models or approving audio."""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'backend'))
from adapters.pcm_edit_comparison import compare_pcm_edit
from adapters.pcm_signal_metrics import measure_pcm_signal


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('result', type=Path)
    parser.add_argument('--source', type=Path)
    parser.add_argument('--start', type=float, default=5)
    parser.add_argument('--end', type=float, default=10)
    args = parser.parse_args()
    result = json.loads(args.result.read_text(encoding='utf-8'))
    if result.get('status') != 'completed':
        raise ValueError('Only completed jobs can be measured.')
    artifact = result['result']['artifact']
    audio = Path(artifact['file_path'])
    signal = measure_pcm_signal(audio, audio.parent)
    if signal.get('audio_sha256') != artifact['metadata']['checksum']:
        raise ValueError('Audio checksum differs from the persisted artifact.')
    report = {'task_id': result['task_id'], 'plan_id': result['plan_id'],
              'task_type': result['task_type'], 'signal': signal,
              'quality_verified': False, 'acceptance_recorded': False}
    if args.source:
        report['comparison'] = compare_pcm_edit(args.source, audio, args.start, args.end)
    target = args.result.parent / 'signal_postflight.json'
    target.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'report': str(target), **report}, ensure_ascii=False))


if __name__ == '__main__':
    main()
