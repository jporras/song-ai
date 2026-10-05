import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from application.song_service import SongService


class AssistantSampleGuidanceTest(unittest.TestCase):
    def test_guidance_requires_sample_with_and_without_active_set(self):
        service = SongService.__new__(SongService)
        project = {"set": {"project_name": "Mi idea", "description": "Una celebracion"},
                   "assets": {name: {"intent": {}, "content": ""}
                              for name in ("instrumental", "melody", "lyrics")}}
        for context in (None, project):
            with self.subTest(active_set=context is not None):
                prompt = service._build_gemma_prompt(context, {"question": "Que sigue?"}, {})
                self.assertIn("sample vigente de ese set", prompt)
                self.assertIn("aprobado por el usuario", prompt)
                self.assertIn("sample mock no acredita produccion real", prompt)
                self.assertNotIn("No presentes sample", prompt)

    def test_initial_guidance_identifies_preparation_and_missing_pieces(self):
        service = SongService.__new__(SongService)
        prompt = service._build_gemma_prompt(None, {}, {"missing": ["letra"]})
        self.assertIn("preparando las tres piezas obligatorias", prompt)
        self.assertIn("instrumental, melodia vocal y letra", prompt)
        self.assertIn("'missing': ['letra']", prompt)
