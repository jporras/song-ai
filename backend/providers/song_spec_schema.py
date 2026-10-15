"""Structured decoding contract for local technical specification proposals."""
import json
from models.song_spec_field_types import NUMBER_CONTROLS, LIST_CONTROLS


def proposal_schema(prompt: str) -> dict:
    # Steering precedes the serialized task. Decode only the task payload.
    task = json.loads(prompt.rsplit('Solicitud y contexto del proyecto:\n', 1)[-1])
    context = task['context']
    existing = context['current_spec']
    properties = {}
    for key, field in context['fields'].items():
        value = existing.get(key)
        if value not in (None, '', []):
            properties[key] = {'enum': [value]}
        elif field.get('applicable') is False or field['control'] in {'artifact', 'informational', 'voice_profile'}:
            properties[key] = {'enum': [value] if value is not None else [None]}
        elif field.get('options'):
            properties[key] = {'enum': [*field['options'], None, '']}
        elif field['control'] in NUMBER_CONTROLS:
            properties[key] = {'type': ['number', 'null']}
        elif field['control'] in LIST_CONTROLS:
            properties[key] = {'type': ['array', 'null'], 'items': {'type': 'string'}}
        else:
            properties[key] = {'type': ['string', 'null']}
    return {'type': 'object', 'additionalProperties': False,
            'required': ['spec', 'conflicts', 'missing_fields', 'summary'],
            'properties': {
                'spec': {'type': 'object', 'properties': properties,
                         'required': list(properties), 'additionalProperties': False},
                'conflicts': {'type': 'array', 'items': {'type': 'string', 'minLength': 40, 'maxLength': 220}},
                'missing_fields': {'type': 'array', 'items': {'enum': [key for key, field in context['fields'].items()
                    if field.get('required_for_spec')] or list(properties)}},
                'summary': {'type': 'string', 'maxLength': 350}}}
