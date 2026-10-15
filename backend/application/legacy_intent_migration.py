"""Infer a reviewable migration from persisted phase inputs, never frontend defaults."""
from copy import deepcopy
import hashlib
import json
from uuid import uuid4
from application.music_spec_edit import EditMusicSpec


MAPPINGS = {
    'intent': ('intent', {'description': 'creative_brief', 'songType': 'song_type',
        'language': 'language', 'recipient': 'recipient_name', 'bpm': 'bpm', 'key': 'key',
        'vocalType': 'voice_style', 'instruments': 'instruments'}),
    'music-plan': ('musicPlan', {'bpm': 'bpm', 'key': 'key', 'timeSignature': 'time_signature',
        'dynamicArc': 'dynamic_arc'}),
    'lyrics': ('lyrics', {'language': 'language', 'tone': 'lyrical_tone', 'theme': 'theme',
        'structure': 'structure'}),
    'voice': ('voice', {'mainVoice': 'voice_style', 'emotion': 'vocal_expression',
        'performance': 'vocal_expression', 'pronunciation': 'pronunciation'}),
}


class LegacyIntentMigration:
    def __init__(self, store):
        self.store = store

    def preview(self, song_id):
        project = self.store.get_song_project(song_id)
        if not project or not project.get('spec'):
            raise ValueError('Prepara una ficha antes de migrar información.')
        user_id = str(project.get('user_id', ''))
        if not user_id.startswith('set:'):
            raise ValueError('El proyecto no está vinculado a un set histórico.')
        set_id = user_id[4:]
        song_set = self.store.get_indexed_set(set_id)
        if not song_set:
            raise ValueError('El set histórico no existe.')
        phases = self.store.list_project_phase_data(set_id)
        record = project['spec']
        spec = record['json_spec']
        assets = {}
        for field in ('instrumental_id', 'melody_id', 'lyrics_id'):
            if song_set.get(field):
                try:
                    assets[field] = self.store.get_asset_draft_detail(song_set[field])
                except ValueError:
                    assets[field] = {'asset_id': song_set[field], 'status': 'source_unavailable'}
        context = {'set': song_set, 'phase_data': phases, 'selected_assets': assets}
        fingerprint = hashlib.sha256(json.dumps(context, sort_keys=True, ensure_ascii=False,
                                                default=str).encode()).hexdigest()
        candidates = {}
        for phase, (section, mapping) in MAPPINGS.items():
            saved = phases.get(phase, {})
            values = saved.get('data', {}).get(section, {})
            for legacy, field in mapping.items():
                value = values.get(legacy)
                if value in (None, '', []):
                    continue
                if field == 'instruments':
                    if not isinstance(value, list) or any(not isinstance(v, str) for v in value):
                        continue
                elif field not in {'bpm', 'duration_seconds'} and not isinstance(value, str):
                    continue
                try:
                    EditMusicSpec(self.store).validate_edits({field: value})
                except ValueError:
                    # Keep unsupported/invalid intent in the complete source context.
                    continue
                candidates.setdefault(field, []).append({'value': deepcopy(value),
                    'phase': phase, 'path': f'data/{section}/{legacy}',
                    'updated_at': saved.get('updated_at'),
                    'origin': 'historical_saved_input_origin_unverified'})
        additions, conflicts = {}, []
        for field, evidence in candidates.items():
            distinct = []
            for item in evidence:
                if item['value'] not in distinct:
                    distinct.append(item['value'])
            current = spec.get(field)
            if spec.get('_provenance', {}).get(field, {}).get('locked') is True:
                conflicts.append({'field': field, 'current': deepcopy(current),
                                  'candidates': evidence, 'resolution': 'locked_preserve_current'})
                continue
            if current not in (None, '', []):
                if any(value != current for value in distinct):
                    conflicts.append({'field': field, 'current': deepcopy(current),
                                      'candidates': evidence, 'resolution': 'preserve_current'})
            elif len(distinct) == 1:
                additions[field] = {'value': distinct[0], 'sources': evidence}
            else:
                conflicts.append({'field': field, 'current': current, 'candidates': evidence,
                                  'resolution': 'needs_review'})
        return {'version': 'legacy-intent-mapping-1.0', 'song_id': song_id, 'set_id': set_id,
                'revision_id': record['revision']['revision_id'], 'source_sha256': fingerprint,
                'mode': 'deterministic_inference_not_model_run', 'confirmation': 'pending',
                'additions': additions, 'conflicts': conflicts, 'source_context': deepcopy(context),
                'warning': 'Un dato guardado puede proceder de un ejemplo o default; no acredita un deseo USER.'}

    def apply(self, song_id, request):
        proposal = self.preview(song_id)
        if request.get('revision_id') != proposal['revision_id'] or request.get('source_sha256') != proposal['source_sha256']:
            raise ValueError('Cambió la ficha o la información histórica; prepara otra propuesta.')
        fields = request.get('fields')
        if not isinstance(fields, list) or not fields or any(not isinstance(f, str) or f not in proposal['additions'] for f in fields):
            raise ValueError('Selecciona solo datos faltantes de la propuesta; conflictos no se sobrescriben.')
        record = self.store.get_song_project(song_id)['spec']
        spec = deepcopy(record['json_spec'])
        provenance = spec.setdefault('_provenance', {})
        for field in fields:
            if spec.get(field) not in (None, '', []):
                raise ValueError('No se sobrescriben decisiones vigentes.')
            item = proposal['additions'][field]
            spec[field] = deepcopy(item['value'])
            provenance[field] = {'source': 'historical_inference', 'origin': 'AI_INFERRED',
                'inference_method': 'deterministic_mapping', 'sources': item['sources'],
                'source_sha256': proposal['source_sha256'], 'confirmation': 'pending',
                'note': 'Migración aplicada explícitamente; la revisión creativa sigue pendiente.'}
        result = self.store.upsert_song_spec(song_id=song_id, json_spec=spec,
            approved_by_qwen=False,
            missing_fields=[f for f in record.get('missing_fields', []) if f not in fields],
            schema_version=record.get('schema_version', '1.1'),
            technical_review_mode='historical_inference_pending_review',
            user_confirmation_status='pending', expected_revision_id=proposal['revision_id'])
        task_id = 'legacy-migration-' + uuid4().hex
        self.store.create_task(task_id, 'legacy_intent_migration', 'system',
                               {'song_id': song_id, 'revision_id': proposal['revision_id']}, 'Migración histórica aplicada.')
        self.store.update_task(task_id, 'completed', 100, 'Revisión creativa pendiente.',
                               {'proposal': proposal, 'applied_fields': fields,
                                'new_revision_id': result['revision']['revision_id']})
        return result
