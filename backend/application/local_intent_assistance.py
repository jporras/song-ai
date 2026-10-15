"""Discuss a user's request against persisted context without editing MusicSpec."""
import json


def provider_intent_guidance(registry, payload):
    prompt = json.dumps({'task':'collect_song_intent', 'context':payload['context'],
        'output_contract':{'format':'plain_text', 'language':'Spanish',
            'explain_three_required_pieces':True, 'preserve_confirmed_decisions':True,
            'suggestions_require_explicit_save':True, 'do_not_claim_qwen_review':True}}, ensure_ascii=False)
    try:
        response = registry.interpret_with_active_provider(prompt, 'collect_song_intent')
    except (OSError, TimeoutError, ValueError, RuntimeError) as error:
        return {'summary':'No se pudo revisar la intención. La ficha se conserva.',
                'mode':'provider_error', 'provider_executed':False, 'provider_error':str(error)}
    text = response.get('summary')
    real = response.get('mode') in {'llama_cpp','provider_handoff'}
    if not real or not isinstance(text, str) or not text.strip() or len(text) > 16000:
        return {'summary':'La asistencia no devolvió una respuesta real utilizable. La ficha se conserva.',
                'mode':'provider_invalid_output' if real else 'mock_handoff', 'provider_executed':real}
    return {'summary':text.strip(), 'mode':'provider_handoff', 'provider_executed':True,
            'intent_guidance':{'source_project_id':payload['project_id'],
                'source_revision_id':payload['context']['source_revision_id'],
                'requires_user_save':True, 'active_spec_modified':False,
                'approved_by_qwen':False, 'user_confirmation_status':'proposed'},
            'engine_steering':response.get('engine_steering', {})}


class CollectLocalIntent:
    def __init__(self, storage, orchestrator):
        self.storage, self.orchestrator = storage, orchestrator

    def execute(self, song_id, payload):
        from application.local_project_queries import LocalProjectQueries
        project = self.storage.get_song_project(song_id)
        if not project:
            raise ValueError('Proyecto no encontrado.')
        message = payload.get('message')
        if not isinstance(message, str) or not message.strip() or len(message) > 8192:
            raise ValueError('Describe tu intención con texto de entre 1 y 8192 caracteres.')
        record = project.get('spec') or {}
        revision = record.get('revision', {}).get('revision_id')
        if payload.get('spec_revision_id', revision) != revision:
            raise ValueError('La ficha cambió. Recarga antes de consultar al asistente.')
        context = {'user_request':message.strip(), 'current_spec':record.get('json_spec', {}),
                   'source_revision_id':revision, 'project_name':project['title'],
                   'preparation_without_spec':not bool(record)}
        if project.get('user_id', '').startswith('set:'):
            context['selected_set'] = self.storage.get_song_set(project['user_id'][4:])
        handoff = self.orchestrator.run_handoff({'model_role':'assistant','task_type':'collect_song_intent',
            'project_id':song_id,'project_name':project['title'],'phase':'SONG_SPEC_COLLECTION',
            'context':context})
        return {**LocalProjectQueries(self.storage).get(song_id), 'handoff':handoff,
                'gemma':{'message':handoff['summary'], 'assistant_inference_executed':handoff['result']['provider_executed']},
                'active_spec_modified':False, 'requires_user_save':True}
