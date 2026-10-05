import sys
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path
from unittest.mock import Mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from adapters.ace_step_source_audio import AceStepSourceAudio
from application.ace_step_plan_compiler import PreviewAceStepPlan
from tests import test_ace_step_plan_compiler
from tests.test_sample_audio_evidence import write_audio


class SourceAudioTest(unittest.TestCase):
    def test_integrity_ownership_path_and_truncation(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            directory = root / "projects" / "song1"
            directory.mkdir(parents=True)
            audio = directory / "source.wav"
            write_audio(audio)
            project = {"id": "song1", "artifacts": [{"artifact_id": "a1", "song_id": "song1", "file_path": str(audio)}]}
            inspector = AceStepSourceAudio(root)
            evidence = inspector.inspect(project, "a1", str(audio))
            self.assertEqual(evidence["duration_seconds"], .1)
            self.assertFalse(evidence["musical_quality_verified"])
            for artifact, path in (("other", str(audio)), ("a1", str(root / "other.wav"))):
                with self.assertRaises(ValueError):
                    inspector.inspect(project, artifact, path)
            foreign = deepcopy(project)
            foreign["artifacts"][0]["song_id"] = "other"
            with self.assertRaises(ValueError):
                inspector.inspect(foreign, "a1", str(audio))
            outside = root / "outside.wav"
            write_audio(outside)
            project["artifacts"][0]["file_path"] = str(outside)
            with self.assertRaises(ValueError):
                inspector.inspect(project, "a1", str(outside))
            project["artifacts"][0]["file_path"] = str(audio)
            audio.write_bytes(audio.read_bytes()[:-2])
            with self.assertRaisesRegex(ValueError, "incompleto"):
                inspector.inspect(project, "a1", str(audio))

    def test_preview_binds_checksum_and_checks_real_interval(self):
        fixture = test_ace_step_plan_compiler.AceStepPlanCompilerTest()
        fixture.setUp()
        record = fixture.record
        record["json_spec"].update(task_type="repaint", src_audio="source.wav", source_artifact_id="a1",
                                   repainting_start=1, repainting_end=3)
        store = Mock()
        store.get_song_project.return_value = {"id": "song1", "spec": record}
        inspector = Mock()
        inspector.inspect.return_value = {"duration_seconds": 4, "sha256": "checksum"}
        preview = PreviewAceStepPlan(store, inspector)
        plan = preview.execute("song1", "Letra")
        self.assertEqual(plan["source_audio_evidence"]["sha256"], "checksum")
        self.assertNotIn("source_artifact_verification", plan["pending"])
        self.assertFalse(plan["ready_for_execution"])
        old_hash = plan["plan_sha256"]
        inspector.inspect.return_value = {"duration_seconds": 4, "sha256": "replaced"}
        self.assertNotEqual(preview.execute("song1", "Letra")["plan_sha256"], old_hash)
        for start, end in ((4, -1), (1, 5)):
            record["json_spec"].update(repainting_start=start, repainting_end=end)
            with self.assertRaisesRegex(ValueError, "duracion"):
                preview.execute("song1", "Letra")
        store.create_song_artifact.assert_not_called()
