"""Creative section notes remain metadata, never words to sing."""

DIRECTION_FIELDS = ('direction', 'energy', 'vocal_direction', 'instrument_direction')


def validate_section_directions(sections, previous=(), unlocks=None):
    unlocks = [] if unlocks is None else unlocks
    if not isinstance(unlocks, list) or any(not isinstance(item, str) for item in unlocks):
        raise ValueError('Los desbloqueos de dirección deben identificar secciones.')
    old = {section['id']:section for section in previous}
    incoming = {section.get('id'):section for section in sections}
    for section in sections:
        if not isinstance(section.get('direction_locked', False), bool):
            raise ValueError('La protección de dirección debe ser verdadero o falso.')
        for field in DIRECTION_FIELDS:
            value = section.get(field, '')
            if not isinstance(value, str) or len(value) > 1000:
                raise ValueError('La dirección por sección debe ser texto de hasta 1000 caracteres por campo.')
    for section_id in unlocks:
        if not old.get(section_id, {}).get('direction_locked') or section_id not in incoming or incoming[section_id].get('direction_locked'):
            raise ValueError('Revisa el desbloqueo explícito de dirección.')
    for section_id, section in old.items():
        if section.get('direction_locked') and section_id not in unlocks:
            current = incoming.get(section_id)
            if not current or not current.get('direction_locked') or any(current.get(field, '') != section.get(field, '') for field in DIRECTION_FIELDS):
                raise ValueError('La dirección está protegida. Desbloquéala explícitamente antes de editarla.')


def section_direction_trace(spec):
    return [{'section_id':section['id'], 'section_type':section['type'],
             'requested':{field:section[field] for field in DIRECTION_FIELDS if section.get(field)},
             'locked':section.get('direction_locked', False),
             'source_path':f"_lyrics_document.sections[{index}]",
             'route':'retained_not_sent_to_engine', 'transformations':[],
             'reason':'Sin traducción por sección validada; requiere revisión musical del resultado.'}
            for index, section in enumerate(spec.get('_lyrics_document', {}).get('sections', []))
            if any(section.get(field) for field in DIRECTION_FIELDS)]
