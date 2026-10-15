import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

sys.path[:0] = [str(Path(__file__).resolve().parents[1]/'tools')]
from acestep_runtime_options import INPUT_ARGUMENTS, runtime_input_trace, load_execution_context


class RuntimeInputsTest(unittest.TestCase):
    def fixture(self):
        approved = dict(captions='Balada; piano; voz suave', lyrics='[Verse]\nJosé, quédate aquí.',
            bpm=97, key_scale='Am', time_signature='4', vocal_language='es', audio_duration=123.0,
            task_type='repaint', generation_api='direct', lm_model_path='acestep-5Hz-lm-0.6B',
            seed=24680, inference_steps=32, guidance_scale=5.0, shift=1.5, reference_audio='reference.wav',
            src_audio='source.wav', instruction='guitar', repainting_start=1.5, repainting_end=4.5,
            audio_cover_strength=.75, chunk_mask_mode='explicit')
        args = SimpleNamespace(config_path='acestep-v15-base', bpm=97, key_scale='Am', time_signature='4',
            vocal_language='es', duration=123.0, task_type='repaint', generation_api='direct',
            lm_model_path='acestep-5Hz-lm-0.6B', seed=24680, infer_step=32, guidance_scale=5.0, shift=1.5,
            reference_audio='reference.wav', src_audio='source.wav', instruction='guitar',
            repainting_start=1.5, repainting_end=4.5, audio_cover_strength=.75, chunk_mask_mode='explicit')
        return args, {'spec_revision_id':'user-r1', 'plan_sha256':'plan-hash', 'approved_inputs':approved}

    def test_all_twenty_one_inputs_match_and_each_unauthorized_change_is_rejected(self):
        args, context = self.fixture()
        inputs = context['approved_inputs']
        self.assertEqual(set(inputs), set(INPUT_ARGUMENTS) | {'captions','lyrics'})
        self.assertEqual(len(inputs), 21)
        trace = runtime_input_trace(args, inputs['captions'], inputs['lyrics'], context)
        self.assertEqual(len(trace['entries']), 21)
        self.assertEqual(trace['spec_revision_id'], 'user-r1')
        for field in inputs:
            changed_args, changed_context = self.fixture()
            caption, lyrics = inputs['captions'], inputs['lyrics']
            if field == 'captions': caption += ' changed'
            elif field == 'lyrics': lyrics += '\nCambio no autorizado'
            else:
                name = INPUT_ARGUMENTS[field]
                value = getattr(changed_args, name)
                setattr(changed_args, name, value + 1 if isinstance(value, (int, float)) else value + ' changed')
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, field):
                runtime_input_trace(changed_args, caption, lyrics, changed_context)

    def test_selected_audio_checksum_is_checked_and_file_substitution_fails(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as folder:
            args, context = self.fixture()
            source = Path(folder)/'source.wav'
            source.write_bytes(b'original selected audio')
            checksum = hashlib.sha256(source.read_bytes()).hexdigest()
            args.src_audio = context['approved_inputs']['src_audio'] = str(source)
            context['approved_audio_sha256'] = {'src_audio':checksum}
            trace = runtime_input_trace(args, context['approved_inputs']['captions'], context['approved_inputs']['lyrics'], context)
            self.assertEqual(next(e for e in trace['entries'] if e['field']=='src_audio')['verified_audio_sha256'], checksum)
            source.write_bytes(b'replaced audio')
            with self.assertRaisesRegex(ValueError, 'audio seleccionado cambio'):
                runtime_input_trace(args, context['approved_inputs']['captions'], context['approved_inputs']['lyrics'], context)

    def test_context_shape_unknown_inputs_and_checksum_are_rejected(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as folder:
            path = Path(folder)/'context.json'
            for change in ({'approved_inputs':[]}, {'approved_inputs':{'future_input':1}},
                           {'spec_revision_id':None}, {'approved_audio_sha256':{'src_audio':'bad'}}):
                _, context = self.fixture()
                context.update(change)
                path.write_text(json.dumps(context),encoding='utf-8')
                with self.subTest(change=change), self.assertRaises(ValueError): load_execution_context(path)
            _, context = self.fixture()
            path.write_text(json.dumps(context),encoding='utf-8')
            self.assertEqual(load_execution_context(path),context)

    def test_legacy_context_remains_identified_as_partial(self):
        args, _ = self.fixture()
        trace = runtime_input_trace(args,'Caption','Letra',{'requested_options':{'seed':24680}})
        self.assertEqual(trace['status'],'legacy_context_without_full_input_contract')
        self.assertEqual(trace['entries'],[])

    def test_actual_cli_rejects_changed_input_before_loading_or_deleting_previous_output(self):
        import acestep_generate
        from dataclasses import replace
        from adapters.ace_step_execution import AceStepExecutionArguments
        from audio.ace_step_profiles import resolve_ace_step_profile
        from application.ace_step_plan_compiler import AceStepPlanCompiler
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as folder:
            root = Path(folder)
            profile = replace(resolve_ace_step_profile('base'), checkpoint_root=str(root/'checkpoints'))
            record = {'revision': {'revision_id':'r1', 'user_confirmation_status':'confirmed', 'deterministic_valid':True},
                      'missing_fields':[], 'json_spec': {'task_type':'text2music', 'ace_step_config':profile.config_path,
                      'bpm':97, 'key':'Am', 'time_signature':'4/4', 'language':'es', 'duration_seconds':120,
                      'song_type':'balada', 'emotion':'tierna', 'instruments':['piano']}}
            plan = AceStepPlanCompiler().compile(record,'[Verse]\nJosé, quédate aquí.')
            output = root/'original.wav'
            output.write_bytes(b'original audio must survive a rejected request')
            argv = AceStepExecutionArguments().build({'plan':plan,'effective_status':'approved','inputs_current':True},
                profile,sys.executable,root,output)
            argv[argv.index('--bpm')+1] = '99'
            with patch.object(sys,'argv',argv[1:]), \
                 patch.object(acestep_generate,'build_diagnostics') as diagnostics:
                with self.assertRaisesRegex(ValueError,'input aprobado: bpm'):
                    acestep_generate.main()
                diagnostics.assert_not_called()
            self.assertEqual(output.read_bytes(),b'original audio must survive a rejected request')
            self.assertFalse((root/'checkpoints').exists())
