import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'backend'))
from application.song_specification_service import SongSpecificationService
from models.ace_step_capability_profile import CONNECTED_PROFILE
from models.ace_step_generation_options import generation_options
from models.ace_step_tasks import validate_task_inputs
from application.ace_step_plan_compiler import AceStepPlanCompiler


class CapabilityIntegrationTest(unittest.TestCase):
    def fields(self, spec):
        return {field['id']: field for group in SongSpecificationService().catalog(spec)['groups']
                for field in group['fields']}

    def test_creation_does_not_require_source_or_lm(self):
        fields = self.fields({'task_type': 'text2music'})
        self.assertFalse(fields['src_audio']['required_for_task'])
        self.assertFalse(fields['source_artifact_id']['applicable'])
        self.assertFalse(fields['lm_model_path']['applicable'])
        validate_task_inputs('text2music', 'acestep-v15-turbo')
        self.assertTrue(self.fields({'generation_api': 'high_level_lm'})['lm_model_path']['applicable'])

    def test_studio_requirements_and_validator_agree(self):
        for task in ('cover', 'repaint', 'lego', 'extract', 'complete'):
            with self.subTest(task=task):
                fields = self.fields({'task_type': task})
                self.assertTrue(fields['source_artifact_id']['required_for_task'])
                with self.assertRaises(ValueError):
                    validate_task_inputs(task, 'acestep-v15-base')
        fields = self.fields({'task_type': 'lego'})
        self.assertTrue(fields['instruction']['required_for_task'])
        self.assertTrue(fields['target_tracks']['required_for_task'])
        self.assertIn('guitar', fields['target_tracks']['options'])
        with self.assertRaises(ValueError):
            validate_task_inputs('lego', 'acestep-v15-turbo', 'source.wav', 'guitar', tracks=('guitar',))

    def test_catalog_ranges_match_backend_rejections(self):
        for config, steps in [('acestep-v15-turbo', 20), ('acestep-v15-base', 200)]:
            fields = self.fields({'ace_step_config': config})
            self.assertEqual(fields['inference_steps']['capability_policy']['maximum'], steps)
            generation_options({'ace_step_config': config, 'inference_steps': steps})
            with self.assertRaises(ValueError):
                generation_options({'ace_step_config': config, 'inference_steps': steps+1})
        self.assertEqual(self.fields({'ace_step_config': 'acestep-v15-turbo'})
                         ['guidance_scale']['capability_policy']['fixed_value'], 1)
        with self.assertRaises(ValueError):
            generation_options({'ace_step_config': 'acestep-v15-turbo', 'guidance_scale': 2})

    def test_contract_never_claims_runtime_or_audio_validation(self):
        catalog = SongSpecificationService().catalog()
        self.assertEqual(catalog['summary']['total'], 49)
        self.assertEqual(catalog['capability_profile']['runtime_availability'], 'requires_preflight')
        self.assertEqual(catalog['capability_profile']['audio_quality'], 'not_verified_by_contract')
        self.assertEqual(catalog['capability_profile']['version'], CONNECTED_PROFILE.version)

    def test_compiled_plan_identifies_the_shared_contract(self):
        record = {'json_spec': {'bpm': 97, 'key': 'Am', 'language': 'es',
                  'duration_seconds': 120, 'song_type': 'balada'}, 'missing_fields': [],
                  'revision': {'revision_id': 'r1', 'user_confirmation_status': 'confirmed',
                               'deterministic_valid': True}}
        plan = AceStepPlanCompiler().compile(record, 'Letra')
        self.assertEqual(plan['capability_profile']['version'], CONNECTED_PROFILE.version)
        self.assertEqual(len(plan['capability_profile']['sha256']), 64)


if __name__ == '__main__':
    unittest.main()
