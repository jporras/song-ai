"""Deterministic review evidence, never a model or creative approval."""
import hashlib
from application.local_lyrics_access import LocalLyricsAccess
from application.lyrics_review_service import LyricsReviewService
from application.music_spec_revision_service import MusicSpecRevisionService


class LocalLyricsReview:
    def __init__(self, storage):
        self.storage = storage

    def execute(self, song_id):
        project = self.storage.get_song_project(song_id)
        if project is None or not project.get('spec'):
            raise ValueError('Prepara la definición del proyecto antes de revisar la letra.')
        record = project['spec']
        lyrics = LocalLyricsAccess(self.storage).get(song_id)
        if lyrics.get('active_music_spec_document') and lyrics.get('revision_id') != record.get('revision', {}).get('revision_id'):
            raise ValueError('La definición cambió durante la revisión. Recarga y vuelve a revisar la letra.')
        rules = LyricsReviewService(self.storage)
        evidence = rules.evaluate(record['json_spec'], lyrics['lyrics'])
        issues = evidence['issues']
        report = {'review_kind':'deterministic_lyrics_rules',
            'source_revision_id':record.get('revision', {}).get('revision_id'),
            'lyrics_sha256':hashlib.sha256(lyrics['markdown'].encode()).hexdigest(),
            'source':lyrics['source'], 'deterministic_valid':not issues,
            **evidence,
            'model_review_executed':False, 'approved_by_qwen':False,
            'user_approval':False, 'audio_quality_verified':False}
        self.storage.create_song_event(song_id=song_id,phase='LYRICS_TECHNICAL_REVIEW',
            status='completed',progress=100,active_model='deterministic-lyrics-review',
            message='Letra revisada mediante reglas; revisión del modelo y aprobación creativa separadas.',payload=report)
        return {'project':project,'review':report,
                'progress':MusicSpecRevisionService(self.storage).progress_for(project)}
