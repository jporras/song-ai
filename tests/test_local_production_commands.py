import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch
from contextlib import ExitStack

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'backend'))
from core.storage import StorageManager
from application.song_service import SongService
from application.local_production_commands import LocalProductionCommands


class LocalProductionCommandTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.addCleanup(self.folder.cleanup)
        self.store = StorageManager(Path(self.folder.name))
        self.song = self.store.create_song_project('Alma')['id']
        markdown = '## VERSO\nAlma canta con alegría.\n'
        self.saved = self.store.upsert_song_spec(self.song, {
            'title':'Alma', 'voice_style':'cálida',
            '_lyrics_document':{'markdown':markdown,'sections':[{'id':'verse','type':'VERSO','text':'Alma canta con alegría.'}]}},
            True, [], deterministic_valid=True, user_confirmation_status='confirmed')
        self.directory = self.store.data_dir/'projects'/self.song
        self.directory.mkdir(parents=True,exist_ok=True)
        self.store.write_json(self.directory/'lyrics_approved.json', {'approved_by_qwen':True,'lyrics':{'sections':[]}})
        self.store.write_json(self.directory/'music_plan.json', {'bpm':72})
        self.store.write_json(self.directory/'midi_metadata.json', {'markers':[]})
        for name in ('song_base.mid','instrumental.wav','vocals.wav','vocals_converted.wav','mix.wav'):
            (self.directory/name).write_bytes(b'compatibility fixture')

    def test_all_seven_routes_use_injected_local_providers_without_legacy_initialization(self):
        provider_classes = ['music_plan_service.MusicPlanService','midi_generation_service.MidiGenerationService',
            'instrumental_generation_service.InstrumentalGenerationService','vocal_synthesis_service.VocalSynthesisService',
            'voice_conversion_service.VoiceConversionService','mixing_service.MixingService',
            'professional_full_song_service.ProfessionalFullSongService','mastering_service.MasteringService']
        providers = {}
        with ExitStack() as stack:
            legacy = stack.enter_context(patch('application.professional_song_service.ProfessionalSongService',
                                               side_effect=AssertionError('Historical service initialized')))
            stack.enter_context(patch('application.local_production_context.FinalProductionGate.require_for_project',return_value={}))
            for name in provider_classes:
                provider = Mock(command_template='')
                provider.configured.return_value = True
                for method in ('generate','run','mix','master'):
                    getattr(provider,method).side_effect = lambda *args, **kwargs: {'project':self.store.get_song_project(self.song)}
                stack.enter_context(patch('application.'+name,return_value=provider))
                providers[name] = provider
            service = SongService(self.store)
            for name in ['generate_professional_music_plan','generate_professional_midi','generate_professional_instrumental',
                         'generate_professional_vocals','convert_professional_voice','mix_professional_song']:
                getattr(service,name)(self.song)
            service.master_professional_song(self.song,generation_profile='quality')
            providers['professional_full_song_service.ProfessionalFullSongService'].generate.assert_called_once_with(
                self.song,generation_profile='quality')
            self.assertNotIn('_legacy_professional_songs',service.__dict__)
            self.assertNotIn('model_manager',service.__dict__)
            legacy.assert_not_called()
        self.assertEqual(self.store.get_song_project(self.song)['spec'],self.saved)
        self.assertFalse(any(e.get('active_model')=='qwen' for e in self.store.list_song_project_events(self.song)))

    def test_unconfirmed_spec_never_reseeds_or_runs_provider(self):
        pending = self.store.upsert_song_spec(self.song,self.saved['json_spec'],False,[],
                                             deterministic_valid=True,user_confirmation_status='pending')
        provider = Mock()
        with patch('application.music_plan_service.MusicPlanService',return_value=provider):
            with self.assertRaisesRegex(ValueError,'confirma la ficha'):
                LocalProductionCommands(self.store).execute('music_plan',self.song)
        provider.generate.assert_not_called()
        self.assertEqual(self.store.get_song_project(self.song)['spec'],pending)

    def test_voice_failure_records_failed_phase_and_keeps_spec(self):
        provider = Mock(command_template='fixture-command')
        provider.generate.side_effect = RuntimeError('fixture failure')
        with patch('application.vocal_synthesis_service.VocalSynthesisService',return_value=provider):
            with self.assertRaisesRegex(RuntimeError,'fixture failure'):
                LocalProductionCommands(self.store).execute('vocals',self.song)
        project = self.store.get_song_project(self.song)
        self.assertEqual(project['status'],'failed')
        self.assertEqual(project['current_phase'],'VOCAL_SYNTHESIS')
        self.assertEqual(project['spec'],self.saved)

    def test_master_uses_active_lyrics_and_rejects_placeholder_before_provider(self):
        spec = dict(self.saved['json_spec'])
        spec['_lyrics_document'] = {'markdown':'## VERSO\nHola {nombre}', 'sections':[]}
        self.store.upsert_song_spec(self.song,spec,True,[],deterministic_valid=True,user_confirmation_status='confirmed')
        provider = Mock()
        with patch('application.professional_full_song_service.ProfessionalFullSongService',return_value=provider):
            with self.assertRaisesRegex(ValueError,'placeholders'):
                LocalProductionCommands(self.store).execute('master',self.song)
        provider.generate.assert_not_called()

    def test_compatibility_service_is_lazy_and_cached(self):
        with patch('application.professional_song_service.ProfessionalSongService') as historical:
            service = SongService(self.store)
            historical.assert_not_called()
            first = service.professional_songs
            self.assertIs(first,service.professional_songs)
            historical.assert_called_once()
