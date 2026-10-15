"""Observe local checkpoint prerequisites without importing engines or reading weights."""
import hashlib
import json
from pathlib import Path


COMPONENTS = {
    'acestep-v15-base': ('config.json', 'model.safetensors'),
    'acestep-v15-turbo': ('config.json', 'model.safetensors'),
    'vae': ('config.json', 'diffusion_pytorch_model.safetensors'),
    'Qwen3-Embedding-0.6B': ('config.json', 'model.safetensors'),
    'acestep-5Hz-lm-0.6B': ('config.json', 'model.safetensors', 'tokenizer.json'),
    'acestep-5Hz-lm-1.7B': ('config.json', 'model.safetensors', 'tokenizer.json'),
}


def observe_checkpoint_root(root: Path) -> dict:
    components = {}
    for name, required in COMPONENTS.items():
        directory = root / name
        files = {}
        for filename in required:
            path = directory / filename
            try:
                size = path.stat().st_size if path.is_file() else 0
                files[filename] = {'present_nonempty': size > 0, 'size_bytes': size}
            except OSError:
                files[filename] = {'present_nonempty': False, 'size_bytes': 0}
        config = directory / 'config.json'
        config_info = {'status': 'missing_or_empty'}
        if files['config.json']['present_nonempty']:
            try:
                if files['config.json']['size_bytes'] > 1024 * 1024:
                    raise ValueError('Config exceeds inspection budget')
                raw = config.read_bytes()
                parsed = json.loads(raw.decode('utf-8-sig'))
                if not isinstance(parsed, dict):
                    raise ValueError('Config must be an object')
                architectures = parsed.get('architectures', [])
                if not isinstance(architectures, list) or not all(isinstance(x, str) for x in architectures):
                    raise ValueError('Invalid architecture list')
                config_info = {'status': 'parsed', 'sha256': hashlib.sha256(raw).hexdigest(),
                               'architectures': architectures}
            except (OSError, ValueError):
                config_info = {'status': 'invalid_or_unreadable'}
        complete = all(item['present_nonempty'] for item in files.values()) and config_info['status'] == 'parsed'
        if name.startswith('acestep-v15-'):
            complete = complete and 'AceStepConditionGenerationModel' in config_info.get('architectures', [])
        components[name] = {'files': files, 'config': config_info, 'prerequisites_present': complete}
    routes = {}
    for family in ('base', 'turbo'):
        common = all(components[name]['prerequisites_present'] for name in
                     (f'acestep-v15-{family}', 'vae', 'Qwen3-Embedding-0.6B'))
        routes[family] = {'direct': common, 'high_level': common,
                         'high_level_lm': {lm: common and components[lm]['prerequisites_present']
                                           for lm in COMPONENTS if lm.startswith('acestep-5Hz-lm-')}}
    return {'checkpoint_root': str(root), 'components': components, 'route_prerequisites': routes,
            'loaded_verified': False, 'generation_verified': False, 'weights_checksum_verified': False,
            'scope': 'local_file_metadata_and_bounded_config_only'}
