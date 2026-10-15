"""Inspect installed source contracts without importing engines or loading weights."""
import ast
import hashlib
import json
from pathlib import Path
import sys


def inspect_contract(root: Path) -> dict:
    package = root / '.venv/Lib/site-packages/acestep'
    paths = {
        'direct': package / 'core/generation/handler/generate_music.py',
        'high_level': package / 'inference.py',
        'tasks': package / 'constants.py',
        'wrapper': root / 'tools/acestep_generate.py',
        'adapter': root / 'tools/acestep_high_level.py',
    }
    trees, hashes = {}, {}
    for name, path in paths.items():
        raw = path.read_bytes()
        trees[name] = ast.parse(raw.decode('utf-8-sig'))
        hashes[name] = hashlib.sha256(raw).hexdigest()
    function = next(node for node in ast.walk(trees['direct'])
                    if isinstance(node, ast.FunctionDef) and node.name == 'generate_music')
    direct_fields = {arg.arg for arg in function.args.args + function.args.kwonlyargs}
    params = next(node for node in ast.walk(trees['high_level'])
                  if isinstance(node, ast.ClassDef) and node.name == 'GenerationParams')
    high_fields = {node.target.id for node in params.body
                   if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name)}
    calls = [(node, direct_fields) for node in ast.walk(trees['wrapper'])
             if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
             and isinstance(node.func.value, ast.Name) and node.func.value.id == 'handler'
             and node.func.attr == 'generate_music']
    calls += [(node, high_fields) for node in ast.walk(trees['adapter'])
              if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
              and node.func.id == 'GenerationParams']
    problems = []
    for call, fields in calls:
        problems.extend('argument:' + keyword.arg for keyword in call.keywords
                        if keyword.arg is not None and keyword.arg not in fields)
    # instruction is passed through a dynamic kwargs dict / attribute assignment.
    for name, fields in [('direct', direct_fields), ('high_level', high_fields)]:
        if 'instruction' not in fields:
            problems.append(name + ':instruction')
    constants = {}
    for node in trees['tasks'].body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id in {'TASK_TYPES_BASE', 'TASK_TYPES_TURBO'}:
                    constants[target.id] = ast.literal_eval(node.value)
    wanted = {'text2music', 'cover', 'repaint', 'lego', 'extract', 'complete'}
    for task in wanted - set(constants.get('TASK_TYPES_BASE', [])):
        problems.append('base_task:' + task)
    for task in {'text2music', 'cover', 'repaint'} - set(constants.get('TASK_TYPES_TURBO', [])):
        problems.append('turbo_task:' + task)
    if len(calls) != 2:
        problems.append('wrapper_calls_not_identified')
    return {'scope': 'installed_source_contract_not_runtime_or_audio_verification',
            'compatible': not problems, 'problems': sorted(problems),
            'base_tasks': constants.get('TASK_TYPES_BASE', []),
            'turbo_tasks': constants.get('TASK_TYPES_TURBO', []),
            'source_sha256': hashes, 'model_loaded': False, 'audio_generated': False}


if __name__ == '__main__':
    try:
        result = inspect_contract(Path(__file__).resolve().parents[1])
    except (OSError, ValueError, SyntaxError, StopIteration) as error:
        print(json.dumps({'compatible': False, 'inspection_error': str(error)}, ensure_ascii=False))
        sys.exit(1)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    sys.exit(0 if result['compatible'] else 1)
