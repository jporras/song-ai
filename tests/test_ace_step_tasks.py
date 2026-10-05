import ast
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from models.ace_step_tasks import TASKS, validate_task_inputs
from adapters.acestep_task_audit import wrapper_tasks


class AceStepTasksTest(unittest.TestCase):
    def test_all_six_task_contracts_with_base(self):
        for task in TASKS:
            tracks = ("guitar",) if task in {"lego", "extract", "complete"} else ()
            validate_task_inputs(task, "acestep-v15-base", "source.wav", "guitar", 1, 2, tracks)

    def test_base_tasks_reject_turbo_sft_and_legacy_model(self):
        for task in ("lego", "extract", "complete"):
            for config in ("acestep-v15-turbo", "acestep-v15-sft", "3.5b-default", ""):
                with self.subTest(task=task, config=config), self.assertRaises(ValueError):
                    validate_task_inputs(task, config, "source.wav", "guitar", tracks=("guitar",))

    def test_rejects_missing_source_invalid_interval_or_mismatched_tracks(self):
        with self.assertRaises(ValueError):
            validate_task_inputs("cover", "", "")
        for start, end in ((2, 1), (-1, 2), (float("nan"), 2), (0, float("inf"))):
            with self.assertRaises(ValueError):
                validate_task_inputs("repaint", "", "source.wav", start=start, end=end)
        with self.assertRaises(ValueError):
            validate_task_inputs("lego", "acestep-v15-base", "source.wav", "drums", tracks=("guitar",))

    def test_cli_choices_only_count_when_forwarded(self):
        parser = "parser.add_argument('--task-type', choices=('cover', 'repaint'))\n"
        self.assertEqual(wrapper_tasks(ast.parse(parser)), [])
        self.assertEqual(wrapper_tasks(ast.parse(parser + "handler.generate_music(task_type=args.task_type)")), ["cover", "repaint"])
