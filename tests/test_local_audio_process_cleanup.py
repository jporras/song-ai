"""Real disposable child processes; these tests do not load ACE-Step or a GPU."""
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'backend'))
from application.local_audio_process_service import LocalAudioProcessService
from application.audio_cancellation import AudioCancelled
from audio.ace_step_profiles import resolve_ace_step_profile


class LocalAudioProcessCleanupTest(unittest.TestCase):
    def test_cancel_and_monitor_failure_reap_actual_child_before_model_restore(self):
        for reason in ('cancel', 'monitor_failure'):
            with self.subTest(reason=reason), tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as folder:
                root = Path(folder)
                caption, lyrics = root/'caption.txt', root/'lyrics.md'
                caption.write_text('QA', encoding='utf-8')
                lyrics.write_text('QA', encoding='utf-8')
                service = LocalAudioProcessService(Mock(data_dir=root))
                service.resource_monitor = Mock()
                service.resource_monitor.prepare_for_audio.return_value = {'readiness': {'ready': True}}
                service.resource_monitor.capture.side_effect = RuntimeError('monitor failure')
                original_popen = subprocess.Popen
                children = []

                def launch(*args, **kwargs):
                    process = original_popen(*args, **kwargs)
                    if args[0][0] == sys.executable:
                        children.append(process)
                    return process

                def restore(**kwargs):
                    self.assertEqual(len(children), 1)
                    self.assertIsNotNone(children[0].poll())

                service.resource_monitor.restore_text_models.side_effect = restore
                cancellation = Mock(side_effect=[None, AudioCancelled('cancel')]) if reason == 'cancel' else None
                error_type = AudioCancelled if reason == 'cancel' else RuntimeError
                try:
                    with patch('application.local_audio_process_service.subprocess.Popen', side_effect=launch):
                        with self.assertRaises(error_type):
                            service._run_command({'id': 'qa', 'spec': {}}, root, caption, lyrics,
                                root/'unused.wav', root/'generation.log', root/'diagnostics.json',
                                resolve_ace_step_profile('turbo'),
                                process_arguments=[sys.executable, '-c', 'import time; time.sleep(60)'],
                                cancellation_check=cancellation)
                    service.resource_monitor.restore_text_models.assert_called_once()
                    self.assertFalse((root/'unused.wav').exists())
                finally:
                    for child in children:
                        if child.poll() is None:
                            child.kill()
                            child.wait(timeout=15)
