import sys
from pathlib import Path
import tempfile
import unittest
import ast
import subprocess
from types import SimpleNamespace
from unittest.mock import patch
from urllib.error import URLError

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from adapters.ui_control_audit import ControlParser
from adapters.runtime_probe import probe_runtime
from adapters.acestep_api_audit import compare_signature
from adapters.parameter_audit import audit_parameters
from adapters.acestep_import_probe import probe_acestep_import


class RuntimeAuditTest(unittest.TestCase):
    def test_import_timeout_is_distinct_from_invalid_payload(self):
        with patch("adapters.acestep_import_probe.subprocess.run", side_effect=subprocess.TimeoutExpired("probe", 60)):
            self.assertEqual(probe_acestep_import(Path("."))["status"], "timeout")
        with patch("adapters.acestep_import_probe.subprocess.run", return_value=SimpleNamespace(returncode=0, stdout="not json")):
            self.assertEqual(probe_acestep_import(Path("."))["status"], "invalid_payload")

    def test_import_success_never_verifies_generation(self):
        process = SimpleNamespace(returncode=0, stdout='{"status":"imported","import_verified":true,"generation_verified":true}')
        with patch("adapters.acestep_import_probe.subprocess.run", return_value=process):
            result = probe_acestep_import(Path("."))
        self.assertTrue(result["import_verified"])
        self.assertFalse(result["generation_verified"])

    def test_key_occurrence_does_not_verify_audio_effect(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "frontend").mkdir()
            (root / "backend" / "application").mkdir(parents=True)
            (root / "frontend" / "index.html").write_text('<input v-model="voice.vibrato" />', encoding="utf-8")
            (root / "backend" / "application" / "renderer.py").write_text("value = data.get('vibrato')", encoding="utf-8")
            record = audit_parameters(root)[0]
        self.assertEqual(record["status"], "candidate_reads")
        self.assertFalse(record["audio_effect_verified"])

    def test_signature_rejects_extra_and_missing_parameters(self):
        method = ast.parse("def generate_music(self, captions, lyrics=''):\n    pass").body[0]
        call = ast.parse("handler.generate_music(unknown=1)").body[0].value
        result = compare_signature(method, [call])
        self.assertFalse(result["signature_compatible"])
        self.assertEqual(result["unsupported_keywords"], ["unknown"])
        self.assertEqual(result["missing_required"], ["captions"])

    def test_signature_match_does_not_verify_execution(self):
        method = ast.parse("def generate_music(self, captions, lyrics=''):\n    pass").body[0]
        call = ast.parse("handler.generate_music(captions='idea')").body[0].value
        result = compare_signature(method, [call])
        self.assertTrue(result["signature_compatible"])
        self.assertFalse(result["execution_verified"])

    def test_binding_is_not_proof_of_processing(self):
        parser = ControlParser()
        parser.feed('<input v-model.number="stem.level" @input="markDirty(\'instrumental\')" />')
        control = parser.controls[0]
        self.assertEqual(control["status"], "PARTIAL")
        self.assertEqual(control["engine"], "unverified")
        self.assertEqual(control["bindings"]["v-model.number"], "stem.level")

    def test_remote_servers_are_never_contacted(self):
        with tempfile.TemporaryDirectory() as folder:
            with patch("adapters.runtime_probe.subprocess.run", side_effect=OSError), patch("adapters.runtime_probe.build_opener") as opener:
                report = probe_runtime(Path(folder), {"qwen": "https://example.com"})
        opener.return_value.open.assert_not_called()
        self.assertIsNone(report["servers"]["qwen"]["available"])

    def test_local_probe_failure_is_evidence_not_inference(self):
        with tempfile.TemporaryDirectory() as folder:
            with patch("adapters.runtime_probe.subprocess.run", side_effect=OSError), patch("adapters.runtime_probe.build_opener") as opener:
                opener.return_value.open.side_effect = URLError("offline")
                report = probe_runtime(Path(folder), {"gemma": "http://127.0.0.1:8081"})
        self.assertFalse(report["servers"]["gemma"]["available"])
        self.assertFalse(report["servers"]["gemma"]["inference_verified"])
