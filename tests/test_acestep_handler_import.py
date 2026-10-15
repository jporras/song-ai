import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

sys.path[:0] = [str(Path(__file__).resolve().parents[1] / name) for name in ('tools', 'backend')]
from acestep_generate import load_acestep_api


class HandlerImportTest(unittest.TestCase):
    def test_imports_handler_without_gradio_pipeline(self):
        handler = object()
        with patch('acestep_generate.importlib.util.find_spec', return_value=object()), patch(
                'acestep_generate.importlib.import_module', return_value=SimpleNamespace(AceStepHandler=handler)) as importer:
            result = load_acestep_api()
        importer.assert_called_once_with('acestep.handler')
        self.assertTrue(result['available'])
        self.assertIs(result['handler_class'], handler)

    def test_missing_dependency_remains_explicit(self):
        error = ModuleNotFoundError('missing', name='dependency')
        with patch('acestep_generate.importlib.util.find_spec', return_value=object()), patch(
                'acestep_generate.importlib.import_module', side_effect=error):
            result = load_acestep_api()
        self.assertFalse(result['available'])
        self.assertEqual(result['kind'], 'missing_dependency')
