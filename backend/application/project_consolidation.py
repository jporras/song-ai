"""Consolidate an existing project without changing its lyrics or audio.

The caller supplies the researched creative resolution. This case of use does
not impersonate model execution or approve the resulting specification.
"""
from copy import deepcopy
import hashlib
import json
from pathlib import Path

from models.assets import AssetDraft, AssetType
from models.intent import MusicalIntent
from models.manifest import Manifest
from models.song_set import SongSet
from application.song_specification_service import SongSpecificationService


class ProjectConsolidation:
    VERSION = "project-consolidation-1"

    def __init__(self, store):
        self.store = store

    def execute(self, song_id, resolution):
        project = self.store.get_song_project(song_id)
        if not project or not str(project.get('user_id', '')).startswith('set:'):
            raise ValueError('Se requiere un proyecto existente vinculado a un set.')
        if project['spec']['json_spec'].get('_consolidation', {}).get('version') == self.VERSION:
            return {'song_id': song_id, 'status': 'already_consolidated'}
        set_id = project['user_id'][4:]
        song_set = self.store.get_indexed_set(set_id)
        phases = self.store.list_project_phase_data(set_id)
        lyric_data = deepcopy(phases.get('lyrics', {}).get('data', {}))
        sections = lyric_data.get('lyricSections', [])
        lyrics = lyric_data.get('lyricsEditor', {}).get('content', '')
        if not sections or not lyrics.strip():
            raise ValueError('Falta la letra editada persistida; no se inventa una sustitucion.')
        spec = deepcopy(resolution['spec'])
        if not all(spec.get(field) not in (None, '', []) for group in SongSpecificationService.CATALOG
                   for field, _, _, required, _ in group['fields'] if required):
            raise ValueError('La resolucion no completa los campos obligatorios de la ficha.')
        if spec.get('recipient_name') != resolution['recipient']:
            raise ValueError('Destinatario incoherente.')
        source = {'set': song_set, 'spec': project['spec'], 'phases': phases,
                  'assets': {key: self.store.get_asset_draft_detail(song_set[key])
                             for key in ('instrumental_id', 'melody_id', 'lyrics_id')}}
        fingerprint = hashlib.sha256(json.dumps(source, sort_keys=True, ensure_ascii=False, default=str).encode()).hexdigest()
        slug = resolution['recipient'].lower()
        ids = {}
        intent = MusicalIntent(bpm=spec['bpm'], key=spec['key'], mood=spec['emotion'],
            instruments=spec['instruments'], energy='low', vocal_style=spec['voice_style'],
            lyrics_context=spec['theme'], placeholders={'name': resolution['recipient']})
        for kind in AssetType:
            asset_id = f'{kind.value}-consolidated-{slug}-20261007'
            ids[kind.value] = asset_id
            folder = self.store.get_asset_draft_dir(kind, asset_id)
            filename = {'instrumental': 'instrumental.txt', 'melody': 'melody.txt', 'lyrics': 'lyrics.md'}[kind.value]
            content = lyrics if kind == AssetType.LYRICS else resolution[kind.value + '_description']
            self.store.save_asset_draft(AssetDraft(asset_id, kind,
                Manifest(asset_id, kind.value, 'codex-consolidation', metadata={'source_sha256': fingerprint}),
                intent, [folder/filename], {'project_id': song_id, 'origin': 'recovered_and_inferred', 'confirmation': 'pending'}))
            (folder/filename).write_text(content, encoding='utf-8')
        spec.update(source_set_id=set_id, source_of_truth='sqlite', structure=[s['type'].lower() for s in sections])
        spec['_consolidation'] = {'version': self.VERSION, 'source_sha256': fingerprint,
            'actor': 'Codex', 'model_execution': False, 'conflicts_resolved': resolution['conflicts'],
            'lyrics_sha256': hashlib.sha256(lyrics.encode()).hexdigest(),
            'audio_policy': 'preserved_original_not_acceptance_of_current_revision'}
        spec['_retained_intent'] = {
            'instrumental': deepcopy(phases.get('instrumental', {}).get('data', {})),
            'voice_details': {key: deepcopy(value) for key, value in phases.get('voice', {}).get('data', {}).get('voice', {}).items()
                              if key not in {'sectionDirection', 'sections'}},
            'execution_note': 'Detalles expresivos conservados; sliders DSP y notas MIDI no son controles ejecutables ACE-Step.'}
        spec['section_direction'] = deepcopy(resolution['section_direction'])
        spec['_provenance'] = {key: {'source': 'codex_consolidation', 'origin': 'AI_INFERRED',
            'confirmation': 'pending', 'source_sha256': fingerprint,
            'note': resolution.get('field_notes', {}).get(key, 'Reconstruido desde fuentes persistidas; no acredita una decision USER nueva.')}
            for key in spec if not key.startswith('_')}
        for group in SongSpecificationService.CATALOG:
            for field, _, _, _, _ in group['fields']:
                if field not in spec:
                    spec.setdefault('_field_disposition', {})[field] = 'optional_or_delegated_pending_review'
                    spec['_provenance'][field] = {'source': 'explicit_delegation_proposal', 'confirmation': 'pending',
                        'note': 'Opcional/delegado al perfil; sin prometer una capacidad desconectada.'}
        self.store.save_song_set(SongSet(set_id, resolution['recipient'], spec['creative_brief'], song_set['created_at'],
            ids['instrumental'], ids['melody'], ids['lyrics'],
            {**song_set.get('compatibility_data', {}), 'consolidation_version': self.VERSION}))
        phase_updates = deepcopy(phases)
        for phase, saved in phase_updates.items():
            data = saved['data']
            if phase == 'intent':
                data.setdefault('intent', {}).update(recipient=resolution['recipient'], description=spec['creative_brief'],
                    instruments=spec['instruments'], bpm=spec['bpm'], key=spec['key'])
            elif phase == 'lyrics':
                data = lyric_data
                data.setdefault('lyrics', {}).update(theme=spec['theme'], structure=', '.join(spec['structure']))
                data['lyrics'].setdefault('placeholders', {})['name'] = resolution['recipient']
                data['lyricsEditor'].update(selectedAssetId=ids['lyrics'], path=str(self.store.get_asset_draft_dir(AssetType.LYRICS, ids['lyrics'])/'lyrics.md'))
            elif phase == 'voice':
                data.setdefault('voice', {})['sectionDirection'] = deepcopy(resolution['section_direction'])
            elif phase == 'music-plan':
                data.setdefault('musicPlan', {}).update(bpm=spec['bpm'], key=spec['key'], timeSignature=spec['time_signature'])
                data['musicPlan']['sections'] = deepcopy(resolution['plan_sections'])
            self.store.save_project_phase_data(set_id, phase, data, saved.get('status', 'saved'),
                change_source='CODEX_CONSOLIDATION', validation_status='review_pending')
        record = self.store.upsert_song_spec(song_id, spec, True, [], schema_version='1.1',
            technical_review_mode='codex_consolidation_not_qwen_execution', user_confirmation_status='pending',
            expected_revision_id=project['spec'].get('revision', {}).get('revision_id'))
        folder = self.store.data_dir/'projects'/song_id
        normalized = {'INTRO': 'intro', 'VERSO': 'verse', 'CORO': 'chorus', 'PUENTE': 'bridge', 'OUTRO': 'outro'}
        lyric_document = {'song_id': song_id, 'title': resolution['recipient'], 'language': spec['language'],
            'structure': [normalized.get(s['type'], s['type'].lower()) for s in sections],
            'sections': [{'id': s['id'], 'type': normalized.get(s['type'], s['type'].lower()),
                          'label': s['type'], 'lines': s['text'].splitlines()} for s in sections],
            'source': 'sqlite_saved_lyrics_consolidation', 'revision_id': record['revision']['revision_id']}
        self.store.write_json(folder/'lyrics.json', lyric_document)
        (folder/'lyrics.md').write_text(lyrics, encoding='utf-8')
        self.store.write_json(folder/'lyrics_approved.json', {'song_id': song_id, 'approved_by_qwen': False,
            'status': 'pending_review', 'lyrics': lyric_document, 'source': 'codex_consolidation_not_qwen_execution'})
        self.store.write_json(folder/'song_spec.json', {'song_id': song_id, 'revision_id': record['revision']['revision_id'],
            'song_spec': spec, 'user_confirmation_status': 'pending', 'technical_review_mode': 'codex_consolidation'})
        markdown = [f"# {resolution['recipient']}", '', 'Ficha consolidada. Revision creativa pendiente.', '']
        for group in SongSpecificationService.CATALOG:
            markdown.extend([f"## {group['label']}", ''])
            for field, label, *_ in group['fields']:
                markdown.append(f"- {label}: {spec.get(field) if spec.get(field) is not None else 'Opcional/delegado'}")
        (folder/'song_spec.md').write_text('\n'.join(markdown), encoding='utf-8')
        for artifact in project.get('artifacts', []):
            path = folder/Path(artifact['file_path']).name
            if path.name in {'song_spec.json', 'lyrics.json', 'lyrics.md', 'lyrics_approved.json'}:
                self.store.song_workflow_repository.update_artifact_metadata(artifact['artifact_id'],
                    {**artifact['metadata'], 'checksum': self.store.file_checksum(path), 'file_size': path.stat().st_size,
                     'source': 'codex_consolidation', 'creative_review': 'pending', 'approved_by_qwen': False})
        # Keep the entire source context inside this project's persisted task.
        task_id = f'consolidation-{song_id}'
        self.store.create_task(task_id, 'project_consolidation', 'system', {'song_id': song_id, 'source_context': source}, 'Consolidacion de proyecto existente.')
        self.store.update_task(task_id, 'completed', 100, 'Migracion terminada; revision creativa pendiente.',
            {'revision_id': record['revision']['revision_id'], 'resolution': resolution, 'asset_ids': ids})
        self.store.create_song_event(song_id, 'SONG_SPEC_COLLECTION', 'waiting_user_input', 100,
            'Proyecto consolidado: letra preservada, assets independientes y ficha revisable. Audios originales conservados.',
            'Codex', {'event_type': 'PROJECT_CONSOLIDATED', 'revision_id': record['revision']['revision_id'], 'source_sha256': fingerprint})
        self.store.update_song_project_phase(song_id, 'SONG_SPEC_COLLECTION', 'waiting_user_input')
        return {'song_id': song_id, 'status': 'consolidated', 'revision_id': record['revision']['revision_id'], 'asset_ids': ids}
