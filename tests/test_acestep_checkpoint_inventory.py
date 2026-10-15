import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from adapters.acestep_checkpoint_inventory import COMPONENTS, observe_checkpoint_root


class CheckpointInventoryTest(unittest.TestCase):
    def populate(self, root):
        for name, filenames in COMPONENTS.items():
            directory = root / name
            directory.mkdir()
            for filename in filenames:
                (directory / filename).write_bytes(b'fixture-not-model-weights')
            (directory / 'config.json').write_text(json.dumps({
                'architectures': ['AceStepConditionGenerationModel']}), encoding='utf-8')

    def test_component_failure_disables_only_dependent_routes(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            self.populate(root)
            (root / 'acestep-v15-base' / 'model.safetensors').write_bytes(b'')
            (root / 'acestep-5Hz-lm-0.6B' / 'tokenizer.json').unlink()
            result = observe_checkpoint_root(root)
            routes = result['route_prerequisites']
            self.assertFalse(routes['base']['direct'])
            self.assertTrue(routes['turbo']['direct'])
            self.assertFalse(routes['turbo']['high_level_lm']['acestep-5Hz-lm-0.6B'])
            self.assertTrue(routes['turbo']['high_level_lm']['acestep-5Hz-lm-1.7B'])
            (root / 'vae' / 'config.json').write_text('{broken', encoding='utf-8')
            self.assertFalse(observe_checkpoint_root(root)['route_prerequisites']['turbo']['direct'])

    def test_config_architecture_checked_without_reading_weight_content(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            self.populate(root)
            (root / 'acestep-v15-base' / 'config.json').write_text('{"architectures":null}', encoding='utf-8')
            original = Path.read_bytes
            def bounded_read(path):
                self.assertEqual(path.name, 'config.json')
                return original(path)
            with patch.object(Path, 'read_bytes', bounded_read):
                result = observe_checkpoint_root(root)
            self.assertFalse(result['route_prerequisites']['base']['direct'])
            self.assertTrue(result['route_prerequisites']['turbo']['direct'])
            self.assertFalse(result['loaded_verified'])
            self.assertFalse(result['generation_verified'])
            self.assertFalse(result['weights_checksum_verified'])

    def test_missing_root_does_not_create_or_download_models(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder) / 'absent'
            result = observe_checkpoint_root(root)
            self.assertFalse(root.exists())
            self.assertFalse(result['route_prerequisites']['turbo']['direct'])
