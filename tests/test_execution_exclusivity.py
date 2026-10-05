import sys
import unittest
from pathlib import Path
from unittest.mock import Mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from audio.execution_lock import exclusive_audio, exclusive_planning
from providers.registry import ProviderRegistry


class ExecutionExclusivityTest(unittest.TestCase):
    def test_audio_and_planning_exclude_each_other(self):
        with exclusive_planning():
            with self.assertRaisesRegex(ValueError, "planificacion"):
                with exclusive_audio():
                    self.fail("Audio concurrente")
            with self.assertRaisesRegex(ValueError, "planificacion"):
                with exclusive_planning():
                    self.fail("Planificacion concurrente")
        with exclusive_audio():
            with self.assertRaisesRegex(ValueError, "audio activo"):
                with exclusive_planning():
                    self.fail("Planificacion durante audio")

    def test_registry_holds_lease_for_entire_provider_call_and_releases_on_error(self):
        registry = ProviderRegistry()
        provider = Mock()
        registry.interpreter_providers = [provider]
        def interpret(prompt, target):
            with self.assertRaisesRegex(ValueError, "planificacion"):
                with exclusive_audio():
                    self.fail("Audio durante inferencia")
            raise ValueError("Fallo del provider")
        provider.interpret.side_effect = interpret
        with self.assertRaisesRegex(ValueError, "Fallo del provider"):
            registry.interpret_with_active_provider("Idea", "song")
        with exclusive_audio():
            pass

    def test_acquisition_rechecks_after_preliminary_guard(self):
        registry = ProviderRegistry()
        provider = Mock()
        registry.interpreter_providers = [provider]
        lease = exclusive_audio()
        registry.inference_guard = lambda: lease.__enter__()
        try:
            with self.assertRaisesRegex(ValueError, "audio activo"):
                registry.interpret_with_active_provider("Idea", "song")
            provider.interpret.assert_not_called()
        finally:
            lease.__exit__(None, None, None)
