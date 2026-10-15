import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch
import subprocess

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from audio.resource_monitor import ResourceMonitor


class ResourceReadinessTest(unittest.TestCase):
    def setUp(self):
        # Exercise release and budget logic even when the test host lacks psutil.
        psutil_patch = patch('audio.resource_monitor.psutil', object())
        psutil_patch.start()
        self.addCleanup(psutil_patch.stop)

    def monitor(self, release=True, command='stop-owned-models'):
        monitor = ResourceMonitor.__new__(ResourceMonitor)
        monitor.settings = SimpleNamespace(enabled=True, release_llm_before_audio=release,
            stop_llm_command=command, audio_start_delay_seconds=0)
        monitor.capture = Mock(side_effect=lambda **kw: {'message': kw.get('message', 'snapshot')})
        monitor.evaluate = Mock(return_value=SimpleNamespace(ready=True, decision='ready', message='ready', recommendations=[]))
        return monitor

    def test_release_failures_block_before_memory_readiness(self):
        for error in (subprocess.TimeoutExpired('stop', 60), OSError('denied')):
            with self.subTest(error=type(error).__name__):
                monitor = self.monitor()
                with patch('audio.resource_monitor.subprocess.run', side_effect=error):
                    result = monitor.prepare_for_audio('test', required_ram_mb=7049)
                self.assertFalse(result['readiness']['ready'])
                self.assertFalse(result['released_llm'])
                self.assertEqual(result['readiness']['decision'], 'blocked_llm_release')
                monitor.evaluate.assert_not_called()

    def test_missing_release_command_is_not_claimed_as_success(self):
        monitor = self.monitor(command='')
        with patch('audio.resource_monitor.subprocess.run') as command:
            result = monitor.prepare_for_audio('test')
        command.assert_not_called()
        self.assertFalse(result['released_llm'])
        self.assertFalse(result['readiness']['ready'])

    def test_disabled_release_still_checks_budget_without_claiming_release(self):
        monitor = self.monitor(release=False)
        result = monitor.prepare_for_audio('test', required_ram_mb=7049)
        self.assertFalse(result['released_llm'])
        monitor.evaluate.assert_called_once_with(result['snapshot'], 7049)

    def test_exit_code_controls_release_and_budget_is_checked_after_success(self):
        for code in (0, 1):
            with self.subTest(code=code):
                monitor = self.monitor()
                with patch('audio.resource_monitor.subprocess.run', return_value=SimpleNamespace(returncode=code)):
                    result = monitor.prepare_for_audio('test', required_ram_mb=7049)
                self.assertEqual(result['released_llm'], code == 0)
                self.assertEqual(result['readiness']['ready'], code == 0)
                if code == 0:
                    monitor.evaluate.assert_called_once_with(result['snapshot'], 7049)
                else:
                    monitor.evaluate.assert_not_called()

    def test_configured_ram_minimum_blocks_and_boundary_is_allowed(self):
        monitor = ResourceMonitor.__new__(ResourceMonitor)
        monitor.settings = SimpleNamespace(min_free_ram_mb_for_audio=3500, min_free_disk_mb_for_audio=15000,
                                          max_cpu_percent_before_audio=85)
        monitor.recommendations = Mock(return_value=["Libera memoria"])
        snapshot = {"ram_available_mb": 2282, "cpu_percent": 10, "disk_data_free_mb": 20000,
                    "disk_models_free_mb": 20000, "disk_cache_free_mb": 20000}
        blocked = monitor.evaluate(snapshot)
        self.assertFalse(blocked.ready)
        self.assertEqual(blocked.decision, "blocked_ram")
        self.assertIn("Libera memoria", blocked.message)
        self.assertTrue(monitor.evaluate({**snapshot, "ram_available_mb": 3500}).ready)
        self.assertFalse(monitor.evaluate({**snapshot, "ram_available_mb": 3500}, required_ram_mb=8000).ready)
        self.assertTrue(monitor.evaluate({**snapshot, "ram_available_mb": 8000}, required_ram_mb=8000).ready)
