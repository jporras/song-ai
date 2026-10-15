"""Bound diagnostic history while preserving current creative inputs for assistants."""
from copy import deepcopy


def specification_context(record):
    """Keep canonical fields/provenance; phase_data already supplies full details."""
    if not record:
        return None
    result = deepcopy(record)
    spec = result.get('json_spec', {})
    spec.pop('_editor_phases', None)
    spec.pop('_retained_intent', None)
    if spec.get('_lyrics_document'):
        spec['_lyrics_document'] = {'sha256':spec['_lyrics_document']['sha256'],
                                   'text_source':'phase_data.lyrics.data.lyricsEditor.content',
                                   'sections_source':'phase_data.lyrics.data.lyricSections'}
    return result


def assistant_context(value):
    if isinstance(value, list):
        return [assistant_context(item) for item in value]
    if not isinstance(value, dict):
        return deepcopy(value)
    result = {}
    for key, item in value.items():
        if key == "events" and isinstance(item, list):
            result["history_event_count"] = len(item)
            result["recent_events"] = [{field: entry.get(field) for field in
                ("phase", "status", "message", "created_at", "active_model")} for entry in item[-3:] if isinstance(entry, dict)]
        else:
            result[key] = assistant_context(item)
    return result
