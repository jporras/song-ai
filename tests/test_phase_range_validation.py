import unittest
from application.phase_range_validation import validate_phase_ranges

class PhaseRangesTest(unittest.TestCase):
    def test_invalid_and_boundary_directions(self):
        for phase, section, key in [('voice','voice','vibrato'),('instrumental','instrumental','brightness'),('midi','midiPlan','swing')]:
            for value in (-1, 128, '', True, float('nan'), float('inf')):
                with self.subTest(phase=phase,value=value), self.assertRaises(ValueError):
                    validate_phase_ranges(phase,{section:{key:value}})
            validate_phase_ranges(phase,{section:{key:0}})
            validate_phase_ranges(phase,{section:{}})
        with self.assertRaises(ValueError):
            validate_phase_ranges('music-plan',{'musicPlan':{'sections':[{'intensity':101}]}})
        validate_phase_ranges('voice',{'voice':{'layers':[{'level':100}]}})
