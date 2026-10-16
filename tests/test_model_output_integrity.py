import sys
import unittest
from io import BytesIO
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch
from urllib.error import HTTPError
from urllib.request import Request

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from providers.llamacpp import LlamaCppClient, LlamaCppError
from providers.song_spec_schema import proposal_schema
from application.song_specification_service import SongSpecificationService
from audio.resource_monitor import ResourceMonitor
from application.song_service import SongService


class ModelOutputIntegrityTest(unittest.TestCase):
    def test_llama_http_error_preserves_context_limit_diagnostic(self):
        settings = SimpleNamespace(llama_cpp_base_url="http://localhost:8081",
            llama_cpp_timeout_seconds=5)
        client = LlamaCppClient(settings)
        error = HTTPError('http://localhost:8081/completion', 400, 'Bad Request', {},
                          BytesIO(b'{"error":{"message":"request (11906 tokens) exceeds the available context size (8192 tokens)"}}'))
        with patch('providers.llamacpp.urlopen', side_effect=error):
            with self.assertRaisesRegex(LlamaCppError, '11906 tokens.*8192 tokens'):
                client._request_json(Request('http://localhost:8081/completion'))

    def test_decoding_uses_actual_catalog_types_including_tempo_time_and_tracks(self):
        import json
        catalog = SongSpecificationService().catalog({'task_type': 'text2music'})
        fields = {field['id']: field for group in catalog['groups'] for field in group['fields']}
        schema = proposal_schema(json.dumps({'context': {'current_spec': {}, 'fields': fields}}))
        properties = schema['properties']['spec']['properties']
        self.assertEqual(properties['sample_duration_seconds']['type'], ['number', 'null'])
        self.assertEqual(properties['bpm']['type'], ['number', 'null'])
        self.assertEqual(properties['structure']['type'], ['array', 'null'])
        self.assertEqual(properties['vocal_layers']['type'], ['array', 'null'])
        self.assertEqual(properties['src_audio'], {'enum': [None]})
        self.assertEqual(properties['voice_profile_id'], {'enum': [None]})

    def test_structured_decode_requires_complete_catalog_and_preserves_fixed_values(self):
        import json
        prompt = 'Steering\nSolicitud y contexto del proyecto:\n' + json.dumps({'context': {
            'current_spec': {'bpm': 72}, 'fields': {'bpm': {'control': 'number'},
            'voice_style': {'control': 'text'}, 'structure': {'control': 'list'}}}})
        schema = proposal_schema(prompt)
        self.assertEqual(schema['properties']['spec']['required'], ['bpm', 'voice_style', 'structure'])
        self.assertEqual(schema['properties']['spec']['properties']['bpm'], {'enum': [72]})
        settings = SimpleNamespace(llama_cpp_base_url='http://localhost', llama_cpp_n_predict=512,
                                   llama_cpp_temperature=0.3)
        client = LlamaCppClient(settings)
        client._post_json = Mock(return_value={'content': '{}'})
        client.complete(prompt, json_schema=schema)
        self.assertEqual(client._post_json.call_args.args[1]['json_schema'], schema)

    def test_healthy_server_does_not_label_failed_inference_as_real(self):
        service = SongService.__new__(SongService)
        service.provider_registry = Mock()
        service.provider_registry.interpret_with_active_provider.side_effect = LlamaCppError("respuesta incompleta")
        service.provider_registry.llama_cpp_status.return_value = {"available": True}
        readiness = {"missing": ["sample/checkpoint"], "recommendations": ["Revisa la propuesta"]}
        message = service._run_gemma_or_fallback("una peticion", readiness)
        self.assertEqual(readiness["assistant_execution"]["mode"], "local_guidance")
        self.assertFalse(readiness["assistant_execution"]["provider_executed"])
        self.assertIn("respuesta incompleta", message)

    def test_incomplete_outputs_are_not_accepted_as_complete(self):
        settings = SimpleNamespace(llama_cpp_base_url="http://localhost:8081",
            llama_cpp_n_predict=512, llama_cpp_temperature=0.3)
        client = LlamaCppClient(settings)
        for marker in ({"stopped_limit": True}, {"truncated": True}, {"stop_type": "limit"}):
            with self.subTest(marker=marker):
                client._post_json = Mock(return_value={"content": "Una frase sin terminar", **marker})
                with self.assertRaisesRegex(LlamaCppError, "incompleta"):
                    client.complete("Propone una letra")
        client._post_json = Mock(return_value={"content": "Una propuesta completa", "stopped_eos": True})
        self.assertEqual(client.complete("Propone una letra"), "Una propuesta completa")

    @patch("audio.resource_monitor.psutil", object())
    @patch("audio.resource_monitor.subprocess.run")
    def test_failed_model_release_blocks_audio_without_waiting_or_claiming_release(self, run):
        monitor = ResourceMonitor.__new__(ResourceMonitor)
        monitor.settings = SimpleNamespace(enabled=True, release_llm_before_audio=True,
            stop_llm_command="close-project-models", audio_start_delay_seconds=45)
        monitor.capture = Mock(side_effect=lambda **kwargs: {"message": kwargs.get("message", "snapshot")})
        run.return_value.returncode = 1
        with patch("audio.resource_monitor.time.sleep") as sleep:
            result = monitor.prepare_for_audio("audio", required_ram_mb=7049)
        self.assertFalse(result["readiness"]["ready"])
        self.assertFalse(result["released_llm"])
        self.assertEqual(result["readiness"]["decision"], "blocked_llm_release")
        sleep.assert_not_called()
