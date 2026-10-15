"""A complete lyric proposal is task evidence, never an implicit spec edit."""
import json
import re


def lyrics_content_protected(value):
    if isinstance(value, dict):
        return (value.get('locked') is True or value.get('direction_locked') is True
                or bool(value.get('protected_lines'))
                or any(lyrics_content_protected(v) for v in value.values()))
    return isinstance(value, list) and any(lyrics_content_protected(v) for v in value)


def valid_lyrics_markdown(text):
    """Accept only sectioned song text within the connected ACE-Step limit."""
    if not text.startswith('## ') or len(text) + 1 > 4096:
        return False
    sections = re.split(r'^##\s+[^\n]+\n', text, flags=re.MULTILINE)
    return len(sections) > 1 and not sections[0] and all(s.strip() for s in sections[1:])


def provider_lyrics_proposal(registry, payload):
    context = payload['context']
    prompt = json.dumps({'task':'propose_full_lyrics', 'context':context,
        'output_contract':{'format':'markdown', 'sections':'## section name followed by sung text',
            'preserve_user_constraints':True, 'max_characters':4095,
            'explanations_outside_lyrics':False}}, ensure_ascii=False)
    try:
        response = registry.interpret_with_active_provider(prompt, 'propose_full_lyrics')
    except (OSError, TimeoutError, ValueError, RuntimeError) as error:
        return {'summary':'No se pudo preparar la propuesta de letra.', 'mode':'provider_error',
                'provider_executed':False, 'provider_error':str(error)}
    mode = response.get('mode', 'unknown')
    text = str(response.get('summary', '')).strip()
    real = mode in {'llama_cpp','provider_handoff'}
    spec = context['current_spec']
    required = spec.get('required_phrases', [])
    excluded = spec.get('excluded_content', [])
    violates = (any(phrase.casefold() not in text.casefold() for phrase in required if isinstance(phrase,str) and phrase.strip()) or
                any(phrase.casefold() in text.casefold() for phrase in excluded if isinstance(phrase,str) and phrase.strip()))
    if not real or not valid_lyrics_markdown(text) or violates:
        return {'summary':'La respuesta no contiene una propuesta de letra verificable.',
                'mode':'provider_invalid_output' if real else 'mock_handoff', 'provider_executed':real}
    return {'summary':'Propuesta de letra preparada; revisa antes de guardar.',
            'mode':'provider_handoff','provider_executed':True,
            'lyrics_proposal':{'markdown':text, 'source_revision_id':context['source_revision_id'],
                'source_project_id':payload['project_id'], 'requires_user_save':True,
                'confirmation':'proposed', 'persisted_in_music_spec':False},
            'engine_steering':response.get('engine_steering', {})}


class PrepareFullLyricsProposal:
    def __init__(self, storage, orchestrator):
        self.storage, self.orchestrator = storage, orchestrator

    def execute(self, song_id):
        project = self.storage.get_song_project(song_id)
        if not project or not project.get('spec'):
            raise ValueError('Prepara la definición antes de pedir una letra.')
        record = project['spec']
        spec = record['json_spec']
        # Whole-document generation must not replace protected sections or lines.
        if lyrics_content_protected(spec.get('_lyrics_document')) or lyrics_content_protected(spec.get('_editor_phases', {}).get('lyrics')) or spec.get('_provenance', {}).get('lyrics', {}).get('locked'):
            raise ValueError('La letra tiene contenido protegido. Usa la asistencia por sección para conservarlo.')
        handoff = self.orchestrator.run_handoff({'model_role':'assistant','task_type':'propose_full_lyrics',
            'project_id':song_id,'project_name':project['title'],'phase':'LYRICS_GENERATION',
            'context':{'current_spec':spec,'source_revision_id':record['revision']['revision_id']}})
        return {'project':project,'handoff':handoff,'lyrics_proposal':handoff['result'].get('lyrics_proposal')}


def reviewed_full_lyrics_trace(storage, supplied, project, saved_data):
    """Resolve provenance from persisted task evidence, never client claims."""
    import hashlib
    if not isinstance(supplied, dict) or not isinstance(supplied.get('task_id'), str):
        raise ValueError('La propuesta de letra no tiene una tarea de origen válida.')
    task = next((t for t in storage.list_tasks() if t['task_id'] == supplied['task_id']), {})
    proposal = task.get('result', {}).get('lyrics_proposal', {})
    revision = project['spec']['revision']['revision_id']
    if (task.get('status') != 'completed' or task.get('task_type') != 'propose_full_lyrics'
            or proposal.get('source_project_id') != project['id']
            or proposal.get('source_revision_id') != revision):
        raise ValueError('La propuesta pertenece a otra ficha o revisión. Solicita una nueva propuesta.')
    sections = saved_data.get('lyricSections', [])
    markdown = '\n\n'.join('## ' + s['type'] + '\n' + s['text'].strip() for s in sections).strip()
    return {'task_id':task['task_id'], 'source_project_id':project['id'],
        'source_revision_id':revision, 'producer':'assistant_provider',
        'proposed_markdown':proposal['markdown'],
        'saved_markdown_sha256':hashlib.sha256(markdown.encode()).hexdigest(),
        'review_result':'accepted' if markdown == proposal['markdown'].strip() else 'user_modified_or_editor_normalized',
        'confirmation':'explicit_user_save', 'persisted':True,
        'transformations':['markdown_to_editor_sections_v1','reviewed_phase_save_v1']}
