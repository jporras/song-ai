import sys
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'backend'))
from application.ace_step_plan_compiler import AceStepPlanCompiler
from adapters.ace_step_execution import AceStepExecutionArguments
from audio.ace_step_profiles import resolve_ace_step_profile
from models.ace_step_input_trace import input_trace, INPUT_SOURCES, record_verified_audio


class UserInputAcceptanceTest(unittest.TestCase):
    def test_complete_preserves_multiple_user_tracks_to_wrapper(self):
        import json
        from models.ace_step_tasks import validate_task_inputs
        record = self.record('complete')
        record['json_spec'].update(target_tracks=['drums', 'bass'],
            instruction='Complete the input track with drums and bass:')
        original = deepcopy(record)
        plan = AceStepPlanCompiler().compile(record, '[Verse]\nLetra')
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            profile = resolve_ace_step_profile('base')
            argv = AceStepExecutionArguments().build(dict(plan=plan,
                effective_status='approved', inputs_current=True), profile, 'python', root, root/'out.wav')
            tracks = argv[argv.index('--tracks') + 1]
            self.assertEqual(tracks, 'drums,bass')
            instruction = argv[argv.index('--instruction') + 1]
            self.assertEqual(instruction, original['json_spec']['instruction'])
            validate_task_inputs('complete', profile.config_path,
                argv[argv.index('--src-audio') + 1], instruction, tracks=tuple(tracks.split(',')))
            context = json.loads((root/'ace_execution_context.json').read_text(encoding='utf-8'))
            self.assertEqual(context['wrapper_task_constraints']['target_tracks'], ['drums', 'bass'])
            self.assertEqual(context['wrapper_task_constraints']['cli_rule'], 'comma_join')
        self.assertEqual(record, original)

    def test_numeric_extremes_across_every_compatible_config_task_and_api(self):
        routes = 0
        for config in ('acestep-v15-base','acestep-v15-turbo'):
            for task in ('text2music','cover','repaint','lego','extract','complete'):
                if config.endswith('turbo') and task in ('lego','extract','complete'):
                    continue
                for api in ('direct','high_level','high_level_lm'):
                    if api == 'high_level_lm' and task != 'text2music':
                        continue
                    routes += 1
                    for high in (False,True):
                        with self.subTest(config=config,task=task,api=api,high=high):
                            record=self.record(task,api)
                            spec=record['json_spec']
                            values=dict(bpm=300 if high else 30,duration_seconds=600 if high else 10,
                                seed=4294967295 if high else 0,
                                inference_steps=(20 if config.endswith('turbo') else 200) if high else 1,
                                guidance_scale=15 if high and config.endswith('base') else 1,
                                shift=10 if high else .1)
                            spec.update(values,ace_step_config=config)
                            original=deepcopy(record)
                            plan=AceStepPlanCompiler().compile(record,'Letra USER')
                            expected={**values,'audio_duration':values['duration_seconds']}
                            expected.pop('duration_seconds')
                            for field,value in expected.items():
                                self.assertEqual(plan['payload'][field],value)
                            self.assertEqual(record,original)
                            with tempfile.TemporaryDirectory() as folder:
                                root=Path(folder)
                                args=AceStepExecutionArguments().build(dict(plan=plan,effective_status='approved',inputs_current=True),
                                    resolve_ace_step_profile('turbo' if config.endswith('turbo') else 'base'),
                                    'python',root,root/'out.wav')
                                self.assertEqual(args[args.index('--seed')+1],str(values['seed']))
        self.assertEqual(routes,20)

    def record(self, task='text2music', api='direct'):
        spec = dict(task_type=task, generation_api=api, ace_step_config='acestep-v15-base',
                    bpm=97, key='Am', time_signature='4/4', language='Spanish',
                    duration_seconds=123, seed=24680, inference_steps=32, guidance_scale=5,
                    shift=1.5, song_type='balada', emotion='triste', instruments=['piano', 'guitar'],
                    voice_style='voz suave', vocal_expression='íntima', dynamic_arc='gran coro final',
                    groove='suave', vocal_range='medio', mix_balance='voz al frente',
                    reference_audio='reference.wav', reference_artifact_id='ref1',
                    lm_model_path='acestep-5Hz-lm-0.6B')
        if task != 'text2music':
            spec.update(src_audio='source.wav', source_artifact_id='source1', instruction='guitar',
                        target_tracks=['guitar'], repainting_start=1.5, repainting_end=4.5,
                        audio_cover_strength=.75)
        spec['_provenance'] = {key: {'source': 'explicit_user_control'} for key in spec}
        return dict(json_spec=spec, missing_fields=[], revision=dict(revision_id='user-r1',
                    user_confirmation_status='confirmed', deterministic_valid=True))

    def test_user_values_reach_each_connected_route_without_mutating_spec(self):
        expected = dict(bpm=97, key_scale='Am', time_signature='4', vocal_language='es',
                        audio_duration=123., seed=24680, inference_steps=32, guidance_scale=5., shift=1.5)
        covered = set()
        for task in ('text2music', 'cover', 'repaint', 'lego', 'extract', 'complete'):
            for api in ('direct', 'high_level', 'high_level_lm'):
                if api == 'high_level_lm' and task != 'text2music':
                    continue
                with self.subTest(task=task, api=api), tempfile.TemporaryDirectory() as folder:
                    record = self.record(task, api)
                    original = deepcopy(record)
                    lyrics = '[Verse]\nJosé, quédate aquí.'
                    plan = AceStepPlanCompiler().compile(record, lyrics)
                    self.assertEqual(record, original)
                    for key, value in expected.items():
                        self.assertEqual(plan['payload'][key], value)
                    self.assertEqual(plan['payload']['lyrics'], lyrics)
                    self.assertEqual(plan['payload']['captions'],
                        'balada; triste; piano, guitar; voz suave; íntima; gran coro final; suave; medio; voz al frente')
                    trace = {e['target']: e for e in plan['input_trace']['entries']}
                    self.assertEqual(set(trace), set(plan['payload']))
                    self.assertEqual(trace['vocal_language']['sources'][0]['value'], 'Spanish')
                    self.assertEqual(trace['vocal_language']['rule'], 'language_alias')
                    self.assertEqual(trace['bpm']['sources'][0]['provenance']['source'], 'explicit_user_control')
                    profile = resolve_ace_step_profile('base')
                    root = Path(folder)
                    argv = AceStepExecutionArguments().build(dict(plan=plan, effective_status='approved',
                        inputs_current=True), profile, 'python', root, root/'out.wav')
                    for key, flag in AceStepExecutionArguments.FIELDS.items():
                        if key in plan['payload']:
                            self.assertEqual(argv[argv.index(flag)+1], str(plan['payload'][key]))
                    self.assertEqual((root/'ace_plan_lyrics.md').read_text(encoding='utf-8'), lyrics)
                    self.assertEqual((root/'ace_plan_caption.txt').read_text(encoding='utf-8'), plan['payload']['captions'])
                    import json
                    context = json.loads((root/'ace_execution_context.json').read_text(encoding='utf-8'))
                    self.assertEqual(context['approved_inputs'], plan['payload'])
                    self.assertEqual(context['spec_revision_id'], 'user-r1')
                    if task in ('lego', 'extract', 'complete'):
                        self.assertEqual(argv[argv.index('--tracks') + 1], 'guitar')
                        self.assertEqual(context['wrapper_task_constraints']['target_tracks'],
                                         record['json_spec']['target_tracks'])
                        from models.ace_step_tasks import validate_task_inputs
                        validate_task_inputs(task, profile.config_path,
                            argv[argv.index('--src-audio') + 1], argv[argv.index('--instruction') + 1],
                            float(argv[argv.index('--repainting-start') + 1]) if '--repainting-start' in argv else 0,
                            float(argv[argv.index('--repainting-end') + 1]) if '--repainting-end' in argv else -1,
                            tuple(argv[argv.index('--tracks') + 1].split(',')))
                    covered.update(plan['payload'])
        self.assertEqual(covered, set(INPUT_SOURCES) | {'captions', 'lyrics'})

    def test_verified_audio_trace_binds_selected_artifact_and_checksum(self):
        trace = input_trace({'src_audio':'source.wav','source_artifact_id':'user-source'}, {'src_audio':'source.wav'}, 'rev')
        evidence = {'artifact_id':'foreign','sha256':'abc','file_path':'source.wav'}
        with self.assertRaises(ValueError):
            record_verified_audio(trace, 'src_audio', evidence)
        self.assertEqual(trace['entries'][0]['verification_status'], 'pending_preview_verification')
        record_verified_audio(trace, 'src_audio', {**evidence,'artifact_id':'user-source'})
        self.assertEqual(trace['entries'][0]['audio_sha256'], 'abc')
        self.assertEqual(trace['entries'][0]['sources'][0]['field'], 'source_artifact_id')
        self.assertEqual(trace['entries'][0]['sources'][1]['provenance']['source'], 'system_artifact_resolution')
        self.assertEqual(trace['entries'][0]['result'], 'source.wav')
        self.assertEqual(trace['entries'][0]['verification_status'], 'verified_project_audio_artifact')

    def test_new_input_without_mapping_rule_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'sin regla'):
            input_trace({}, {'future_input': 1}, 'r1')

    def test_invalid_user_values_are_not_silently_fixed(self):
        for field, value in [('bpm', 97.5), ('language', 'not-a-language'), ('emotion', 'x'*513)]:
            record = self.record()
            record['json_spec'][field] = value
            original = deepcopy(record)
            with self.assertRaises(ValueError):
                AceStepPlanCompiler().compile(record, 'Letra')
            self.assertEqual(record, original)
        with self.assertRaises(ValueError):
            AceStepPlanCompiler().compile(self.record(), 'x'*4097)


if __name__ == '__main__':
    unittest.main()
