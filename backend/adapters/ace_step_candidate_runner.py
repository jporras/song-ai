"""Reuse the existing monitored process runner for isolated candidate outputs."""
from adapters.ace_step_execution import AceStepExecutionArguments
from adapters.ace_step_preflight import AceStepPreflight
from pathlib import Path


class AceStepCandidateRunner:
    def __init__(self, process_service):
        self.process_service = process_service

    def run(self, project, item, profile, directory, output, revalidate, cancellation_check=None):
        AceStepPreflight(Path(__file__).resolve().parents[2]).inspect_plan(item)
        argv = AceStepExecutionArguments().build(item, profile, self.process_service._python_executable(), directory, output)
        argv.extend(("--output-type", "exploratory_candidate"))
        self.process_service._run_command(project, directory, directory / "ace_plan_caption.txt",
            directory / "ace_plan_lyrics.md", output, directory / "generation.log",
            directory / "ace_step_diagnostics.json", profile, process_arguments=argv, revalidate=revalidate,
            execution_phase="SONG_SPEC_COLLECTION", cancellation_check=cancellation_check)
