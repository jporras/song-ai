import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'backend'))
from core.storage import StorageManager
from application.local_lyrics_access import LocalLyricsAccess


class LocalLyricsTest(unittest.TestCase):
    def test_legacy_read_and_edit_remain_identified_as_snapshot(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as folder:
            store=StorageManager(Path(folder))
            song=store.create_song_project('Idea')['id']
            path=Path(folder)/'projects'/song/'lyrics.md'
            path.parent.mkdir(parents=True,exist_ok=True)
            path.write_text('## Verse 1\nTexto antiguo\n',encoding='utf-8')
            access=LocalLyricsAccess(store)
            self.assertEqual(access.get(song)['source'],'legacy_snapshot')
            access.update(song,{'content':'## Verse 1\nTexto editado\n'})
            self.assertIn('Texto editado',access.get(song)['markdown'])
            self.assertFalse(access.get(song)['active_music_spec_document'])

    def test_active_document_wins_over_derived_file_and_old_edit_cannot_overwrite_it(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as folder:
            store=StorageManager(Path(folder))
            song=store.create_song_project('Alma')['id']
            saved=store.upsert_song_spec(song,{'language':'es','_lyrics_document':{
                'markdown':'## Verse 1\nAlma duerme\n','sections':[]}},False,[])
            path=Path(folder)/'projects'/song/'lyrics.md'
            path.parent.mkdir(parents=True,exist_ok=True)
            path.write_text('Otra canción',encoding='utf-8')
            access=LocalLyricsAccess(store)
            result=access.get(song)
            self.assertEqual(result['source'],'sqlite_music_spec')
            self.assertIn('Alma duerme',result['markdown'])
            self.assertEqual(result['lyrics']['language'],'es')
            with self.assertRaisesRegex(ValueError,'fase de letra'):
                access.update(song,{'content':'Cambio ajeno'})
            self.assertEqual(store.get_song_project(song)['spec']['revision']['revision_id'],saved['revision']['revision_id'])
