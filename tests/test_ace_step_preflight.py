import sys
import tempfile
import unittest
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from adapters.ace_step_preflight import AceStepPreflight


class PreflightTest(unittest.TestCase):
    def test_missing_empty_wrong_architecture_and_presence_only(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            model = root / "data/models/music/acestep-1.5-2b-turbo"
            config = model / "acestep-v15-base/config.json"
            item = {"plan": {"retained_spec": {"ace_step_config": "acestep-v15-base"}}}
            check = AceStepPreflight(root)
            with self.assertRaisesRegex(ValueError, "Faltan archivos"):
                check.inspect_plan(item)
            for relative in ("tools/acestep_generate.py", ".venv/Scripts/python.exe",
                "data/models/music/acestep-1.5-2b-turbo/acestep-v15-base/config.json",
                "data/models/music/acestep-1.5-2b-turbo/acestep-v15-base/model.safetensors",
                "data/models/music/acestep-1.5-2b-turbo/vae/config.json",
                "data/models/music/acestep-1.5-2b-turbo/vae/diffusion_pytorch_model.safetensors",
                "data/models/music/acestep-1.5-2b-turbo/Qwen3-Embedding-0.6B/config.json",
                "data/models/music/acestep-1.5-2b-turbo/Qwen3-Embedding-0.6B/model.safetensors"):
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("placeholder")
            config.write_text(json.dumps({"architectures": ["OtherModel"]}))
            with self.assertRaisesRegex(ValueError, "arquitectura"):
                check.inspect_plan(item)
            config.write_text(json.dumps({"architectures": ["AceStepConditionGenerationModel"]}))
            evidence = check.inspect_plan(item)
            self.assertTrue(evidence["required_files_present"])
            self.assertFalse(evidence["model_loaded_verified"])
            self.assertFalse(evidence["weights_checksum_verified"])
            (model / "acestep-v15-base/model.safetensors").write_bytes(b"")
            with self.assertRaisesRegex(ValueError, "Faltan archivos"):
                check.inspect_plan(item)
