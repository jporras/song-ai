import sys
import unittest
from pathlib import Path
from unittest.mock import Mock

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'backend'))
from application.artifact_regeneration import ArtifactRegeneration
from application.song_service import SongService


class RegenerationTests(unittest.TestCase):
    def test_all_types_dispatch_once_and_unknown_does_not_execute(self):
        handlers = {operation:Mock(return_value={'operation':operation})
                    for operation in set(ArtifactRegeneration.OPERATIONS.values())}
        dispatcher = ArtifactRegeneration(handlers)
        for artifact,operation in ArtifactRegeneration.OPERATIONS.items():
            for handler in handlers.values():
                handler.reset_mock()
            self.assertEqual(dispatcher.execute('song',artifact), {'operation':operation})
            handlers[operation].assert_called_once_with('song')
            self.assertEqual(sum(h.call_count for h in handlers.values()),1)
        for handler in handlers.values():
            handler.reset_mock()
        with self.assertRaises(ValueError):
            dispatcher.execute('song','unknown')
        self.assertFalse(any(h.called for h in handlers.values()))

    def test_song_service_uses_modern_lyrics_proposal_and_local_review(self):
        service = SongService.__new__(SongService)
        methods = ['generate_professional_lyrics','review_professional_lyrics','generate_professional_music_plan',
            'generate_professional_midi','generate_professional_instrumental','generate_professional_vocals',
            'convert_professional_voice','mix_professional_song','master_professional_song','export_professional_song']
        for method in methods:
            setattr(service,method,Mock(return_value={'operation':method}))
        self.assertFalse(hasattr(service,'professional_songs'))
        result = service.regenerate_professional_artifact('song','lyrics_json')
        self.assertEqual(result['operation'],'generate_professional_lyrics')
        service.generate_professional_lyrics.assert_called_once_with('song')
        service.regenerate_professional_artifact('song','lyrics_approved_json')
        service.review_professional_lyrics.assert_called_once_with('song')
