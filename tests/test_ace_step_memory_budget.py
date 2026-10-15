import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from adapters.ace_step_memory_budget import estimate_ace_step_memory


class MemoryBudgetTest(unittest.TestCase):
    def test_budget_uses_only_selected_and_shared_weights(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            profile = SimpleNamespace(name="base", checkpoint_root="models", config_path="base")
            for path in ("base/model.safetensors", "vae/diffusion_pytorch_model.safetensors", "Qwen3-Embedding-0.6B/model.safetensors"):
                target = root / "models" / path
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(b"x" * 64)
            result = estimate_ace_step_memory(root, profile)
            self.assertEqual(result["weight_files_mb"], 1)
            self.assertEqual(result["required_ram_mb"], 1025)
            self.assertFalse(result["model_load_verified"])
            self.assertFalse(result["measured_working_set"])
            with self.assertRaises(ValueError):
                estimate_ace_step_memory(root, profile, "acestep-5Hz-lm-1.7B")
            lm = root / "models" / "acestep-5Hz-lm-1.7B" / "model.safetensors"
            lm.parent.mkdir()
            lm.write_bytes(b"x" * 1024 * 1024)
            augmented = estimate_ace_step_memory(root, profile, "acestep-5Hz-lm-1.7B")
            self.assertGreater(augmented["required_ram_mb"], result["required_ram_mb"] + 1024)

    def test_missing_weights_never_return_a_budget(self):
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaises(ValueError):
                estimate_ace_step_memory(Path(folder), SimpleNamespace(checkpoint_root="models", config_path="base"))
