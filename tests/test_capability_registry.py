import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from application.capability_registry import Capability, CapabilityRegistry


class CapabilityRegistryTest(unittest.TestCase):
    def test_configuration_does_not_authorize_execution(self):
        registry = CapabilityRegistry([Capability("song.generate", "ace_step", True, None)])
        with self.assertRaisesRegex(ValueError, "not verified"):
            registry.require_verified("song.generate")

    def test_unknown_and_duplicate_capabilities_are_rejected(self):
        item = Capability("song.generate", "ace_step", True, True)
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            CapabilityRegistry([item, item])
        with self.assertRaisesRegex(ValueError, "not verified"):
            CapabilityRegistry([item]).require_verified("unknown")

    def test_verification_requires_availability(self):
        with self.assertRaisesRegex(ValueError, "requires"):
            CapabilityRegistry([Capability("song.generate", "ace_step", True, None, verified=True)])
        item = Capability("song.generate", "ace_step", True, True, verified=True)
        self.assertEqual(CapabilityRegistry([item]).require_verified(item.identifier), item)
