import sys
import tempfile
import unittest
import wave
import struct
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'backend'))
from adapters.pcm_edit_comparison import compare_pcm_edit


class EditComparisonTest(unittest.TestCase):
    def test_local_change_has_identical_exterior_and_measured_selected_difference(self):
        with tempfile.TemporaryDirectory() as folder:
            paths=[Path(folder)/name for name in ('source.wav','edit.wav')]
            for path,values in zip(paths,([1000]*30,[1000]*10+[2000]*10+[1000]*10)):
                with wave.open(str(path),'wb') as w:
                    w.setnchannels(1);w.setsampwidth(2);w.setframerate(10)
                    w.writeframes(struct.pack('<30h',*values))
            report=compare_pcm_edit(*paths,1,2)
            self.assertEqual([r['identical_sample_fraction'] for r in report['regions']],[1,0,1])
            self.assertAlmostEqual(report['regions'][1]['difference_rms_full_scale'],1000/32768)
            self.assertFalse(report['quality_verified'])
            with self.assertRaises(ValueError):compare_pcm_edit(*paths,1,4)
