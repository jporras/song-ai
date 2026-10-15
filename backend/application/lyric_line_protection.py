"""Validate explicit USER protection of literal lyric lines before persistence."""


def validate_line_protection(previous, incoming, unlocks):
    if not isinstance(incoming, list) or any(not isinstance(section, dict) or not isinstance(section.get('text', ''), str) for section in incoming):
        raise ValueError('Las secciones de letra deben contener texto válido.')
    if unlocks is None:
        unlocks = []
    if not isinstance(unlocks, list) or any(not isinstance(item, str) for item in unlocks):
        raise ValueError('Los desbloqueos de líneas deben ser una lista de identificadores.')
    old = {section['id']: section for section in previous}
    new = {section['id']: section for section in incoming if isinstance(section, dict) and 'id' in section}
    for section in incoming:
        indexes = section.get('protected_lines', [])
        lines = section.get('text', '').split('\n')
        if not isinstance(indexes, list) or any(type(i) is not int or i < 0 or i >= len(lines) for i in indexes) or len(set(indexes)) != len(indexes):
            raise ValueError('Las líneas protegidas deben identificar líneas existentes sin duplicados.')
    valid_unlocks = set()
    for section_id, section in old.items():
        updated = new.get(section_id, {})
        before = section.get('text', '').split('\n')
        after = updated.get('text', '').split('\n')
        for index in section.get('protected_lines', []):
            key = f'{section_id}:{index}'
            if key in unlocks and index not in updated.get('protected_lines', []):
                valid_unlocks.add(key)
                continue
            if index not in updated.get('protected_lines', []) or index >= len(after) or before[index] != after[index]:
                raise ValueError('Una línea protegida cambió. Desbloquéala explícitamente antes de editarla.')
    if set(unlocks) != valid_unlocks:
        raise ValueError('El desbloqueo debe corresponder a una línea previamente protegida.')
