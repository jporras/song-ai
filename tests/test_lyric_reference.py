import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'backend'))
from application.assistant_request_policy import lyric_reference, plain_lyric_proposal


class LyricReferenceTest(unittest.TestCase):
    def test_presentation_is_removed_without_changing_sung_words(self):
        response = '## Propuesta de letra:\n\n**1. La tarde en casa.**\n**2. El piano canta.**\n**3. Una voz serena.**\n**4. La calma abraza.**'
        self.assertEqual(plain_lyric_proposal('Propone cuatro lineas cantables', response),
            'La tarde en casa.\nEl piano canta.\nUna voz serena.\nLa calma abraza.')
        self.assertEqual(plain_lyric_proposal('Revisa la letra', response), response)
        self.assertEqual(plain_lyric_proposal('Propone cinco lineas cantables', response), response)
        introduction = 'Aqui tienes cuatro lineas cantables:\n**1. La tarde en casa.**\n**2. El piano canta.**\n**3. Una voz serena.**\n**4. La calma abraza.**'
        self.assertEqual(plain_lyric_proposal('Propone cuatro lineas cantables', introduction),
            'La tarde en casa.\nEl piano canta.\nUna voz serena.\nLa calma abraza.')
        introduction = introduction.replace('lineas cantables', 'versos cantables')
        self.assertEqual(plain_lyric_proposal('Propone cuatro lineas cantables', introduction),
            'La tarde en casa.\nEl piano canta.\nUna voz serena.\nLa calma abraza.')
    def test_mock_text_is_not_used_as_creative_reference_and_original_is_preserved(self):
        asset = {'manifest': {'provider': 'mock-local', 'asset_id': 'l1'},
                 'intent': {'theme': 'lullaby'}, 'content': 'Duerme {name}'}
        reference = lyric_reference(asset)
        self.assertIsNone(reference['content'])
        self.assertEqual(reference['intent'], asset['intent'])
        self.assertEqual(reference['creative_authority'], 'mock_example_not_confirmed_user_wish')
        self.assertEqual(asset['content'], 'Duerme {name}')

    def test_real_draft_remains_available_without_inventing_approval(self):
        reference = lyric_reference({'manifest': {'provider': 'user'}, 'content': 'Una tarde en casa'})
        self.assertEqual(reference['content'], 'Una tarde en casa')
        self.assertEqual(reference['creative_authority'], 'existing_draft_review_required')
