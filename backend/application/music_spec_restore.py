"""Recover a persisted snapshot as a new, unapproved revision."""
from copy import deepcopy
from typing import Protocol


class RevisionStore(Protocol):
    def get_song_project(self, song_id): ...
    def list_song_spec_revisions(self, song_id): ...
    def upsert_song_spec(self, **kwargs): ...


class RestoreMusicSpec:
    def __init__(self, store: RevisionStore):
        self.store = store

    def execute(self, song_id: str, request: dict) -> dict:
        project = self.store.get_song_project(song_id)
        if not project or not project.get('spec'):
            raise ValueError('El proyecto no tiene una definición para restaurar.')
        current = project['spec']
        expected = request.get('revision_id')
        if not expected or expected != current.get('revision', {}).get('revision_id'):
            raise ValueError('La definición cambió. Recarga antes de restaurar.')
        source = next((r for r in self.store.list_song_spec_revisions(song_id)
                       if r['revision_id'] == request.get('source_revision_id')), None)
        if source is None:
            raise ValueError('Selecciona una revisión del proyecto activo.')
        spec = deepcopy(source['json_spec'])
        def has_protection(value):
            if isinstance(value, dict):
                return value.get('locked') is True or any(has_protection(v) for v in value.values())
            return isinstance(value, list) and any(has_protection(v) for v in value)
        for field in ('_lyrics_document', '_editor_phases'):
            value = current['json_spec'].get(field)
            if has_protection(value) and value != spec.get(field):
                raise ValueError('Desbloquea las secciones protegidas antes de restaurar.')
        for field, provenance in current['json_spec'].get('_provenance', {}).items():
            if provenance.get('locked') and current['json_spec'].get(field) != spec.get(field):
                raise ValueError('Desbloquea la decisión protegida antes de restaurar: ' + field)
            if provenance.get('locked'):
                spec.setdefault('_provenance', {})[field] = deepcopy(provenance)
        spec['_restoration'] = {'source_revision_id': source['revision_id'],
                                'source_deterministic_valid': source.get('deterministic_valid') is True,
                                'replaced_revision_id': expected, 'actor': 'user',
                                'transformation': 'persisted_snapshot_restore_v1'}
        return self.store.upsert_song_spec(song_id=song_id, json_spec=spec,
            approved_by_qwen=False, missing_fields=source.get('missing_fields', []),
            schema_version=source.get('schema_version', '1.1'),
            technical_review_mode='restored_snapshot_requires_review',
            user_confirmation_status='pending', expected_revision_id=expected)
