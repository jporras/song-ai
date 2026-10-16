import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'backend'))
from core.storage import StorageManager
from application.local_project_export_service import LocalProjectExportService


class LocalExportsTest(unittest.TestCase):
    def test_ace_export_requires_current_plan_and_lyrics_snapshot_instead_of_legacy_midi(self):
        service = LocalProjectExportService.__new__(LocalProjectExportService)
        artifacts = [{'type': 'final_song_wav', 'metadata': {
            'generation_mode': 'local_full_song_command', 'ace_plan_id': 'plan-1'}}]
        self.assertEqual(service._required_artifacts(artifacts), {
            'song_spec', 'ace_plan_json', 'lyrics_markdown',
            'final_song_wav', 'final_song_mp3', 'final_song_flac'})

    def test_export_does_not_include_artifacts_owned_by_another_project(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as folder:
            store = StorageManager(Path(folder))
            song = store.create_song_project('Idea')['id']
            other = store.create_song_project('Otra')['id']
            for artifact_id, owner in (('owned', song), ('foreign', other)):
                path = Path(folder) / 'projects' / owner / f'{artifact_id}.md'
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(artifact_id, encoding='utf-8')
                store.create_song_artifact(artifact_id=artifact_id, song_id=song,
                    phase='EXPORT', artifact_type=artifact_id, file_path=str(path), metadata={})
            project = store.get_song_project(song)
            artifacts = LocalProjectExportService(store)._owned_export_artifacts(song, project)
            self.assertEqual([item['type'] for item in artifacts], ['owned'])

    def test_corruption_cannot_become_new_checksum_on_second_verification(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as folder:
            store = StorageManager(Path(folder))
            song = store.create_song_project('Idea')['id']
            path = Path(folder) / 'projects' / song / 'lyrics.md'
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text('Original', encoding='utf-8')
            artifact = store.create_song_artifact(artifact_id='lyrics', song_id=song,
                phase='LYRICS_GENERATION', artifact_type='lyrics_markdown', file_path=str(path), metadata={})
            expected = artifact['metadata']['checksum']
            path.write_text('Modificado', encoding='utf-8')
            for _ in range(2):
                result = store.verify_song_artifact(song, 'lyrics_markdown')
                self.assertEqual(result['artifact_status'], 'CORRUPTED')
                self.assertEqual(result['metadata']['checksum'], expected)
                self.assertNotEqual(result['metadata']['observed_checksum'], expected)

    def test_export_rejects_tampered_artifact_before_creating_zip(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as folder:
            store = StorageManager(Path(folder))
            song = store.create_song_project('Idea')['id']
            project = Path(folder) / 'projects' / song
            project.mkdir(parents=True, exist_ok=True)
            required = ('song_spec', 'lyrics_json', 'lyrics_approved_json', 'music_plan_json',
                        'midi', 'final_song_wav', 'final_song_mp3', 'final_song_flac')
            for kind in required:
                path = project / (kind + '.bin')
                path.write_bytes(kind.encode())
                store.create_song_artifact(artifact_id=kind, song_id=song, phase='EXPORT',
                    artifact_type=kind, file_path=str(path), metadata={
                        'generation_mode': 'local_full_song_command' if kind == 'final_song_wav' else ''})
            (project / 'final_song_mp3.bin').write_bytes(b'changed')
            with patch('application.local_project_export_service.FinalProductionGate.require_for_project'):
                with self.assertRaisesRegex(ValueError, 'checksum.*final_song_mp3'):
                    LocalProjectExportService(store).export(song)
            self.assertFalse((project / 'project_export.zip').exists())

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
