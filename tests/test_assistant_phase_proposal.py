import sys
import unittest
from unittest.mock import Mock
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'backend'))
from application.assistant_phase_proposal import validate_assistant_revision, bind_phase_proposal, reviewed_proposal_trace, reviewed_proposal_batch


class AssistantPhaseProposalTest(unittest.TestCase):
    def test_unrelated_placeholder_proposal_does_not_supersede_original(self):
        proposals = [bind_phase_proposal({'available':True,'phase':'lyrics','changes':{'placeholders':value}}, self.project, str(value))
                     for value in ({'name':'Alma'}, {'occasion':'noche'})]
        traces = reviewed_proposal_batch(proposals, proposals, 'lyrics', {'lyrics':{'placeholders':{'name':'Alma','occasion':'noche'}}})
        self.assertEqual(traces[0]['decisions']['placeholders']['review_result'], 'accepted')
    def test_batch_distinguishes_later_proposal_from_manual_change(self):
        proposals = [bind_phase_proposal({'available':True,'phase':'intent','changes':{'bpm':value}}, self.project, str(value)) for value in (109,115)]
        traces = reviewed_proposal_batch(proposals, proposals, 'intent', {'intent':{'bpm':117}})
        self.assertEqual(traces[0]['decisions']['bpm']['review_result'], 'superseded_by_later_proposal')
        self.assertEqual(traces[0]['decisions']['bpm']['superseded_by_application'], 2)
        self.assertEqual(traces[1]['decisions']['bpm']['review_result'], 'user_modified')
        self.assertEqual(traces[1]['decisions']['bpm']['saved_value'], 117)
        self.assertEqual(traces[1]['application_order'], 2)

    def setUp(self):
        self.project = {'set': {'set_id':'alma'}, 'music_spec_revision_id':'r1',
                        'phase_data':{'intent':{'data':{'intent':{'bpm':97}}}}}

    def test_stale_request_rejected_before_inference(self):
        self.assertEqual(validate_assistant_revision(self.project, 'r1'), 'r1')
        with self.assertRaisesRegex(ValueError, 'Recarga'):
            validate_assistant_revision(self.project, 'r0')
        self.assertEqual(validate_assistant_revision(self.project, None), 'r1')

    def test_proposal_is_traceable_without_confirmation_or_mutation(self):
        patch = {'available':True, 'phase':'intent', 'changes':{'bpm':105}}
        proposal = bind_phase_proposal(patch, self.project, 'Quiero BPM 105')
        self.assertEqual(proposal['source_revision_id'], 'r1')
        self.assertEqual(proposal['source_project_id'], 'alma')
        self.assertEqual(proposal['producer'], 'deterministic_question_parser')
        self.assertEqual(proposal['confirmation'], 'proposed')
        self.assertFalse(proposal['persisted'])
        self.assertEqual(len(proposal['source_phase_sha256']), 64)
        proposal['changes']['bpm'] = 110
        self.assertEqual(patch['changes']['bpm'], 105)
        self.assertEqual(self.project['phase_data']['intent']['data']['intent']['bpm'], 97)

    def test_source_hash_changes_with_persisted_decisions(self):
        patch = {'phase':'intent'}
        first = bind_phase_proposal(patch, self.project, 'Ayuda')
        self.project['phase_data']['intent']['data']['intent']['bpm'] = 101
        second = bind_phase_proposal(patch, self.project, 'Ayuda')
        self.assertNotEqual(first['source_phase_sha256'], second['source_phase_sha256'])

    def test_service_rejects_stale_revision_without_model_call(self):
        from application.song_service import SongService
        service = SongService.__new__(SongService)
        service.storage = Mock()
        service.model_orchestrator = Mock()
        service.model_orchestrator.active_audio_task.return_value = None
        service.get_project = Mock(return_value=self.project)
        service._run_gemma_or_fallback = Mock()
        with self.assertRaisesRegex(ValueError, 'Recarga'):
            service.gemma_assistant({'set_id':'alma', 'spec_revision_id':'r0'})
        service._run_gemma_or_fallback.assert_not_called()
        service.model_orchestrator.review_sqlite_project_state.assert_not_called()

    def test_review_records_accepted_and_user_modified_values(self):
        proposal = bind_phase_proposal({'available':True,'phase':'intent','changes':{'bpm':105,'key':'C major'}}, self.project, 'Cambiar')
        trace = reviewed_proposal_trace(proposal, proposal, 'intent', {'intent':{'bpm':105,'key':'D minor'}})
        self.assertEqual(trace['decisions']['bpm']['review_result'], 'accepted')
        self.assertEqual(trace['decisions']['key']['review_result'], 'user_modified')
        self.assertEqual(trace['decisions']['key']['saved_value'], 'D minor')
        self.assertEqual(proposal['confirmation'], 'proposed')

    def test_bpm_question_accepts_both_natural_word_orders(self):
        from application.song_service import SongService
        service = SongService.__new__(SongService)
        for question in ('Quiero 105 BPM', 'Cambia el BPM a 105', 'Cambia BPM: 105'):
            proposal = service._phase_form_patch_from_question(question, 'intent', self.project)
            self.assertEqual(proposal['changes']['bpm'], 105)

    def test_modified_or_stale_proposal_trace_is_rejected(self):
        from copy import deepcopy
        proposal = bind_phase_proposal({'available':True,'phase':'intent','changes':{'bpm':105}}, self.project, 'Cambiar')
        for field, value in [('source_revision_id','r0'), ('changes',{'bpm':222}), ('source_phase_sha256','bad')]:
            changed = deepcopy(proposal)
            changed[field] = value
            with self.assertRaises(ValueError):
                reviewed_proposal_trace(changed, proposal, 'intent', {'intent':{'bpm':105}})
