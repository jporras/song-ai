import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from adapters.acestep_configuration_audit import audit_acestep_configuration


class ConfigurationAuditTest(unittest.TestCase):
    def test_inspection_does_not_execute_wrapper_or_claim_loaded_configuration(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "tools").mkdir()
            (root / "tools" / "acestep_generate.py").write_text(
                'raise RuntimeError("must not execute")\n'
                'parser.add_argument("--config-path", default=os.getenv("ACESTEP_CONFIG_PATH", "turbo"))\n'
                'def resolve_acestep_v15_config_path(path):\n    return "base"\n', encoding="utf-8")
            report = audit_acestep_configuration(root)
        self.assertIn("ACESTEP_CONFIG_PATH", report["argument_default_expressions"]["--config-path"])
        self.assertEqual(report["resolver_config_candidates"], ["base"])
        self.assertIsNone(report["effective_config"])
        self.assertFalse(report["loaded_verified"])

    def test_missing_wrapper_is_reported(self):
        with tempfile.TemporaryDirectory() as folder:
            self.assertEqual(audit_acestep_configuration(Path(folder))["status"], "wrapper_missing")
