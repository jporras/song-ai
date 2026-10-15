import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from adapters.ace_step_runtime_evidence import read_candidate_runtime
from audio.ace_step_profiles import BASE_PROFILE
from tests.test_sample_audio_evidence import write_audio


class RuntimeEvidenceTest(unittest.TestCase):
    def test_report_binds_diagnostics_and_audio_without_quality_claim(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            audio = root / "candidate.wav"
            write_audio(audio)
            data = {"schema": "song-ai-ace-step-diagnostics-v1", "status": "completed", "runtime": {
                "ace_step_init": {"enable_generate": True, "config_path": BASE_PROFILE.config_path},
                "requested_device": "xpu", "active_device": "cpu", "fallback_reason": "sin memoria"},
                "output": {"path": str(audio), "exists": True, "size_bytes": audio.stat().st_size},
                "parameters": {"infer_step": 32, "task_type": "text2music"}}
            diagnostic = root / "ace_step_diagnostics.json"
            data['runtime_options_trace'] = {'schema_version':'runtime_options_v1','spec_revision_id':'r1',
                'entries':[{'field':'seed','requested_value':0,'wrapper_value':0,'source':'approved_override'}]}
            data['runtime']['generation_api'] = {'engine_reported_options':{'seed':0}}
            diagnostic.write_text(json.dumps(data), encoding="utf-8")
            report = read_candidate_runtime(root, audio, BASE_PROFILE)
            self.assertEqual(report["status"], "reported_completion")
            self.assertTrue(report["configuration_matches"])
            self.assertEqual(report["active_device"], "cpu")
            self.assertFalse(report["quality_verified"])
            self.assertEqual(report['runtime_options_trace'], data['runtime_options_trace'])
            self.assertEqual(report['generation_api']['engine_reported_options'], {'seed':0})
            self.assertEqual(report['input_observation']['status'],'unavailable')
            plan={'spec_revision_id':'r1','plan_sha256':'hash1','payload':{'bpm':97}}
            trace={'schema_version':'runtime_inputs_v1','status':'approved_inputs_match',
                   'spec_revision_id':'r1','plan_sha256':'hash1','entries':[{'field':'bpm',
                       'approved_value':97,'wrapper_value':97,'transformation':'approved_request_identity_v1'}]}
            data['runtime_input_trace']=trace
            diagnostic.write_text(json.dumps(data),encoding='utf-8')
            bound=read_candidate_runtime(root,audio,BASE_PROFILE,plan)
            self.assertEqual(bound['runtime_input_trace'],trace)
            self.assertTrue(bound['input_observation']['matches_approved_plan'])
            self.assertFalse(bound['quality_verified'])
            trace['spec_revision_id']='foreign-revision'
            diagnostic.write_text(json.dumps(data),encoding='utf-8')
            self.assertEqual(read_candidate_runtime(root,audio,BASE_PROFILE,plan)['input_observation']['status'],'mismatch')
            self.assertEqual(len(report["audio_sha256"]), 64)
            data["runtime"]["ace_step_init"]["config_path"] = "turbo"
            diagnostic.write_text(json.dumps(data), encoding="utf-8")
            self.assertFalse(read_candidate_runtime(root, audio, BASE_PROFILE)["configuration_matches"])
            data["output"]["path"] = str(root / "another.wav")
            diagnostic.write_text(json.dumps(data), encoding="utf-8")
            self.assertEqual(read_candidate_runtime(root, audio, BASE_PROFILE)["status"], "pending")

    def test_missing_malformed_and_check_only_are_not_completion(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            audio = root / "candidate.wav"
            write_audio(audio)
            self.assertEqual(read_candidate_runtime(root, audio, BASE_PROFILE)["status"], "pending")
            for text in ("invalid", "[]", json.dumps({"schema": "song-ai-ace-step-diagnostics-v1", "status": "check_only_completed"})):
                (root / "ace_step_diagnostics.json").write_text(text, encoding="utf-8")
                self.assertEqual(read_candidate_runtime(root, audio, BASE_PROFILE)["status"], "pending")
