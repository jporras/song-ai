import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'backend'))
from core.storage import StorageManager
from application.song_service import SongService


class LocalQueriesTest(unittest.TestCase):
    def test_queries_keep_revision_and_events_intact_without_historical_service(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as folder:
            store=StorageManager(Path(folder))
            songs=[store.create_song_project(name)['id'] for name in ('Alma','Isabella')]
            revisions=[store.upsert_song_spec(song,{'title':name},False,[]) for song,name in zip(songs,('Alma','Isabella'))]
            service=SongService.__new__(SongService)
            service.storage=store
            projects=service.list_professional_projects()['projects']
            self.assertEqual({p['id'] for p in projects},set(songs))
            for song,revision in zip(songs,revisions):
                before=store.list_song_project_events(song)
                self.assertEqual(service.get_professional_project(song)['project']['spec']['revision']['revision_id'],revision['revision']['revision_id'])
                self.assertEqual(service.list_professional_project_events(song)['events'],before)
                self.assertEqual(len(store.list_song_spec_revisions(song)),1)
                self.assertEqual(store.list_song_project_events(song),before)
            with self.assertRaises(ValueError): service.get_professional_project('missing')
