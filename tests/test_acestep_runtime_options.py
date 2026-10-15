import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from acestep_runtime_options import runtime_options, runtime_trace, load_execution_context


class RuntimeOptionsTest(unittest.TestCase):
    def test_wrapper_rejects_changed_approved_values_or_model(self):
        with self.assertRaisesRegex(ValueError,'opción aprobada'):
            runtime_trace(self.args(seed=42), {'requested_options':{'seed':0}})
        with self.assertRaisesRegex(ValueError,'perfil'):
            runtime_trace(self.args(), {'execution_profile':{'config_path':'acestep-v15-base'}})

    def test_context_loader_rejects_invalid_shape_unknown_options_and_large_files(self):
        import tempfile
        import json
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/'context.json'
            for data in ([], {'requested_options':[]}, {'requested_options':{'unknown':7}}):
                path.write_text(json.dumps(data), encoding='utf-8')
                with self.assertRaises(ValueError):
                    load_execution_context(path)
            path.write_text(' ' * 65537, encoding='utf-8')
            with self.assertRaises(ValueError):
                load_execution_context(path)
            self.assertIsNone(load_execution_context(''))
    def args(self, **changes):
        return SimpleNamespace(**{'config_path':'acestep-v15-turbo','seed':42,'infer_step':4,
                                  'guidance_scale':None,'shift':None, **changes})

    def test_delegated_defaults_match_model_and_explicit_values_are_preserved(self):
        self.assertEqual(runtime_options(self.args())['guidance_scale'], 1)
        self.assertEqual(runtime_options(self.args())['shift'], 3)
        self.assertEqual(runtime_options(self.args(config_path='acestep-v15-base'))['guidance_scale'], 15)
        self.assertEqual(runtime_options(self.args(config_path='acestep-v15-base'))['shift'], 1)
        self.assertEqual(runtime_options(self.args(seed=0,guidance_scale=1,shift=2))['seed'], 0)
        self.assertEqual(runtime_options(self.args(shift=2))['shift'], 2)

    def test_trace_keeps_delegation_and_distinguishes_profile_from_override(self):
        trace = runtime_trace(self.args(seed=0), {'spec_revision_id':'r1','requested_options':{'seed':0},
            'provenance':{'shift':{'source':'explicit_user_delegation'}}})
        fields = {entry['field']:entry for entry in trace['entries']}
        self.assertEqual(trace['spec_revision_id'], 'r1')
        self.assertEqual(fields['seed']['source'], 'approved_override')
        self.assertEqual(fields['inference_steps']['source'], 'execution_profile')
        self.assertEqual(fields['shift']['wrapper_value'], 3)
        self.assertEqual(fields['shift']['provenance']['source'], 'explicit_user_delegation')
        self.assertIn('not_engine_observation', trace['scope'])
