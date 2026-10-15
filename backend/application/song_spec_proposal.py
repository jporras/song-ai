"""Validate a model proposal without changing the active SQLite specification."""
from copy import deepcopy
import json
import math
from models.song_spec_field_types import NUMBER_CONTROLS, LIST_CONTROLS


def engine_input_check(spec: dict) -> dict | None:
    if not spec.get('task_type') or not spec.get('ace_step_config'):
        return None
    from models.ace_step_tasks import validate_task_inputs
    errors = []
    try:
        validate_task_inputs(spec['task_type'], spec['ace_step_config'],
            spec.get('src_audio') or '', spec.get('instruction') or '',
            spec.get('repainting_start') or 0,
            spec.get('repainting_end') if spec.get('repainting_end') is not None else -1,
            tuple(spec.get('target_tracks') or []))
    except (ValueError, TypeError) as error:
        errors.append(str(error))
    return {'source': 'deterministic_task_contract', 'status': 'conflict' if errors else 'structurally_compatible',
            'errors': errors, 'generation_verified': False, 'source_audio_verified': False}


def proposal_summary(proposal: dict) -> str:
    coverage = proposal['coverage']
    return (f"Propuesta tecnica: {coverage['covered']} de {coverage['total']} parametros contemplados, "
            f"{len(proposal['missing_fields'])} datos obligatorios pendientes y "
            f"{len(proposal['conflicts'])} conflictos por revisar. Revisa los valores antes de confirmar.")


def latest_current_proposal(tasks: list[dict], song_id: str, revision_id: str) -> dict | None:
    """Recover a persisted proposal only for this project and its current revision."""
    for task in sorted(tasks, key=lambda item: item.get('created_at', ''), reverse=True):
        if (task.get('task_type') != 'compile_song_spec' or task.get('status') != 'completed'
                or task.get('payload', {}).get('project_id') != song_id):
            continue
        result = task.get('result', {})
        proposal = result.get('spec_proposal')
        if (result.get('mode') == 'provider_handoff' and result.get('provider_executed')
                and proposal and proposal.get('validation_version') == 2
                and proposal.get('source_revision_id') == revision_id):
            recovered = {**deepcopy(proposal), 'song_id': song_id, 'task_id': task['task_id']}
            recovered['model_summary'] = recovered.get('model_summary', recovered.get('summary', ''))
            recovered['summary'] = proposal_summary(recovered)
            return recovered
    return None


def specification_proposal(response: str, context: dict) -> dict:
    raw = response.strip()
    if raw.startswith('```') and raw.endswith('```'):
        raw = '\n'.join(raw.splitlines()[1:-1])
    try:
        result = json.loads(raw)
    except (ValueError, TypeError) as error:
        raise ValueError('Qwen no devolvio una propuesta JSON valida; la ficha activa se conserva.') from error
    if not isinstance(result, dict) or not isinstance(result.get('spec'), dict):
        raise ValueError('La propuesta de Qwen no contiene una ficha estructurada.')
    fields = context['fields']
    proposed = result['spec']
    missing = sorted(set(fields) - set(proposed))
    if missing:
        raise ValueError('La propuesta no cubre el catalogo completo: ' + ', '.join(missing))
    unknown = set(proposed) - set(fields)
    if unknown:
        raise ValueError('La propuesta incluye campos fuera del catalogo: ' + ', '.join(sorted(unknown)))
    existing = context['current_spec']
    for key, value in proposed.items():
        if value is not None and fields[key]['control'] in NUMBER_CONTROLS and (isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value)):
            raise ValueError(f'La propuesta contiene un numero invalido: {key}.')
        if value is not None and fields[key]['control'] in LIST_CONTROLS and (not isinstance(value, list) or any(not isinstance(item, str) for item in value)):
            raise ValueError(f'La propuesta contiene una lista invalida: {key}.')
        options = fields[key].get('options', [])
        if value not in (None, '') and options and value not in options:
            raise ValueError(f'La propuesta contiene una opcion no admitida: {key}.')
        if existing.get(key) not in (None, '', []) and existing[key] != value:
            raise ValueError(f'Qwen intento cambiar el valor vigente de {key}; requiere una propuesta de cambio explicita.')
    if not isinstance(result.get('conflicts'), list) or not isinstance(result.get('missing_fields'), list):
        raise ValueError('La propuesta debe declarar conflictos y datos pendientes.')
    if any(not isinstance(item, str) or len(item.split()) < 3 or item.strip() in fields for item in result['conflicts']):
        raise ValueError('Qwen debe explicar cada contradiccion concreta, no devolver solamente nombres de campos.')
    if any(not isinstance(key, str) or key not in fields for key in result['missing_fields']):
        raise ValueError('Los datos pendientes deben ser claves del catalogo.')
    compiled = {**deepcopy(existing), **deepcopy(proposed)}
    model_conflicts = deepcopy(result['conflicts'])
    missing_values = [key for key, field in fields.items()
                      if field.get('required_for_spec') and compiled.get(key) in (None, '', [])]
    model_missing_fields = deepcopy(result['missing_fields'])
    result['missing_fields'] = sorted(set(missing_values))
    engine_check = engine_input_check(compiled)
    if engine_check:
        result['conflicts'].extend('Validacion del motor: ' + error for error in engine_check['errors'])
    provenance = deepcopy(existing.get('_provenance', {}))
    for key in proposed:
        if existing.get(key) in (None, '', []) and proposed[key] not in (None, '', []):
            provenance[key] = {'source': 'qwen_proposal', 'note': 'Propuesta sin confirmacion del usuario.'}
    compiled['_provenance'] = provenance
    proposal = {'validation_version': 2, 'spec': compiled, 'conflicts': result['conflicts'], 'missing_fields': result['missing_fields'],
            'model_conflicts': model_conflicts,
            'model_missing_fields': model_missing_fields,
            'model_summary': str(result.get('summary', '')),
            'coverage': {'covered': len(fields), 'total': len(fields)},
            'user_confirmation_status': 'pending', 'source_revision_id': context['source_revision_id'],
            'active_spec_modified': False}
    proposal['summary'] = proposal_summary(proposal)
    return proposal
