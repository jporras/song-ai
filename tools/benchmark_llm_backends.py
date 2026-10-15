"""Isolated exploratory llama-bench runner; never changes application settings."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
import re
from pathlib import Path
import subprocess
import time


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--backend', action='append', required=True, metavar='NAME=EXECUTABLE')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--timeout', type=int, default=90)
    parser.add_argument('--runtime', type=Path, help='Isolated runtime.json containing DLL directories')
    parser.add_argument('--device', choices=('CPU', 'GPU', 'NPU'))
    parser.add_argument('--role', action='append', choices=('qwen', 'gemma'))
    parser.add_argument('--flash-attention', choices=('on', 'off'), default='off')
    parser.add_argument('--prompt-tokens', type=int, default=512)
    parser.add_argument('--generate-tokens', type=int, default=32)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    args.output.mkdir(parents=True, exist_ok=True)
    environment = dict(os.environ)
    if args.runtime:
        runtime = json.loads(args.runtime.read_text(encoding='utf-8'))
        environment['PATH'] = os.pathsep.join(runtime['runtime_path']) + os.pathsep + environment.get('PATH', '')
        environment.update(runtime.get('runtime_environment', {}))
    if args.device:
        environment['GGML_OPENVINO_DEVICE'] = args.device
        environment['GGML_OPENVINO_STATEFUL_EXECUTION'] = '0' if args.device == 'NPU' else '1'
    report = {'scope': 'exploratory_not_application_quality',
              'recorded_at': datetime.now(timezone.utc).isoformat(),
              'protocol': {'prompt_tokens': args.prompt_tokens, 'generated_tokens': args.generate_tokens, 'repetitions': 2,
                           'batch': 512, 'ubatch': 256, 'threads': 6, 'flash_attention': args.flash_attention == 'on',
                           'requested_device': args.device,
                           'timeout_per_model_seconds': args.timeout}, 'results': []}
    for backend in args.backend:
        name, separator, executable_text = backend.partition('=')
        if not separator or not name.replace('-', '').isalnum():
            parser.error('Backend must be NAME=EXECUTABLE with a simple name')
        executable = Path(executable_text).resolve()
        for role in args.role or ('qwen', 'gemma'):
            entry = {'backend_candidate': name, 'role': role, 'executable': str(executable)}
            report['results'].append(entry)
            if not executable.is_file():
                entry.update(status='setup_missing', reason='No executable; performance not evaluated')
            else:
                started = None
                try:
                    help_result = subprocess.run([str(executable), '--help'], capture_output=True,
                                                 timeout=15, env=environment, creationflags=subprocess.CREATE_NO_WINDOW)
                    help_text = (help_result.stdout + help_result.stderr).decode('utf-8', errors='replace')
                    flash_value = args.flash_attention if '<on|off|auto>' in help_text else ('1' if args.flash_attention == 'on' else '0')
                    command = [str(executable), '-m', str(root/f'data/models/llm/{role}/{role}.gguf'),
                               '-p', str(args.prompt_tokens), '-n', str(args.generate_tokens), '-r', '2', '-b', '512', '-ub', '256',
                               '-t', '6', '-ngl', '999', '-fa', flash_value, '-o', 'json']
                    entry['command'] = command
                    started = time.monotonic()
                    stdout_path = args.output/f'{name}-{role}.stdout.json'
                    stderr_path = args.output/f'{name}-{role}.stderr.log'
                    with stdout_path.open('wb') as output_log, stderr_path.open('wb') as error_log:
                        completed = subprocess.run(command, cwd=executable.parent, stdout=output_log, stderr=error_log,
                                                   timeout=args.timeout, env=environment, creationflags=subprocess.CREATE_NO_WINDOW)
                    entry['wall_seconds'] = time.monotonic()-started
                    stdout = stdout_path.read_text(encoding='utf-8', errors='replace')
                    stderr = stderr_path.read_text(encoding='utf-8', errors='replace')
                    device_match = re.search(r'OpenVINO: using device (\S+)', stderr)
                    if device_match:
                        entry['observed_device'] = device_match.group(1)
                    entry['exit_code'] = completed.returncode
                    if completed.returncode:
                        entry.update(status='runtime_failed', reason=stderr[-1800:])
                    else:
                        rows = json.loads(stdout)
                        entry.update(status='completed', measurements=rows)
                        observed = {str(row.get('backend', row.get('backends', 'unknown'))) for row in rows}
                        entry['observed_backends'] = sorted(observed)
                        # Report observations; successful CPU fallback must not be called a GPU win.
                        if all(value.lower() in {'cpu', 'unknown'} for value in observed):
                            entry.update(status='backend_unverified', reason='GPU execution not identified in result')
                        if 'fallback to CPU' in stderr:
                            entry.update(status='backend_unverified', reason='Requested OpenVINO device unavailable; CPU fallback detected')
                        if any('OPENVINO' in value.upper() for value in observed) and args.device:
                            if not device_match or device_match.group(1).split('.')[0] != args.device:
                                entry.update(status='backend_unverified', reason='Requested OpenVINO device not confirmed by runtime log')
                except subprocess.TimeoutExpired as error:
                    entry.update(status='timeout', reason='Owned subprocess stopped at exploratory deadline')
                    if started is not None:
                        entry['wall_seconds'] = time.monotonic()-started
                    if error.stderr:
                        (args.output/f'{name}-{role}.stderr.log').write_bytes(error.stderr)
                except (OSError, ValueError) as error:
                    entry.update(status='harness_error', reason=str(error))
            (args.output/'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
            print(json.dumps({key: value for key, value in entry.items() if key not in {'reason', 'measurements', 'command'}}, ensure_ascii=False), flush=True)


if __name__ == '__main__':
    main()
