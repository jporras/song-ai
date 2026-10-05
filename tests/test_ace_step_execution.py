import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from adapters.ace_step_execution import AceStepExecutionArguments
from audio.ace_step_profiles import resolve_ace_step_profile
from application.professional_full_song_service import ProfessionalFullSongService
from application.audio_cancellation import AudioCancelled


class ExecutionArgumentsTest(unittest.TestCase):
    def test_negative_resource_readiness_blocks_process_and_restores_models(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            caption, lyrics = root / "caption.txt", root / "lyrics.md"
            caption.write_text("Idea", encoding="utf-8")
            lyrics.write_text("Letra", encoding="utf-8")
            service = ProfessionalFullSongService(Mock(data_dir=root), command_template="python tools/acestep_generate.py")
            service.resource_monitor = Mock()
            service.resource_monitor.prepare_for_audio.return_value = {"readiness": {"ready": False, "message": "Memoria insuficiente"}}
            with patch("application.professional_full_song_service.subprocess.Popen") as process:
                with self.assertRaisesRegex(ValueError, "recursos suficientes"):
                    service._run_command({"id": "song", "spec": {}}, root, caption, lyrics, root / "out.wav",
                        root / "run.log", root / "diag.json", resolve_ace_step_profile("base"), process_arguments=["python", "wrapper.py"])
                process.assert_not_called()
            service.resource_monitor.restore_text_models.assert_called_once()
    def test_running_cancel_stops_process_and_restores_models(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            caption, lyrics = root / "caption.txt", root / "lyrics.md"
            caption.write_text("Idea", encoding="utf-8")
            lyrics.write_text("Letra", encoding="utf-8")
            store = Mock(data_dir=root)
            service = ProfessionalFullSongService(store, command_template="python tools/acestep_generate.py")
            service.resource_monitor = Mock()
            service.resource_monitor.prepare_for_audio.return_value = {"readiness": {}}
            process = Mock()
            process.poll.return_value = None
            cancel = Mock(side_effect=[None, AudioCancelled("Cancelado")])
            with patch("application.professional_full_song_service.subprocess.Popen", return_value=process), patch.object(service, "_terminate_process") as stop:
                with self.assertRaises(AudioCancelled):
                    service._run_command({"id": "song", "spec": {}}, root, caption, lyrics, root / "out.wav",
                                         root / "run.log", root / "diag.json", resolve_ace_step_profile("base"),
                                         process_arguments=["python", "wrapper.py"], cancellation_check=cancel)
                stop.assert_called_once_with(process)
            service.resource_monitor.restore_text_models.assert_called_once()
    def test_process_receives_arguments_without_shell(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            caption, lyrics = root / "caption.txt", root / "lyrics.md"
            caption.write_text("Idea", encoding="utf-8")
            lyrics.write_text("Letra", encoding="utf-8")
            store = Mock()
            store.data_dir = root
            service = ProfessionalFullSongService(store, command_template="python tools/acestep_generate.py")
            service.resource_monitor = Mock()
            service.resource_monitor.prepare_for_audio.return_value = {"readiness": {}}
            process = Mock()
            process.poll.return_value = 0
            argv = ["python", "tools/acestep_generate.py", "--prompt", str(caption)]
            with patch("application.professional_full_song_service.subprocess.Popen", return_value=process) as popen:
                service._run_command({"id": "song", "spec": {}}, root, caption, lyrics, root / "out.wav",
                                     root / "run.log", root / "diag.json", resolve_ace_step_profile("base"), process_arguments=argv)
            self.assertEqual(popen.call_args.args[0], argv)
            self.assertFalse(popen.call_args.kwargs["shell"])
            service.resource_monitor.restore_text_models.assert_called_once()

    def test_inputs_are_literal_arguments_and_text_is_in_files(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            item = {"effective_status": "approved", "inputs_current": True,
                    "plan": {"retained_spec": {"ace_step_config": "acestep-v15-base"},
                    "payload": {"task_type": "cover", "captions": 'idea & echo secret', "lyrics": 'texto $(command)',
                                "bpm": 72, "src_audio": "source & name.wav", "audio_cover_strength": .5}}}
            argv = AceStepExecutionArguments().build(item, resolve_ace_step_profile("base"), "python", root, root / "out.wav")
            self.assertEqual(argv[argv.index("--src-audio") + 1], "source & name.wav")
            self.assertEqual((root / "ace_plan_caption.txt").read_text(), 'idea & echo secret')
            self.assertEqual((root / "ace_plan_lyrics.md").read_text(), 'texto $(command)')
            self.assertNotIn('idea & echo secret', argv)
            for update in ({"effective_status": "stale"}, {"inputs_current": False}):
                with self.assertRaises(ValueError):
                    AceStepExecutionArguments().build({**item, **update}, resolve_ace_step_profile("base"), "python", root, root / "out.wav")
            with self.assertRaises(ValueError):
                AceStepExecutionArguments().build(item, resolve_ace_step_profile("turbo"), "python", root, root / "out.wav")
