"""Resolve wrapper defaults and explain them; engine observations stay separate."""
import json
import hashlib
import math
from pathlib import Path

INPUT_ARGUMENTS = {
    'bpm':'bpm', 'key_scale':'key_scale', 'time_signature':'time_signature',
    'vocal_language':'vocal_language', 'audio_duration':'duration', 'task_type':'task_type',
    'generation_api':'generation_api', 'lm_model_path':'lm_model_path', 'seed':'seed',
    'inference_steps':'infer_step', 'guidance_scale':'guidance_scale', 'shift':'shift',
    'reference_audio':'reference_audio', 'src_audio':'src_audio', 'instruction':'instruction',
    'repainting_start':'repainting_start', 'repainting_end':'repainting_end',
    'audio_cover_strength':'audio_cover_strength', 'chunk_mask_mode':'chunk_mask_mode',
}


def load_execution_context(path):
    if not path:
        return None
    context_path = Path(path)
    if context_path.stat().st_size > 65536:
        raise ValueError('Contexto de ejecución demasiado grande.')
    context = json.loads(context_path.read_text(encoding='utf-8'))
    if not isinstance(context, dict) or any(not isinstance(context.get(key, {}), dict) for key in ('requested_options','provenance','execution_profile')):
        raise ValueError('Contexto de ejecución no válido.')
    if set(context.get('requested_options', {})) - {'seed','inference_steps','guidance_scale','shift'}:
        raise ValueError('Opciones de ejecución sin regla de trazabilidad.')
    if 'approved_inputs' in context:
        inputs = context['approved_inputs']
        if (not isinstance(inputs, dict) or set(inputs) - set(INPUT_ARGUMENTS) - {'captions','lyrics'}
                or not {'captions','lyrics','task_type'} <= set(inputs)
                or not isinstance(context.get('spec_revision_id'), str) or not context['spec_revision_id']):
            raise ValueError('Inputs aprobados sin contrato o revision valida.')
        for value in inputs.values():
            if type(value) not in (str, int, float) or (type(value) in (int, float) and not math.isfinite(value)):
                raise ValueError('Valor de input aprobado no valido.')
    checksums = context.get('approved_audio_sha256', {})
    if (not isinstance(checksums, dict) or set(checksums) - {'src_audio','reference_audio'}
            or any(not isinstance(v, str) or len(v) != 64 or any(c not in '0123456789abcdef' for c in v) for v in checksums.values())):
        raise ValueError('Evidencia de audio aprobada no valida.')
    if checksums and not set(checksums) <= set(context.get('approved_inputs', {})):
        raise ValueError('Evidencia de audio sin input aprobado correspondiente.')
    return context


def runtime_input_trace(args, prompt, lyrics, context=None):
    """Compare every approved request input before loading models or deleting output."""
    context = context or {}
    approved = context.get('approved_inputs')
    if approved is None:
        return {'status':'legacy_context_without_full_input_contract', 'entries':[],
                'scope':'wrapper_inputs_not_engine_observation_or_audio_quality'}
    options = runtime_options(args)
    entries = []
    for field, expected in approved.items():
        actual = (prompt if field == 'captions' else lyrics if field == 'lyrics' else
                  options[field] if field in options else getattr(args, INPUT_ARGUMENTS[field]))
        if actual != expected:
            raise ValueError('El wrapper cambio un input aprobado: ' + field)
        entry = {'field':field, 'approved_value':expected, 'wrapper_value':actual,
                 'transformation':'approved_request_identity_v1'}
        checksum = context.get('approved_audio_sha256', {}).get(field)
        if checksum:
            digest = hashlib.sha256()
            with Path(actual).open('rb') as audio:
                for chunk in iter(lambda: audio.read(1024 * 1024), b''):
                    digest.update(chunk)
            if digest.hexdigest() != checksum:
                raise ValueError('El audio seleccionado cambio desde la aprobacion: ' + field)
            entry['verified_audio_sha256'] = checksum
        entries.append(entry)
    return {'schema_version':'runtime_inputs_v1', 'status':'approved_inputs_match',
            'scope':'wrapper_inputs_not_engine_observation_or_audio_quality',
            'spec_revision_id':context['spec_revision_id'], 'plan_sha256':context.get('plan_sha256'), 'entries':entries}


def runtime_options(args):
    turbo = 'turbo' in args.config_path
    return {'seed':args.seed, 'inference_steps':args.infer_step,
            'guidance_scale':args.guidance_scale if args.guidance_scale is not None else (1.0 if turbo else 15.0),
            'shift':args.shift if args.shift is not None else (3.0 if turbo else 1.0)}


def runtime_trace(args, context=None):
    values = runtime_options(args)
    context = context or {}
    requested = context.get('requested_options', {})
    provenance = context.get('provenance', {})
    if context.get('execution_profile', {}).get('config_path', args.config_path) != args.config_path:
        raise ValueError('El modelo del wrapper no coincide con el perfil registrado.')
    for field, requested_value in requested.items():
        if field not in values or values[field] != requested_value:
            raise ValueError('El wrapper cambió una opción aprobada: ' + field)
    return {'schema_version':'runtime_options_v1', 'scope':'wrapper_arguments_not_engine_observation_or_audio_quality',
        'spec_revision_id':context.get('spec_revision_id'),
        'config_path':args.config_path, 'execution_profile':context.get('execution_profile'),
        'entries':[{'field':key, 'requested_value':requested.get(key), 'wrapper_value':value,
            'source':'approved_override' if key in requested else 'execution_profile' if key == 'inference_steps' and context else 'wrapper_default_or_cli',
            'provenance':provenance.get(key, {}), 'transformation':'runtime_default_resolution_v1'}
            for key,value in values.items()]}
