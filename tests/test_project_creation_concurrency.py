import sys
import tempfile
import unittest
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'backend'))
from core.storage import StorageManager


class ConcurrentCreationTest(unittest.TestCase):
    def test_two_connections_create_one_linked_project_and_one_creation_event(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as folder:
            stores=[StorageManager(Path(folder)),StorageManager(Path(folder))]
            barrier=Barrier(2)
            def create(index):
                barrier.wait(timeout=5)
                return stores[index].create_song_project('Alma '+str(index),'set:concurrent',reuse_linked=True)
            with ThreadPoolExecutor(max_workers=2) as executor:
                results=list(executor.map(create,(0,1)))
            self.assertEqual(results[0]['id'],results[1]['id'])
            self.assertEqual(sum(bool(r.get('_creation_reused')) for r in results),1)
            self.assertEqual(len(stores[0].list_song_projects()),1)
            self.assertEqual(len(stores[0].list_song_project_events(results[0]['id'])),1)
            saved=stores[0].upsert_song_spec(results[0]['id'],{'bpm':72},False,[],deterministic_valid=True)
            reused=stores[1].create_song_project('No sobrescribir','set:concurrent',reuse_linked=True)
            self.assertEqual(reused['spec']['revision']['revision_id'],saved['revision']['revision_id'])

    def test_ambiguous_or_unlinked_request_cannot_write(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as folder:
            store=StorageManager(Path(folder))
            for title in ('A','B'): store.create_song_project(title,'set:ambiguous')
            for user_id in ('set:ambiguous','local-user','set:'):
                with self.subTest(user_id=user_id), self.assertRaises(ValueError):
                    store.create_song_project('C',user_id,reuse_linked=True)
            self.assertEqual(len(store.list_song_projects()),2)
