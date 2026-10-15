"""Read active lyrics from SQLite; retain explicit legacy snapshot compatibility."""
from copy import deepcopy
from application.lyrics_service import LyricsService
from application.music_spec_revision_service import MusicSpecRevisionService


class LocalLyricsAccess:
    def __init__(self, storage):
        self.storage = storage
        self.snapshots = LyricsService(storage)

    def get(self, song_id):
        project = self.storage.get_song_project(song_id)
        if project is None:
            raise ValueError('Proyecto no encontrado.')
        record = project.get('spec') or {}
        spec = record.get('json_spec', {})
        document = spec.get('_lyrics_document')
        if not document:
            return {**self.snapshots.get(song_id), 'source': 'legacy_snapshot',
                    'active_music_spec_document': False}
        markdown = document.get('markdown', '')
        if not isinstance(markdown, str) or not markdown.strip():
            raise ValueError('La letra activa está incompleta. Revisa la fase de letra del proyecto.')
        payload = self.snapshots.from_markdown(song_id, str(spec.get('title', project['title'])), markdown)
        payload['language'] = spec.get('language', '')
        json_path, md_path = self.snapshots.paths(song_id)
        return {'song_id':song_id, 'markdown':markdown, 'lyrics':payload,
                'lyrics_json_path':str(json_path), 'lyrics_md_path':str(md_path),
                'document':deepcopy(document), 'source':'sqlite_music_spec',
                'active_music_spec_document':True,
                'revision_id':record.get('revision', {}).get('revision_id')}

    def update(self, song_id, request):
        active = self.get(song_id)
        if active['active_music_spec_document']:
            raise ValueError('Edita la letra desde la fase de letra del proyecto; esta ruta histórica no modifica la revisión activa.')
        result = self.snapshots.update_markdown(song_id, str(request.get('content', '')))
        result['progress'] = MusicSpecRevisionService(self.storage).progress_for(result['project'])
        return result
