import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'backend'))
from application.lyric_section_direction import validate_section_directions, section_direction_trace


class DirectionTests(unittest.TestCase):
    def test_locked_direction_requires_explicit_unlock_and_cannot_be_deleted(self):
        old = [{'id':'chorus','type':'CORO','direction':'Crece sin batería','direction_locked':True}]
        for new in ([], [{**old[0],'direction':'Añadir batería'}], [{**old[0],'direction_locked':False}]):
            with self.assertRaises(ValueError):
                validate_section_directions(new, old)
        validate_section_directions([{**old[0],'direction_locked':False}], old, ['chorus'])

    def test_trace_preserves_literal_notes_and_declares_no_engine_route(self):
        spec = {'_lyrics_document':{'sections':[{'id':'chorus','type':'CORO','direction':'Crece sin batería','energy':'Máxima'}]}}
        trace = section_direction_trace(spec)[0]
        self.assertEqual(trace['requested'], {'direction':'Crece sin batería','energy':'Máxima'})
        self.assertEqual(trace['route'], 'retained_not_sent_to_engine')
        self.assertEqual(trace['transformations'], [])
