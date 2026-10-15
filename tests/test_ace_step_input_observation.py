import unittest
from copy import deepcopy
from unittest.mock import Mock,patch
from pathlib import Path

from adapters.ace_step_input_observation import inspect_input_observation
from adapters.ace_step_candidate_runner import AceStepCandidateRunner
from audio.ace_step_profiles import BASE_PROFILE


class InputObservationTest(unittest.TestCase):
    def test_revision_hash_values_coverage_and_audio_checksum_are_bound(self):
        plan={'spec_revision_id':'r1','plan_sha256':'h1','payload':{'bpm':97,'src_audio':'audio.wav'},
              'input_trace':{'entries':[{'target':'src_audio','verification_status':'verified_project_audio_artifact','audio_sha256':'audio-hash'}]}}
        trace={'schema_version':'runtime_inputs_v1','status':'approved_inputs_match',
               'spec_revision_id':'r1','plan_sha256':'h1','entries':[
                   {'field':field,'approved_value':value,'wrapper_value':value,
                    'transformation':'approved_request_identity_v1'} for field,value in plan['payload'].items()]}
        trace['entries'][1]['verified_audio_sha256']='audio-hash'
        self.assertTrue(inspect_input_observation(trace,plan)['matches_approved_plan'])
        changed=[]
        for key in ('spec_revision_id','plan_sha256','schema_version'):
            item=deepcopy(trace);item[key]='other';changed.append(item)
        for key in ('approved_value','wrapper_value','transformation'):
            item=deepcopy(trace);item['entries'][0][key]='other';changed.append(item)
        item=deepcopy(trace);item['entries'].append(item['entries'][0]);changed.append(item)
        item=deepcopy(trace);item['entries'][1]['verified_audio_sha256']='other';changed.append(item)
        for item in changed:
            self.assertEqual(inspect_input_observation(item,plan)['status'],'mismatch')
        self.assertEqual(inspect_input_observation(None,plan)['status'],'unavailable')
        self.assertEqual(inspect_input_observation(trace,None)['status'],'plan_not_compared')

    def test_runner_rejects_missing_or_mismatched_trace_before_returning_candidate(self):
        runner=AceStepCandidateRunner(Mock())
        with patch('adapters.ace_step_candidate_runner.AceStepPreflight'), \
             patch('adapters.ace_step_candidate_runner.AceStepExecutionArguments') as arguments, \
             patch('adapters.ace_step_candidate_runner.read_candidate_runtime') as read:
            arguments.return_value.build.return_value=[]
            for status in ('unavailable','mismatch'):
                read.return_value={'input_observation':{'status':status}}
                with self.assertRaisesRegex(ValueError,'traza'):
                    runner.run({}, {'plan':{}},BASE_PROFILE,Path('dir'),Path('out'),Mock())
            read.return_value={'input_observation':{'status':'matched'},'quality_verified':False}
            self.assertEqual(runner.run({}, {'plan':{}},BASE_PROFILE,Path('dir'),Path('out'),Mock()),read.return_value)
