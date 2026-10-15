import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'backend'))
from core.storage import StorageManager
from application.local_production_artifact_queries import LocalProductionArtifactQueries
from application.song_service import SongService


class ArtifactQueryTests(unittest.TestCase):
    def test_seven_local_reads_preserve_contract_and_active_sqlite_without_historical_service(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as folder:
            store = StorageManager(Path(folder))
            song = store.create_song_project('Alma')['id']
            store.upsert_song_spec(song, {'title':'Alma'}, False, ['bpm'])
            before = store.get_song_project(song)
            directory = store.data_dir/'projects'/song
            directory.mkdir(parents=True, exist_ok=True)
            # Retrieval fixtures are bytes, not quality evidence or generated audio.
            for name in ('instrumental.wav','vocals.wav','vocals_converted.wav','mix.wav',
                         'final_song.wav','final_song.mp3','final_song.flac','song_base.mid'):
                (directory/name).write_bytes(b'fixture')
            store.write_json(directory/'music_plan.json', {'bpm':72})
            store.write_json(directory/'midi_metadata.json', {'markers':['verse']})
            service = SongService.__new__(SongService)
            service.storage = store
            self.assertFalse(hasattr(service, 'professional_songs'))
            for method,key in [('get_professional_instrumental','instrumental'),('get_professional_vocals','vocals'),
                               ('get_professional_converted_voice','vocals_converted'),('get_professional_mix','mix')]:
                result = getattr(service,method)(song)
                self.assertEqual(set(result), {'song_id',key,'size_bytes'})
                self.assertEqual(result['size_bytes'],7)
                self.assertTrue(Path(result[key]).is_file())
            self.assertEqual(service.get_professional_music_plan(song)['music_plan'], {'bpm':72})
            midi = service.get_professional_midi(song)
            self.assertEqual(set(midi), {'song_id','midi','metadata'})
            self.assertEqual(midi['metadata'], {'markers':['verse']})
            master = service.get_professional_master(song)
            self.assertEqual(set(master), {'song_id','final_wav','final_mp3','final_flac',
                                          'wav_size_bytes','mp3_size_bytes','flac_size_bytes'})
            self.assertEqual(store.get_song_project(song),before)

    def test_missing_project_or_required_file_and_escaping_path_are_rejected(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as folder:
            store = StorageManager(Path(folder))
            song = store.create_song_project('Alma')['id']
            reader = LocalProductionArtifactQueries(store)
            with self.assertRaisesRegex(ValueError,'Proyecto no encontrado'):
                reader.get('unknown','mix')
            with self.assertRaisesRegex(ValueError,'song_base.mid'):
                reader.get(song,'midi')
            directory = store.data_dir/'projects'/song
            directory.mkdir(parents=True,exist_ok=True)
            (directory/'song_base.mid').write_bytes(b'fixture')
            with self.assertRaisesRegex(ValueError,'midi_metadata.json'):
                reader.get(song,'midi')
            (directory/'mix.wav').mkdir()
            with self.assertRaisesRegex(ValueError,'mix.wav'):
                reader.get(song,'mix')
            forged = Mock(data_dir=store.data_dir)
            forged.get_song_project.return_value = {'id':'../../other'}
            with self.assertRaisesRegex(ValueError,'ruta'):
                LocalProductionArtifactQueries(forged).get('../../other','mix')
