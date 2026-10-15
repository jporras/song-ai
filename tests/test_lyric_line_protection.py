import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'backend'))
from application.lyric_line_protection import validate_line_protection


class LineProtectionTests(unittest.TestCase):
    def test_protected_literal_and_position_require_explicit_unlock(self):
        old = [{'id':'verse', 'text':'Mi Alma\nOtra línea', 'protected_lines':[0]}]
        validate_line_protection(old, [{'id':'verse','text':'Mi Alma\nNueva línea','protected_lines':[0]}], [])
        for incoming in ([], [{'id':'verse','text':'Otra voz\nOtra línea','protected_lines':[0]}], [{'id':'verse','text':'Mi Alma\nOtra línea','protected_lines':[]}]):
            with self.assertRaises(ValueError):
                validate_line_protection(old, incoming, [])
        validate_line_protection(old, [{'id':'verse','text':'Otra voz','protected_lines':[]}], ['verse:0'])

    def test_invalid_indexes_and_forged_unlock_rejected(self):
        for indexes in ([True], [-1], [2], [0,0]):
            with self.assertRaises(ValueError):
                validate_line_protection([], [{'id':'v','text':'One','protected_lines':indexes}], [])
        with self.assertRaises(ValueError):
            validate_line_protection([], [], ['forged:0'])
