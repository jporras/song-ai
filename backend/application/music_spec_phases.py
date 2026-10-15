"""Legacy forms are projections and explicit commands on one MusicSpec revision.

Additional phase details live in that revision too. Saving is one SQLite spec
write, rather than attempting two separately committed authoritative writes.
"""
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json

from application.music_spec_edit import EditMusicSpec
from application.music_spec_snapshot_export import export_music_spec

PHASE_FIELDS = {
    'intent': ('intent', {'description':'creative_brief', 'songType':'song_type',
        'language':'language', 'recipient':'recipient_name', 'bpm':'bpm', 'key':'key',
        'vocalType':'voice_style', 'instruments':'instruments'}),
    'music-plan': ('musicPlan', {'bpm':'bpm','key':'key','timeSignature':'time_signature','dynamicArc':'dynamic_arc'}),
    'lyrics': ('lyrics', {'language':'language','tone':'lyrical_tone','theme':'theme'}),
    'voice': ('voice', {'mainVoice':'voice_style','performance':'vocal_expression','pronunciation':'pronunciation'}),
    'instrumental': ('instrumental', {'layers':'instruments'}),
}


def linked_spec(store, set_id):
    candidates = [store.get_song_project(p['id']) for p in store.list_song_projects()
                  if p.get('user_id') == f'set:{set_id}']
    candidates = [p for p in candidates if p and p.get('spec')]
    if len(candidates) > 1:
        raise ValueError('Hay varias fichas vinculadas; resuelve el proyecto activo antes de editar sus fases.')
    return candidates[0] if candidates else None


def project_phases(base, record):
    result = deepcopy(base)
    if not record:
        return result
    spec = record['json_spec']
    result.update(deepcopy(spec.get('_editor_phases', {})))
    for phase, (section, fields) in PHASE_FIELDS.items():
        saved = result.setdefault(phase, {'phase':phase, 'status':'spec_projection'})
        values = saved.setdefault('data', {}).setdefault(section, {})
        for old, field in fields.items():
            if field in spec:
                values[old] = deepcopy(spec[field])
    lyrics = result.setdefault('lyrics', {}).setdefault('data', {})
    lyrics.setdefault('lyrics', {})['structure'] = ', '.join(spec.get('structure', []))
    lyrics['lyrics'].setdefault('placeholders', {})['name'] = spec.get('recipient_name', '')
    if spec.get('_lyrics_document'):
        document = spec['_lyrics_document']
        lyrics['lyricSections'] = deepcopy(document['sections'])
        lyrics.setdefault('lyricsEditor', {})['content'] = document['markdown']
    voice = result.setdefault('voice', {}).setdefault('data', {}).setdefault('voice', {})
    if 'section_direction' in spec:
        voice['sectionDirection'] = deepcopy(spec['section_direction'])
    for saved in result.values():
        saved['source_spec_revision_id'] = record.get('revision', {}).get('revision_id')
        saved['source_of_truth'] = 'music_spec_sqlite'
    return result


class _PhaseEdit(EditMusicSpec):
    technical_review_mode = 'user_phase_edit_on_music_spec'

    def __init__(self, store, source_audio, phase, snapshot, document, baseline):
        super().__init__(store, source_audio)
        self.phase, self.snapshot, self.document = phase, snapshot, document
        self.baseline = baseline

    def execute(self, song_id, request):
        record = self.store.get_song_project(song_id)['spec']
        spec = deepcopy(record['json_spec'])
        edits = request['values']
        self.validate_edits(edits)
        for field, value in edits.items():
            if spec.get('_provenance', {}).get(field, {}).get('locked') is True and spec.get(field) != value:
                raise ValueError('Esta decisión está bloqueada; desbloquéala antes de cambiarla.')
            spec[field] = deepcopy(value)
            spec.setdefault('_provenance', {})[field] = {'source':'explicit_user_phase',
                'source_phase':self.phase, 'confirmation':'pending', 'input_value':deepcopy(value),
                'source_snapshot_sha256':hashlib.sha256(json.dumps(self.snapshot['data'], sort_keys=True, ensure_ascii=False).encode()).hexdigest(),
                'transformations':['phase_field_projection_v1', 'section_structure_projection_v1'] if field == 'structure' else ['phase_field_projection_v1']}
        spec = self.amend_spec(spec, record)
        return self.store.upsert_song_spec(song_id=song_id, json_spec=spec,
            approved_by_qwen=False,
            deterministic_valid=record['revision'].get('deterministic_valid') is True,
            missing_fields=[f for f in record.get('missing_fields', []) if f not in edits or spec.get(f) in (None,'',[])],
            schema_version='1.1', technical_review_mode=self.technical_review_mode,
            user_confirmation_status='pending', expected_revision_id=request['revision_id'])

    def amend_spec(self, spec, record):
        for phase, snapshot in self.baseline.items():
            spec.setdefault('_editor_phases', {}).setdefault(phase, deepcopy(snapshot))
        spec.setdefault('_editor_phases', {})[self.phase] = deepcopy(self.snapshot)
        initial_lyrics = self.baseline.get('lyrics', {}).get('data', {})
        if not spec.get('_lyrics_document') and initial_lyrics.get('lyricSections') and initial_lyrics.get('lyricsEditor', {}).get('content'):
            text = initial_lyrics['lyricsEditor']['content']
            spec['_lyrics_document'] = {'sections':deepcopy(initial_lyrics['lyricSections']), 'markdown':text,
                                       'sha256':hashlib.sha256(text.encode()).hexdigest()}
            spec.setdefault('_provenance', {})['lyrics'] = {**spec.get('_provenance', {}).get('lyrics', {}), 'source':'persisted_project_lyrics',
                'sha256':spec['_lyrics_document']['sha256'], 'confirmation':'pending', 'transformations':[]}
        if self.phase == 'instrumental':
            spec.setdefault('_retained_intent', {})['instrumental'] = deepcopy(self.snapshot['data'])
        if self.phase == 'music-plan' and 'sections' in self.snapshot['data'].get('musicPlan', {}):
            spec['section_plan'] = deepcopy(self.snapshot['data']['musicPlan']['sections'])
        if self.phase == 'voice':
            spec.setdefault('_retained_intent', {})['voice_details'] = {
                key:deepcopy(value) for key,value in self.snapshot['data'].get('voice', {}).items()
                if key not in {'sectionDirection','sections'}}
        if self.document is not None:
            if spec.get('_provenance', {}).get('lyrics', {}).get('locked') is True:
                raise ValueError('La letra está bloqueada; desbloquéala antes de modificarla.')
            spec['_lyrics_document'] = deepcopy(self.document)
            spec.setdefault('_provenance', {})['lyrics'] = {'source':'explicit_user_phase',
                'source_phase':'lyrics', 'sha256':self.document['sha256'], 'confirmation':'pending',
                'transformations': ['section_text_to_markdown_v1']}
        if self.phase == 'voice' and 'sectionDirection' in self.snapshot['data'].get('voice', {}):
            direction = self.snapshot['data']['voice']['sectionDirection']
            if spec.get('_provenance', {}).get('section_direction', {}).get('locked') is True and spec.get('section_direction') != direction:
                raise ValueError('La dirección por sección está bloqueada; desbloquéala antes de cambiarla.')
            spec['section_direction'] = deepcopy(direction)
        return spec


class SaveMusicSpecPhase:
    def __init__(self, store, source_audio=None):
        self.store, self.source_audio = store, source_audio

    def execute(self, project, phase, data, expected_revision_id, status, phase_status, proposal_trace=None, unlocked_section_ids=None, unlocked_line_ids=None, unlocked_direction_ids=None):
        record = project['spec']
        if expected_revision_id != record.get('revision', {}).get('revision_id') or not expected_revision_id:
            raise ValueError('La ficha cambió. Recarga el proyecto y revisa tus cambios antes de guardar esta fase.')
        if phase in PHASE_FIELDS:
            section = PHASE_FIELDS[phase][0]
            if section in data and not isinstance(data[section], dict):
                raise ValueError('La sección de configuración debe ser un objeto.')
        from application.phase_range_validation import validate_phase_ranges
        validate_phase_ranges(phase, data)
        if phase == 'intent':
            import math
            for key in ('warmth', 'energy', 'nostalgia', 'cinematic'):
                values = data.get('intent', {})
                if key in values and (type(values[key]) not in (int, float) or not math.isfinite(values[key]) or not 0 <= values[key] <= 100):
                    raise ValueError('Revisa los valores emocionales: deben ser números entre 0 y 100.')
        if phase == 'lyrics' and 'lyricsEditor' in data and not isinstance(data['lyricsEditor'], dict):
            raise ValueError('El editor de letra debe ser un objeto.')
        baseline = project_phases(self.store.list_project_phase_data(project['user_id'][4:]), record)
        old = baseline.get(phase, {}).get('data', {})
        if phase == 'lyrics':
            from application.lyric_line_protection import validate_line_protection
            from application.lyric_section_direction import validate_section_directions
            validate_line_protection(old.get('lyricSections', []), data.get('lyricSections', []), unlocked_line_ids)
            validate_section_directions(data.get('lyricSections', []), old.get('lyricSections', []), unlocked_direction_ids)
            unlocked = unlocked_section_ids or []
            if not isinstance(unlocked, list) or any(not isinstance(item, str) for item in unlocked):
                raise ValueError('Los desbloqueos deben identificar secciones existentes.')
            previous = {s['id']:s for s in old.get('lyricSections', [])}
            if not isinstance(data.get('lyricSections', []), list):
                raise ValueError('Las secciones de letra deben ser una lista.')
            incoming = {s.get('id'):s for s in data.get('lyricSections', []) if isinstance(s, dict)}
            for section in incoming.values():
                if not isinstance(section.get('locked', False), bool):
                    raise ValueError('El bloqueo de sección debe ser verdadero o falso.')
            for section_id in unlocked:
                if not previous.get(section_id, {}).get('locked') or incoming.get(section_id, {}).get('locked', False):
                    raise ValueError('Revisa el desbloqueo explícito de la sección.')
            for section_id, section in previous.items():
                if section.get('locked') and section_id not in unlocked:
                    current = incoming.get(section_id)
                    if not current or not current.get('locked') or any(current.get(key) != section.get(key) for key in ('text','type')):
                        raise ValueError('Una sección protegida cambió. Desbloquéala explícitamente antes de editarla.')
        values = {}
        if phase in PHASE_FIELDS:
            section, mapping = PHASE_FIELDS[phase]
            for legacy, field in mapping.items():
                if legacy in data.get(section, {}) and data[section][legacy] != old.get(section, {}).get(legacy):
                    values[field] = deepcopy(data[section][legacy])
        document = None
        if phase == 'lyrics':
            name = data.get('lyrics', {}).get('placeholders', {}).get('name')
            if name is not None and name != old.get('lyrics', {}).get('placeholders', {}).get('name'):
                values['recipient_name'] = name
            declared = data.get('lyrics', {}).get('structure')
            if declared is not None and declared != old.get('lyrics', {}).get('structure'):
                if not isinstance(declared, str):
                    raise ValueError('La estructura debe ser texto con secciones separadas por coma.')
                values['structure'] = [item.strip() for item in declared.split(',') if item.strip()]
        if phase == 'lyrics' and (data.get('lyricSections') != old.get('lyricSections')
                                 or data.get('lyricsEditor', {}).get('content') != old.get('lyricsEditor', {}).get('content')):
            sections = data.get('lyricSections')
            if not isinstance(sections, list) or not sections or any(not isinstance(s, dict) or not all(isinstance(s.get(k), str) and s[k].strip() for k in ('id','type','text')) for s in sections):
                raise ValueError('Conserva al menos una sección de letra con identificador, tipo y texto.')
            if len({s['id'] for s in sections}) != len(sections):
                raise ValueError('Cada sección debe tener un identificador distinto.')
            markdown = '\n\n'.join(f"## {s['type']}\n{s['text'].strip()}" for s in sections).strip() + '\n'
            if data.get('lyricsEditor', {}).get('content') != markdown:
                raise ValueError('El texto y las secciones de letra no coinciden; revisa el editor antes de guardar.')
            if len(markdown) > 4096 or any(not s['text'].strip() for s in sections):
                raise ValueError('La letra necesita texto por sección y un máximo de 4096 caracteres para ACE-Step.')
            if 'structure' in values:
                aliases = {'verso':'verse','coro':'chorus','puente':'bridge','cierre':'outro'}
                normalized = lambda items: [aliases.get(item.lower(),item.lower()) for item in items]
                if normalized(values['structure']) != normalized([s['type'] for s in sections]):
                    raise ValueError('La estructura declarada y las secciones editadas se contradicen; revisa su orden antes de guardar.')
            document = {'sections':deepcopy(sections), 'markdown':markdown,
                        'sha256':hashlib.sha256(markdown.encode()).hexdigest()}
            values['structure'] = [s['type'].lower() for s in sections]
        if len(json.dumps(data, ensure_ascii=False)) > 262144:
            raise ValueError('La configuración de fase es demasiado grande.')
        if data == old:
            return {'record':record, 'saved':baseline[phase], 'changed':False}
        snapshot = {'phase':phase, 'data':deepcopy(data), 'status':status,
                    'phase_status':phase_status, 'change_source':'USER', 'validation_status':'review_pending',
                    'updated_at':datetime.now(timezone.utc).isoformat()}
        if proposal_trace:
            snapshot['reviewed_assistant_proposals'] = deepcopy(proposal_trace)
            snapshot['reviewed_assistant_proposal'] = deepcopy(proposal_trace[-1])
        if phase == 'lyrics' and unlocked_section_ids:
            snapshot['explicit_user_section_unlocks'] = list(unlocked_section_ids)
        if phase == 'lyrics' and unlocked_line_ids:
            snapshot['explicit_user_line_unlocks'] = list(unlocked_line_ids)
        if phase == 'lyrics' and unlocked_direction_ids:
            snapshot['explicit_user_direction_unlocks'] = list(unlocked_direction_ids)
        updated = _PhaseEdit(self.store, self.source_audio, phase, snapshot, document, baseline).execute(project['id'],
            {'revision_id':expected_revision_id, 'values':values})
        warning = None
        try:
            export_music_spec(self.store, project['id'])
        except OSError as error:
            warning = f'La revisión está guardada en SQLite; exportación pendiente: {error}'
        return {'record':updated, 'saved':project_phases(baseline,updated)[phase], 'changed':True, 'export_warning':warning}
