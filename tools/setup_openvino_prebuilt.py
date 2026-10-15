"""Install a pinned official Windows OpenVINO candidate in an isolated folder."""
import hashlib
import json
from pathlib import Path
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT/'data/tools/llm-exploration/openvino-b11476'
URL = 'https://github.com/ggml-org/llama.cpp/releases/download/b11476/llama-b11476-bin-win-openvino-2026.4.1-x64.zip'
EXPECTED = 'c62c59a6c2b871b85162c7d59307946cd28ee456f1d551bf86bdf68660b6f6c3'


def main():
    BASE.mkdir(parents=True, exist_ok=True)
    archive = BASE/'official.zip'
    if not archive.exists():
        urllib.request.urlretrieve(URL, archive)
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    if digest != EXPECTED:
        raise ValueError('Official GitHub release asset digest mismatch')
    target = (BASE/'runtime').resolve()
    if not target.exists():
        with zipfile.ZipFile(archive) as package:
            for member in package.infolist():
                if not (target/member.filename).resolve().is_relative_to(target):
                    raise ValueError('Unsafe archive path')
            package.extractall(target)
    runtime = {'build': 'b11476', 'openvino': '2026.4.1',
               'runtime_path': sorted({str(p.parent) for p in target.rglob('*.dll')}),
               'runtime_environment': {'GGML_OPENVINO_DEVICE': 'GPU', 'GGML_OPENVINO_STATEFUL_EXECUTION': '1'}}
    for key, name in [('bench', 'llama-bench.exe'), ('server', 'llama-server.exe'), ('cli', 'llama-cli.exe')]:
        found = list(target.rglob(name))
        if found:
            runtime[key] = str(found[0])
    if 'bench' not in runtime or 'server' not in runtime:
        raise ValueError('Official package lacks benchmark or server')
    (BASE/'runtime.json').write_text(json.dumps(runtime, indent=2))
    npu_runtime = dict(runtime)
    npu_runtime['runtime_environment'] = {
        'GGML_OPENVINO_DEVICE': 'NPU', 'GGML_OPENVINO_STATEFUL_EXECUTION': '0',
        'GGML_OPENVINO_MEMORY_OPTIMIZE': '1', 'GGML_OPENVINO_PREFILL_CHUNK_SIZE': '64',
        'GGML_OPENVINO_CACHE_DIR': str((BASE/'npu-cache').resolve())}
    (BASE/'runtime-npu-tuned.json').write_text(json.dumps(npu_runtime, indent=2))
    (BASE/'source.json').write_text(json.dumps({'url': URL, 'sha256': digest,
        'bytes': archive.stat().st_size, 'official_release_asset_digest_verified': True}, indent=2))
    print(json.dumps(runtime), flush=True)


if __name__ == '__main__':
    main()
