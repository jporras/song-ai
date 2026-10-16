import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'backend'))
from audio.ffmpeg_binary import resolve_ffmpeg


class FfmpegBinaryTest(unittest.TestCase):
    def test_uses_managed_binary_when_path_has_no_ffmpeg(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as folder:
            binary = Path(folder) / 'data' / 'tools' / 'ffmpeg' / 'bin' / (
                'ffmpeg.exe' if os.name == 'nt' else 'ffmpeg')
            binary.parent.mkdir(parents=True)
            binary.write_bytes(b'test fixture')
            with patch('audio.ffmpeg_binary.shutil.which', return_value=None):
                self.assertEqual(resolve_ffmpeg(Path(folder)), str(binary.resolve()))

    def test_prefers_path_binary(self):
        with patch('audio.ffmpeg_binary.shutil.which', return_value='ffmpeg-on-path'):
            self.assertEqual(resolve_ffmpeg(Path('unused')), 'ffmpeg-on-path')
