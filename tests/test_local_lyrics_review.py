import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'backend'))
from core.storage import StorageManager
from application.local_lyrics_review import LocalLyricsReview


class LocalReviewTest(unittest.TestCase):
    def test_rule_review_is_traceable_and_does_not_approve_or_change_revision(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as folder:
            store=StorageManager(Path(folder))
            song=store.create_song_project('Alma')['id']
            saved=store.upsert_song_spec(song,{'duration_seconds':30,'structure':['verse_1'],
                '_lyrics_document':{'markdown':'## Verse 1\nAlma duerme\n','sections':[]}},False,[])
            before=store.get_song_project(song)
            report=LocalLyricsReview(store).execute(song)['review']
            self.assertFalse(report['approved_by_qwen'])
            self.assertFalse(report['model_review_executed'])
            self.assertEqual(report['source_revision_id'],saved['revision']['revision_id'])
            self.assertEqual(len(report['lyrics_sha256']),64)
            after=store.get_song_project(song)
            self.assertEqual(before['spec'],after['spec'])
            self.assertEqual(before['current_phase'],after['current_phase'])
            self.assertFalse((Path(folder)/'projects'/song/'lyrics_approved.json').exists())
            self.assertEqual(store.list_song_project_events(song)[-1]['payload']['lyrics_sha256'],report['lyrics_sha256'])
