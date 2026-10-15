import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'backend'))
from application.spec_field_review import field_review
from application.song_specification_service import SongSpecificationService


class SpecFieldReviewTest(unittest.TestCase):
    def test_delegation_proposal_is_not_a_confirmed_decision(self):
        review = field_review(None, {'source':'explicit_delegation_proposal','confirmation':'pending'}, 'optional_or_delegated_pending_review', True)
        self.assertEqual(review['decision_status'], 'delegation_proposed')
        self.assertIn('silencio', review['review_action'])
        chosen = field_review(None, {'source':'explicit_user_delegation','confirmation':'pending'}, 'delegated_to_profile', True)
        self.assertEqual(chosen['decision_status'], 'delegated')
        self.assertIn('confirmar', chosen['review_action'])

    def test_saved_user_value_is_distinct_from_inferred_value(self):
        self.assertEqual(field_review(97, {'source':'explicit_user_phase'}, None, True)['decision_status'], 'user_saved')
        self.assertEqual(field_review(97, {'source':'codex_consolidation'}, None, True)['decision_status'], 'proposed')
        self.assertEqual(field_review(0, {'source':'explicit_user_control'}, None, True)['decision_status'], 'user_saved')
        self.assertEqual(field_review(4, {'source':'explicit_user_control'}, 'optional_or_delegated_pending_review', True)['decision_status'], 'user_saved')

    def test_non_applicable_field_does_not_ask_for_a_decision(self):
        self.assertEqual(field_review(None, {}, None, False)['decision_status'], 'not_applicable')
        self.assertEqual(field_review(None, {}, None, True)['decision_status'], 'missing')

    def test_catalog_keeps_values_and_counts_review_states_separately(self):
        spec = {'bpm':97, '_provenance':{'bpm':{'source':'explicit_user_phase'}}}
        catalog = SongSpecificationService().catalog(spec)
        fields = [f for g in catalog['groups'] for f in g['fields']]
        bpm = next(f for f in fields if f['id']=='bpm')
        self.assertEqual(bpm['value'], 97)
        self.assertEqual(bpm['decision_status'], 'user_saved')
        self.assertEqual(sum(catalog['summary']['review_counts'].values()), catalog['summary']['total'])
        self.assertEqual(spec, {'bpm':97, '_provenance':{'bpm':{'source':'explicit_user_phase'}}})

    def test_every_engine_field_has_meaning_effect_and_example(self):
        catalog = SongSpecificationService().catalog({})
        fields = {f['id']:f for g in catalog['groups'] for f in g['fields']}
        for key in SongSpecificationService.ENGINE_FIELDS:
            self.assertTrue(all(fields[key]['detailed_help'][part] for part in ('meaning','effect','example')), key)

    def test_all_catalog_families_have_examples_without_creating_defaults(self):
        catalog = SongSpecificationService().catalog({})
        fields = [f for group in catalog['groups'] for f in group['fields']]
        self.assertEqual(len(fields), 49)
        for field in fields:
            self.assertTrue(all(field['detailed_help'][part] for part in ('meaning','effect','example')), field['id'])
            self.assertIsNone(field['value'])
