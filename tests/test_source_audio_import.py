import hashlib
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'backend'))
from application.source_audio_import import ImportSourceAudio
from adapters.sample_audio_evidence import inspect_sample_wav
from adapters.ace_step_source_audio import AceStepSourceAudio
from core.storage import StorageManager
from tests.test_sample_audio_evidence import write_audio


class SourceImportTest(unittest.TestCase):
    def test_original_bytes_project_ownership_and_spec_are_preserved(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as folder:
            store=StorageManager(Path(folder))
            project=store.create_song_project('Idea')
            record=store.upsert_song_spec(project['id'],{'emotion':'alegre'},True,[])
            fixture=Path(folder)/'original.wav'; write_audio(fixture,100)
            content=fixture.read_bytes()
            artifact=ImportSourceAudio(store,inspect_sample_wav).execute(project['id'],'../../original.wav',content,True)
            self.assertEqual(Path(artifact['file_path']).read_bytes(),content)
            current=store.get_song_project(project['id'])
            self.assertEqual(current['spec'],record)
            evidence=AceStepSourceAudio(store.data_dir).inspect(current,artifact['artifact_id'],artifact['file_path'])
            self.assertEqual(evidence['sha256'],hashlib.sha256(content).hexdigest())
            other=store.create_song_project('Otra')
            with self.assertRaises(ValueError):
                AceStepSourceAudio(store.data_dir).inspect(other,artifact['artifact_id'],artifact['file_path'])

    def test_invalid_and_unauthorized_uploads_do_not_register_artifacts(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as folder:
            store=StorageManager(Path(folder)); project=store.create_song_project('Idea')
            importer=ImportSourceAudio(store,inspect_sample_wav)
            for name,content,authorized in [('bad.wav',b'invalid',True),('audio.mp3',b'bytes',True),('audio.wav',b'bytes',False)]:
                with self.subTest(name=name,authorized=authorized),self.assertRaises(ValueError):
                    importer.execute(project['id'],name,content,authorized)
            self.assertFalse(store.get_song_project(project['id'])['artifacts'])
            self.assertFalse(list((store.data_dir/'projects'/project['id']).rglob('*.wav')))
