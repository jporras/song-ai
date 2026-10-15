import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'backend'))
from core.storage import StorageManager
from application.local_project_export_service import LocalProjectExportService


class LocalExportsTest(unittest.TestCase):
    def test_registered_project_file_downloads_and_corruption_blocks(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as folder:
            store=StorageManager(Path(folder))
            song=store.create_song_project('Idea')['id']
            path=Path(folder)/'projects'/song/'lyrics.md'
            path.parent.mkdir(parents=True,exist_ok=True)
            path.write_text('Texto',encoding='utf-8')
            store.create_song_artifact(artifact_id='lyrics',song_id=song,phase='LYRICS_GENERATION',
                artifact_type='lyrics_markdown',file_path=str(path),metadata={})
            exports=LocalProjectExportService(store)
            returned, filename, media=exports.download_file(song,'lyrics_markdown')
            self.assertEqual(returned,path.resolve())
            self.assertEqual(media,'text/markdown')
            path.write_text('Texto cambiado',encoding='utf-8')
            with self.assertRaises(ValueError): exports.download_file(song,'lyrics_markdown')

    def test_sibling_directory_is_not_a_project_download(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as folder:
            store=StorageManager(Path(folder))
            song=store.create_song_project('Idea')['id']
            sibling=Path(folder)/'projects'/(song+'-other')
            sibling.mkdir(parents=True)
            path=sibling/'lyrics.md'
            path.write_text('Texto',encoding='utf-8')
            store.create_song_artifact(artifact_id='outside',song_id=song,phase='LYRICS_GENERATION',
                artifact_type='lyrics_markdown',file_path=str(path),metadata={})
            with self.assertRaisesRegex(ValueError,'proyecto activo'):
                LocalProjectExportService(store).download_file(song,'lyrics_markdown')
