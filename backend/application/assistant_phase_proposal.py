"""Bind conversational form proposals to their persisted MusicSpec input."""
from copy import deepcopy
import hashlib
import json


def validate_assistant_revision(project, requested_revision):
    current = (project or {}).get('music_spec_revision_id')
    if requested_revision is not None and requested_revision != current:
        raise ValueError('La ficha cambió. Recarga el proyecto antes de consultar al asistente.')
    return current


def bind_phase_proposal(patch, project, question):
    result = deepcopy(patch)
    revision = (project or {}).get('music_spec_revision_id')
    phase = result.get('phase')
    baseline = (project or {}).get('phase_data', {}).get(phase, {}).get('data', {})
    result.update({
        'schema_version': 'assistant_phase_proposal_v1',
        'source_project_id': (project or {}).get('set', {}).get('set_id'),
        'source_revision_id': revision,
        'source_phase_sha256': hashlib.sha256(json.dumps(baseline, sort_keys=True, ensure_ascii=False).encode()).hexdigest(),
        'question': question,
        'persisted': False,
        'requires_user_save': True,
        # The form parser is deterministic; the conversational model does not
        # produce these values and a question is not creative confirmation.
        'producer': 'deterministic_question_parser',
        'confirmation': 'proposed',
        'transformations': ['question_to_phase_fields_v1'],
    })
    return result


def reviewed_proposal_trace(supplied, expected, phase, saved_data):
    if not isinstance(supplied, dict) or len(json.dumps(supplied, ensure_ascii=False)) > 32768:
        raise ValueError('La traza de propuesta no es válida.')
    for key in ('source_project_id', 'source_revision_id', 'source_phase_sha256', 'phase', 'changes', 'question'):
        if supplied.get(key) != expected.get(key):
            raise ValueError('La propuesta cambió o pertenece a otra revisión; consulta de nuevo antes de guardarla.')
    if not expected.get('available') or expected.get('phase') != phase:
        raise ValueError('La propuesta no corresponde a esta fase.')
    sections = {'intent':'intent', 'lyrics':'lyrics', 'music-plan':'musicPlan',
                'voice':'voice', 'instrumental':'instrumental', 'midi':'midiPlan'}
    actual = saved_data.get(sections.get(phase), {})
    decisions = {}
    for field, value in expected['changes'].items():
        final = actual.get(field)
        # Placeholders are merged in the form; compare the proposed keys only.
        comparison = {k: final.get(k) for k in value} if field == 'placeholders' and isinstance(final, dict) else final
        decisions[field] = {'proposed_value':deepcopy(value), 'saved_value':deepcopy(final),
                            'review_result':'accepted' if comparison == value else 'user_modified'}
    return {**deepcopy(expected), 'decisions':decisions,
            'confirmation':'explicit_user_save', 'persisted':True,
            'transformations':expected['transformations'] + ['reviewed_phase_save_v1']}


def reviewed_proposal_batch(supplied, expected, phase, saved_data):
    if not isinstance(supplied, list) or len(supplied) > 20 or len(json.dumps(supplied, ensure_ascii=False)) > 262144:
        raise ValueError('Guarda un máximo de 20 propuestas revisadas por fase.')
    if len(supplied) != len(expected):
        raise ValueError('La lista de propuestas no coincide con su revisión.')
    traces = [reviewed_proposal_trace(item, origin, phase, saved_data)
              for item, origin in zip(supplied, expected)]
    for index, trace in enumerate(traces):
        trace['application_order'] = index + 1
        for field, decision in trace['decisions'].items():
            later = [i + 1 for i in range(index + 1, len(traces)) if field in traces[i]['changes']]
            if field == 'placeholders':
                keys = set(trace['changes'][field])
                later = [i for i in later if keys.intersection(traces[i - 1]['changes'][field])]
                replaced = set().union(*(keys.intersection(traces[i - 1]['changes'][field]) for i in later)) if later else set()
                if later and replaced != keys:
                    decision['review_result'] = 'partially_superseded_by_later_proposal'
                    decision['superseded_keys'] = sorted(replaced)
                    continue
            if later:
                decision['review_result'] = 'superseded_by_later_proposal'
                decision['superseded_by_application'] = later[-1]
    return traces
