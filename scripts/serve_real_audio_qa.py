"""Serve the existing UI against an isolated completed audio QA database."""
import argparse
import json
import os
import sys
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('result', type=Path)
    parser.add_argument('--port', type=int, default=8025)
    parser.add_argument('--check-only', action='store_true')
    args = parser.parse_args()
    result_path = args.result.resolve()
    result = json.loads(result_path.read_text(encoding='utf-8'))
    directory = Path(result['qa_directory']).resolve()
    if (directory.parent != (ROOT/'data').resolve() or not directory.name.startswith('qa_')
            or result_path.parent != directory):
        raise ValueError('Only a result inside its isolated QA directory can be served.')
    if result.get('status') != 'completed':
        raise ValueError('Finish audio generation before serving its QA result.')
    if args.check_only:
        print(json.dumps({'status':'ready_for_ui_review', 'qa_directory':str(directory),
                          'song_id':result['song_id'], 'task_id':result['task_id']}))
        return
    os.environ.update(SONG_AI_LLM_AUTOSTART='false', SONG_AI_STOP_LLM_ON_EXIT='false',
                      SONG_AI_BOOTSTRAP_ON_START='false', SONG_AI_RESOURCE_MONITOR_ENABLED='false')
    sys.path.insert(0, str(ROOT/'backend'))
    from config.settings import Settings
    original = Settings.load()
    configured = replace(original, data_dir=directory,
        local_models=replace(original.local_models, llama_cpp_enabled=False),
        resource_monitor=replace(original.resource_monitor, enabled=False,
                                 stop_llm_command='', start_llm_command=''))
    Settings.load = classmethod(lambda cls: configured)
    from adapters.http.fastapi_app import app
    import uvicorn
    uvicorn.run(app, host='127.0.0.1', port=args.port)


if __name__ == '__main__':
    main()
