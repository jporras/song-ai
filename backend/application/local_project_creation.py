"""Explicit preparation from a valid set, never automatic model/user approval."""
from copy import deepcopy
import hashlib
from application.set_music_spec_projection import SetMusicSpecProjection
from application.local_project_queries import LocalProjectQueries
from application.music_spec_snapshot_export import export_music_spec


class CreateLocalProject:
    def __init__(self, storage):
        self.storage = storage

    def execute(self, request):
        title = str(request.get('title') or request.get('project_name') or 'Nueva canción')
        source_id = str(request.get('source_set_id') or '').strip()
        spec = None
        if source_id:
            linked = [p for p in self.storage.list_song_projects() if p.get('user_id') == 'set:'+source_id]
            if len(linked) > 1:
                raise ValueError('Hay varias fichas vinculadas; resuelve el proyecto activo antes de crear.')
            if linked:
                return LocalProjectQueries(self.storage).get(linked[0]['id'])
            song_set = self.storage.get_indexed_set(source_id)
            if song_set is None:
                raise ValueError('Selecciona un set válido para preparar el proyecto.')
            projection = SetMusicSpecProjection(self.storage)
            assets = projection._assets_for_set(song_set)
            if any(not assets.get(kind) for kind in ('instrumental','melody','lyrics')):
                raise ValueError('El set necesita instrumental, melodía vocal y letra disponibles.')
            phases = self.storage.list_project_phase_data(source_id)
            spec = projection._spec_from_set_data(song_set, phases, assets, request)
            spec['creative_brief'] = spec.get('description', '')
            spec['_preparation'] = {'source':'persisted_set', 'requires_deterministic_review':True}
            spec['_editor_phases'] = deepcopy(phases)
            spec['_retained_intent'] = {kind:deepcopy(asset.get('intent', {})) for kind,asset in assets.items()}
            spec['_provenance'] = {key:{'source':'persisted_set_projection', 'source_set_id':source_id,
                'confirmation':'pending', 'transformations':['set_phase_projection_v1']} for key in spec if not key.startswith('_')}
            markdown = projection._lyrics_markdown_from_set(song_set, phases, assets)
            sections = deepcopy(projection._phase_payload(phases, 'lyrics').get('lyricSections', []))
            used_ids = {s.get('id') for s in sections if s.get('id')}
            assigned = []
            for index, section in enumerate(sections):
                if not section.get('id'):
                    section_id = f'legacy-section-{index + 1}'
                    while section_id in used_ids:
                        section_id += '-import'
                    section['id'] = section_id
                    used_ids.add(section_id)
                    assigned.append({'section_index': index, 'assigned_id': section_id})
            if assigned:
                spec['_preparation']['section_id_migration'] = assigned
                phase_values = spec['_editor_phases'].setdefault('lyrics', {}).setdefault('data', {})
                if isinstance(phase_values.get('data'), dict):
                    phase_values = phase_values['data']
                phase_values['lyricSections'] = deepcopy(sections)
            spec['_lyrics_document'] = {'markdown':markdown, 'sections':sections,
                'sha256':hashlib.sha256(markdown.encode()).hexdigest()}
        project = self.storage.create_song_project(title, 'set:'+source_id if source_id else str(request.get('user_id') or 'local-user'),
                                                  reuse_linked=bool(source_id))
        song_id = project['id']
        if project.get('_creation_reused'):
            return LocalProjectQueries(self.storage).get(song_id)
        if spec is not None:
            from application.music_spec_edit import EditMusicSpec
            missing = sorted(field for field in EditMusicSpec.REQUIRED_FIELDS if spec.get(field) in (None,'',[]))
            self.storage.upsert_song_spec(song_id,spec,False,missing,technical_review_mode='set_preparation_requires_review',
                user_confirmation_status='pending',deterministic_valid=False)
            export_music_spec(self.storage,song_id)
            self.storage.create_song_event(song_id=song_id,phase='SONG_SPEC_COLLECTION',status='pending',progress=0,
                message='Proyecto preparado desde el set; revisa la definición antes de confirmar.',active_model='system',
                payload={'source_set_id':source_id,'model_review_executed':False})
        return LocalProjectQueries(self.storage).get(song_id)
