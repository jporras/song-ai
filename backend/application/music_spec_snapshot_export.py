"""Regenerable exports of a persisted revision, never a second active source."""
from application.song_specification_service import SongSpecificationService
from pathlib import Path


def export_music_spec(store, song_id):
    record = store.get_song_project(song_id)['spec']
    spec = record['json_spec']
    revision_id = record['revision']['revision_id']
    folder = store.data_dir/'projects'/song_id
    store.write_json(folder/'song_spec.json', {'song_id':song_id,'revision_id':revision_id,
        'song_spec':spec, 'user_confirmation_status':record['revision']['user_confirmation_status']})
    lines = [f"# {spec.get('title', song_id)}", '', f'Revisión: {revision_id}', '', 'Configuración guardada; aceptación del audio separada.', '']
    for group in SongSpecificationService().catalog(spec)['groups']:
        lines.extend([f"## {group['label']}", ''])
        for field in group['fields']:
            lines.append(f"- {field['label']}: {field['value'] if field['value'] is not None else 'Opcional/por revisar'}")
    (folder/'song_spec.md').write_text('\n'.join(lines),encoding='utf-8')
    if spec.get('_lyrics_document'):
        document = spec['_lyrics_document']
        aliases = {'VERSO':'verse','CORO':'chorus','INTRO':'intro','PUENTE':'bridge','OUTRO':'outro'}
        lyrics = {'song_id':song_id, 'title':spec.get('title'), 'language':spec.get('language'), 'revision_id':revision_id,
            'sections':[{'id':s['id'],'label':s['type'],'type':aliases.get(s['type'],s['type'].lower()),'lines':s['text'].splitlines()}
                        for s in document['sections']]}
        lyrics['structure'] = [s['type'] for s in lyrics['sections']]
        store.write_json(folder/'lyrics.json', lyrics)
        (folder/'lyrics.md').write_text(document['markdown'],encoding='utf-8')
    # A creative revision cannot silently reuse the old technical lyric approval.
    approved = folder/'lyrics_approved.json'
    if approved.exists():
        existing = store.read_json(approved)
        store.write_json(approved, {**existing, 'approved_by_qwen':False, 'status':'pending_review',
                                   'invalidated_by_spec_revision_id':revision_id})
    for artifact in store.get_song_project(song_id)['artifacts']:
        path = folder/Path(artifact['file_path']).name
        if path.name in {'song_spec.json','lyrics.json','lyrics.md','lyrics_approved.json'} and path.is_file():
            store.update_song_artifact_metadata(artifact['artifact_id'],
                {**artifact['metadata'],'checksum':store.file_checksum(path),'file_size':path.stat().st_size,
                 'source_spec_revision_id':revision_id,'creative_review':'pending', 'approved_by_qwen':False})
    return revision_id
