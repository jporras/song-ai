import sys
import tempfile
import unittest
import wave
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from adapters.pcm_signal_metrics import measure_pcm_signal


class PcmMetricsTest(unittest.TestCase):
    def write(self, path, width, values):
        raw = bytes(v + 128 for v in values) if width == 1 else b"".join(v.to_bytes(width, "little", signed=True) for v in values)
        with wave.open(str(path), "wb") as audio:
            audio.setnchannels(2)
            audio.setsampwidth(width)
            audio.setframerate(8000)
            audio.writeframes(raw)

    def test_silence_and_signed_levels_for_all_pcm_widths(self):
        with tempfile.TemporaryDirectory() as folder:
            directory = Path(folder)
            for width in (1, 2, 3, 4):
                audio = directory / f"{width}.wav"
                self.write(audio, width, [0, 0, 0, 0])
                silent = measure_pcm_signal(audio, directory)
                self.assertTrue(silent["digital_silence"])
                self.assertIsNone(silent["rms_dbfs"])
                scale = 2 ** (8 * width - 1)
                self.write(audio, width, [-scale, scale - 1, 0, 0])
                result = measure_pcm_signal(audio, directory)
                self.assertFalse(result["digital_silence"])
                self.assertEqual(result["sample_values"], 4)
                self.assertEqual(result["full_scale_values"], 2)
                self.assertEqual(result["peak_dbfs"], 0)
                self.assertLess(result["rms_dbfs"], 0)
                self.assertFalse(result["quality_verified"])
                self.assertNotEqual(result["audio_sha256"], silent["audio_sha256"])

    def test_small_nonzero_signal_is_not_silence_or_full_scale(self):
        with tempfile.TemporaryDirectory() as folder:
            directory = Path(folder)
            audio = directory / "quiet.wav"
            self.write(audio, 2, [1, -1, 1, -1])
            result = measure_pcm_signal(audio, directory)
            self.assertFalse(result["digital_silence"])
            self.assertEqual(result["full_scale_values"], 0)
            self.assertAlmostEqual(result["peak_dbfs"], result["rms_dbfs"])
