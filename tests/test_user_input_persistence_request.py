import json
from pathlib import Path
import tempfile
import unittest

from core.storage import StorageManager
from application.song_service import SongService
from application.music_spec_revision_service import MusicSpecRevisionService
from application.ace_step_plan_compiler import AceStepPlanCompiler
from adapters.ace_step_execution import AceStepExecutionArguments
from audio.ace_step_profiles import BASE_PROFILE


class PersistedUserRequestTest(unittest.TestCase):
    def test_authorized_controls_reopen_confirm_and_reach_wrapper(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as folder:
            root = Path(folder)
            store = StorageManager(root)
            song = store.create_song_project('Intencion USER')['id']
            other = store.create_song_project('Otro proyecto')['id']
            initial = store.upsert_song_spec(song, dict(bpm=72, key='Am', language='es',
                time_signature='4/4', duration_seconds=120, song_type='balada', emotion='calma',
                ace_step_config='acestep-v15-base',
                _provenance={'song_type':{'source':'ai_suggestion','locked':True}}),
                True, [], user_confirmation_status='confirmed')
            service = SongService.__new__(SongService)
            service.storage = store
            values = dict(bpm=97, key='D Major', language='Spanish', time_signature='6/8',
                duration_seconds=123, song_type='balada', emotion='tierna', instruments=['piano','cello'],
                voice_style='voz humana suave', vocal_expression='intima', dynamic_arc='gran coro final',
                groove='pulso lento', vocal_range='registro medio', mix_balance='voz clara',
                generation_api='high_level', task_type='text2music', inference_steps=32,
                guidance_scale=5, shift=1.5, seed=24680)
            service.execute_music_action(song, dict(tool_id='spec.edit',
                revision_id=initial['revision']['revision_id'], user_authorized=True,
                parameters={'values':values}))
            reopened = StorageManager(root)
            pending = reopened.get_song_project(song)['spec']
            for field, value in values.items():
                self.assertEqual(pending['json_spec'][field], value)
                self.assertEqual(pending['json_spec']['_provenance'][field]['source'],'explicit_user_control')
            self.assertIsNone(reopened.get_song_project(other).get('spec'))
            self.assertTrue(pending['json_spec']['_provenance']['song_type']['locked'])
            self.assertEqual(pending['json_spec']['_provenance']['song_type']['previous_source'],'ai_suggestion')
            self.assertEqual(pending['revision']['user_confirmation_status'],'pending')
            with self.assertRaises(ValueError):
                AceStepPlanCompiler().compile(pending,'Jose, quedate aqui.')
            MusicSpecRevisionService(reopened).confirm_song_specification(song,
                {'revision_id':pending['revision']['revision_id']})
            confirmed = StorageManager(root).get_song_project(song)['spec']
            self.assertEqual(confirmed['revision']['user_confirmation_status'],'confirmed')
            plan = AceStepPlanCompiler().compile(confirmed,'José, quédate aquí.')
            self.assertNotIn('representative_real_sample',plan['pending'])
            expected = dict(bpm=97,key_scale='D Major',vocal_language='es',time_signature='6',
                audio_duration=123.,generation_api='high_level',task_type='text2music',
                inference_steps=32,guidance_scale=5.,shift=1.5,seed=24680,
                lyrics='José, quédate aquí.',
                captions='balada; tierna; piano, cello; voz humana suave; intima; gran coro final; pulso lento; registro medio; voz clara')
            for field,value in expected.items(): self.assertEqual(plan['payload'][field],value)
            trace = {entry['target']:entry for entry in plan['input_trace']['entries']}
            self.assertEqual(trace['vocal_language']['sources'][0]['value'],'Spanish')
            self.assertEqual(trace['time_signature']['sources'][0]['value'],'6/8')
            argv = AceStepExecutionArguments().build(dict(plan=plan,effective_status='approved',inputs_current=True),
                BASE_PROFILE,'python',root/'execution',root/'out.wav')
            context=json.loads((root/'execution'/'ace_execution_context.json').read_text(encoding='utf-8'))
            self.assertEqual(context['approved_inputs'],plan['payload'])
            self.assertEqual(context['spec_revision_id'],confirmed['revision']['revision_id'])
            self.assertEqual(argv[argv.index('--bpm')+1],'97')
            with self.assertRaises(ValueError):
                service.execute_music_action(song,dict(tool_id='spec.edit',revision_id=initial['revision']['revision_id'],
                    user_authorized=True,parameters={'values':{'bpm':80}}))

    def test_set_guidance_does_not_require_midi_or_sample(self):
        result=SongService.describe_set(None,dict(set_id='set1',instrumental_id='i',melody_id='m',lyrics_id='l'))
        message=result['ai_management']['next_suggestion']
        self.assertIn('sample opcional',message)
        self.assertIn('ACE-Step',message)
        self.assertNotIn('MIDI',message)
