"""Validate retained creative controls before changing the active specification."""
import math


def validate_phase_ranges(phase, data):
    definitions = {
        'instrumental': ('instrumental', ('depth', 'brightness', 'movement', 'stereoWidth'), 'stems'),
        'voice': ('voice', ('breaths', 'humanization', 'vibrato', 'layerBlend'), 'layers'),
        'music-plan': ('musicPlan', (), 'sections'),
        'midi': ('midiPlan', ('humanization', 'velocity', 'melodyDensity', 'swing'), None),
    }
    if phase not in definitions:
        return
    section, keys, collection = definitions[phase]
    values = data.get(section, {})
    def check(value, maximum=100):
        if type(value) not in (int, float) or not math.isfinite(value) or not 0 <= value <= maximum:
            raise ValueError('Revisa los valores numéricos: deben estar dentro del rango indicado junto al control.')
    if not isinstance(values, dict):
        raise ValueError('La sección de configuración debe ser un objeto.')
    for key in keys:
        if key in values:
            check(values[key], 127 if key == 'velocity' else 60 if key == 'swing' else 100)
    if collection and collection in values:
        items = values[collection]
        if not isinstance(items, list) or any(not isinstance(item, dict) for item in items):
            raise ValueError('Las capas y secciones deben ser una lista de objetos.')
        key = 'intensity' if phase == 'music-plan' else 'level'
        for item in items:
            if key in item:
                check(item[key])
