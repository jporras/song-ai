"""Run a bounded NPU diagnostic without changing Song AI's active runtime."""
import json
import argparse
import os
from pathlib import Path
import subprocess
import time

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'data/diagnostics/openvino-20261007/npu-diagnostic'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runtime', type=Path, default=ROOT/'data/tools/llm-exploration/openvino-b9442/runtime.json')
    parser.add_argument('--output', type=Path, default=OUT)
    parser.add_argument('--timeout', type=int, default=180)
    args = parser.parse_args()
    output = args.output
    runtime = json.loads(args.runtime.read_text())
    environment = dict(os.environ)
    environment['PATH'] = os.pathsep.join(runtime['runtime_path'])+os.pathsep+environment.get('PATH', '')
    environment.update(runtime.get('runtime_environment', {}))
    environment.update(GGML_OPENVINO_DEVICE='NPU', GGML_OPENVINO_STATEFUL_EXECUTION='0')
    output.mkdir(parents=True, exist_ok=True)
    command = [runtime['cli'], '-m', str(ROOT/'data/models/llm/qwen/qwen.gguf'),
               '-c', '512', '-np', '1', '-b', '128', '-ub', '128', '-ngl', '999', '-t', '6', '--fit', 'off',
               '-fa', 'on', '--no-warmup', '--single-turn', '-n', '8',
               '-p', 'Write one musical instrument:', '-lv', '4']
    result = {'scope': 'small_context_diagnostic_not_application_acceptance', 'command': command,
              'runtime': str(args.runtime.resolve()),
              'runtime_environment': {key: value for key, value in environment.items() if key.startswith('GGML_OPENVINO_')}}
    started = time.monotonic()
    with (output/'stdout.log').open('wb') as stdout, (output/'stderr.log').open('wb') as stderr:
        try:
            completed = subprocess.run(command, env=environment, stdout=stdout, stderr=stderr,
                                       timeout=args.timeout, creationflags=subprocess.CREATE_NO_WINDOW)
            result.update(status='completed' if completed.returncode == 0 else 'runtime_failed',
                          exit_code=completed.returncode)
        except subprocess.TimeoutExpired:
            result['status'] = 'timeout'
    result['seconds'] = time.monotonic()-started
    (output/'report.json').write_text(json.dumps(result, indent=2))
    print(json.dumps(result), flush=True)


if __name__ == '__main__':
    main()
