import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from adapters.ace_step_steering import AceStepSteering
from providers.registry import ProviderRegistry
from application.song_service import SongService
from core.storage import StorageManager


class AceStepSteeringTest(unittest.TestCase):
    def test_qwen_handoff_persists_contract_revision_in_task(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as folder:
            storage = StorageManager(Path(folder))
            service = SongService(storage)
            service.bootstrap()
            snapshot = AceStepSteering(ROOT).snapshot("qwen")
            evidence = {key: value for key, value in snapshot.items() if key != "prompt_context"}
            with patch.object(service.provider_registry, "technical_with_active_provider", return_value={
                "mode": "llama_cpp", "summary": "Revisar idioma vocal", "engine_steering": evidence,
            }):
                service.model_orchestrator.run_handoff({"model_role": "technical", "task_type": "review_song_spec",
                    "project_id": "project-test", "project_name": "Mi cancion", "context": {"language": "es"}})
            result = storage.list_tasks()[0]["result"]
            self.assertEqual(result["engine_steering"]["revision"], snapshot["revision"])

    def test_gemma_context_revision_is_recorded_in_sqlite(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as folder:
            storage = StorageManager(Path(folder))
            service = SongService(storage)
            service.bootstrap()
            provider = Mock()
            provider.interpret.return_value = {"mode": "llama_cpp", "summary": "Revisa tu idea"}
            service.provider_registry.interpreter_providers = [provider]
            readiness = {"missing": [], "recommendations": ["Preparar idea"]}
            service._run_gemma_or_fallback("Proyecto", readiness, set_id="set-test")
            events = storage.list_project_phase_events("set-test")
            event = next(item for item in events if item["event_type"] == "ENGINE_STEERING_SUPPLIED")
            self.assertEqual(event["after"]["engine_steering"]["revision"], readiness["engine_steering"]["revision"])

    def test_actual_contract_reports_source_support_without_verifying_audio(self):
        snapshot = AceStepSteering(ROOT).snapshot("qwen")
        self.assertEqual(snapshot["runtime"]["wrapper_tasks"], ["complete", "cover", "extract", "lego", "repaint", "text2music"])
        self.assertFalse(snapshot["runtime"]["generation_verified"])
        self.assertEqual(snapshot["runtime"]["missing_structured_music_fields"], [])
        self.assertIn("create_sample", snapshot["prompt_context"])
        self.assertEqual(len(snapshot["revision"]), 64)

    def test_both_roles_receive_contract_and_project_context(self):
        registry = ProviderRegistry(steering=AceStepSteering(ROOT))
        provider = Mock()
        provider.interpret.return_value = {"summary": "propuesta", "mode": "test"}
        registry.interpreter_providers = registry.technical_providers = [provider]
        for role, call in (("gemma", registry.interpret_with_active_provider),
                           ("qwen", registry.technical_with_active_provider)):
            result = call("Proyecto activo: balada en espanol", "review")
            prompt = provider.interpret.call_args.args[0]
            self.assertIn("Contrato ACE-Step", prompt)
            self.assertIn("Proyecto activo: balada en espanol", prompt)
            self.assertEqual(result["engine_steering"]["role"], role)
            self.assertNotIn("prompt_context", result["engine_steering"])

    def test_document_updates_are_loaded_without_restarting_and_missing_contract_fails(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "docs" / "steering").mkdir(parents=True)
            (root / "tools").mkdir()
            document = root / "docs" / "ACE_STEP_CAPABILITIES.md"
            document.write_text("<!-- MODEL_STEERING_START -->version A<!-- MODEL_STEERING_END -->", encoding="utf-8")
            (root / "docs" / "steering" / "GEMMA_SONG_ROLE.md").write_text("Rol Gemma", encoding="utf-8")
            (root / "tools" / "acestep_generate.py").write_text("handler.generate_music(task_type='text2music')", encoding="utf-8")
            legacy = root / "data" / "models" / "music" / "acestep-1.5-3.5b-default" / "snapshot"
            legacy.mkdir(parents=True)
            (legacy / "config.json").write_text("{}", encoding="utf-8")
            turbo = root / "data" / "models" / "music" / "turbo" / "acestep-v15-turbo"
            turbo.mkdir(parents=True)
            (turbo / "config.json").write_text("{}", encoding="utf-8")
            steering = AceStepSteering(root)
            first = steering.snapshot("gemma")
            self.assertEqual(first["runtime"]["model_config_inventory"]["base"], [])
            self.assertEqual(len(first["runtime"]["model_config_inventory"]["turbo"]), 1)
            document.write_text(document.read_text().replace("version A", "version B"), encoding="utf-8")
            second = steering.snapshot("gemma")
            self.assertNotEqual(first["revision"], second["revision"])
            self.assertIn("version B", second["prompt_context"])
            document.write_text("Sin contrato", encoding="utf-8")
            with self.assertRaises(ValueError):
                steering.snapshot("gemma")
