"""Prepare a pinned, isolated Windows OpenVINO llama.cpp build."""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT/'data/tools/llm-exploration/openvino-b9442'


def download_extract(name: str, url: str, official_checksum: bool = False) -> Path:
    archive = BASE/(name+'.zip')
    if not archive.exists():
        print('Downloading '+name, flush=True)
        urllib.request.urlretrieve(url, archive)
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    if official_checksum:
        record = BASE/(name+'-source.json')
        previous = json.loads(record.read_text(encoding='utf-8')) if record.exists() else {}
        if previous.get('official_checksum_verified') and previous.get('url') == url:
            expected = previous['sha256']
        else:
            expected = urllib.request.urlopen(url+'.sha256', timeout=30).read().decode().split()[0].lower()
        if digest != expected:
            raise ValueError('Official checksum mismatch: '+name)
    target = (BASE/name).resolve()
    if not target.exists():
        with zipfile.ZipFile(archive) as package:
            for member in package.infolist():
                if not (target/member.filename).resolve().is_relative_to(target):
                    raise ValueError('Unsafe archive path')
            package.extractall(target)
    (BASE/(name+'-source.json')).write_text(json.dumps({'url':url,'sha256':digest,
        'bytes':archive.stat().st_size,'official_checksum_verified':official_checksum}, indent=2), encoding='utf-8')
    return target


def main() -> None:
    BASE.mkdir(parents=True, exist_ok=True)
    sdk = download_extract('sdk-2026.0', 'https://storage.openvinotoolkit.org/repositories/openvino/packages/2026.0/windows/openvino_toolkit_windows_2026.0.0.20965.c6d6a13a886_x86_64.zip', True)
    cl = download_extract('opencl-2026.05.29', 'https://github.com/KhronosGroup/OpenCL-SDK/releases/download/v2026.05.29/OpenCL-SDK-v2026.05.29-Win-x64.zip')
    source = download_extract('source-b9442', 'https://codeload.github.com/ggml-org/llama.cpp/zip/refs/tags/b9442')
    source = next(p.parent for p in source.glob('*/CMakeLists.txt'))
    ov_config = next(sdk.rglob('OpenVINOConfig.cmake')).parent
    cl_include = next(cl.rglob('CL/cl.h')).parent.parent
    cl_library = next(cl.rglob('OpenCL.lib'))
    vcvars = Path('C:/Program Files (x86)/Microsoft Visual Studio/18/BuildTools/VC/Auxiliary/Build/vcvars64.bat')
    # Capture compiler variables in memory. Never print or persist the full environment.
    environment_script = BASE/'compiler-env.cmd'
    environment_script.write_text('@echo off\ncall "'+str(vcvars)+'" >nul\nif errorlevel 1 exit /b 1\nset\n', encoding='utf-8')
    captured = subprocess.run(['cmd.exe','/d','/c',str(environment_script)], capture_output=True, check=True,
                              creationflags=subprocess.CREATE_NO_WINDOW)
    environment = dict(os.environ)
    for line in captured.stdout.decode(errors='replace').splitlines():
        if '=' in line and not line.startswith('='):
            key,value = line.split('=',1)
            environment[key.upper()] = value
    cmake = shutil.which('cmake', path=environment.get('PATH'))
    build = BASE/'build'
    configure = [cmake,'-S',str(source),'-B',str(build),'-G','Ninja','-DCMAKE_BUILD_TYPE=Release',
                 '-DGGML_OPENVINO=ON','-DGGML_VULKAN=OFF','-DGGML_NATIVE=ON','-DLLAMA_CURL=OFF',
                 '-DLLAMA_BUILD_NUMBER=9442','-DLLAMA_BUILD_COMMIT=d4c8e2c29',
                 '-DLLAMA_BUILD_TESTS=OFF','-DOpenVINO_DIR='+str(ov_config),
                 '-DOpenCL_INCLUDE_DIR='+str(cl_include),'-DOpenCL_LIBRARY='+str(cl_library)]
    for name,command in [('configure',configure),('build',[cmake,'--build',str(build),'--target','llama-bench','llama-server','llama-cli','--parallel','4'])]:
        print('Starting '+name,flush=True)
        with (BASE/(name+'.log')).open('w',encoding='utf-8') as log:
            result = subprocess.run(command,env=environment,stdout=log,stderr=subprocess.STDOUT,
                                    creationflags=subprocess.CREATE_NO_WINDOW)
        if result.returncode:
            raise RuntimeError(name+' failed; see '+str(BASE/(name+'.log')))
    runtime_dirs = sorted({str(p.parent) for p in sdk.rglob('*.dll')} | {str(p.parent) for p in cl.rglob('*.dll')})
    config = {'build':'b9442','openvino':'2026.0.0','sdk':str(sdk),'source':str(source),
              'runtime_path':runtime_dirs,'bench':str(build/'bin/llama-bench.exe'),
              'server':str(build/'bin/llama-server.exe'),
              'cli':str(build/'bin/llama-cli.exe'),
              'runtime_environment':{'GGML_OPENVINO_DEVICE':'GPU','GGML_OPENVINO_STATEFUL_EXECUTION':'1'}}
    (BASE/'runtime.json').write_text(json.dumps(config,indent=2),encoding='utf-8')
    print('OPENVINO_BUILD_READY',flush=True)


if __name__ == '__main__':
    main()
