import sys
import unittest
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'backend'))
import test_project_consolidation as consolidation_fixture
from application.project_consolidation import ProjectConsolidation
from consolidate_song_projects import resolution
from application.music_spec_phases import SaveMusicSpecPhase, linked_spec, project_phases
from application.song_service import SongService
from application.ace_step_plan_compiler import AceStepPlanCompiler


class MusicSpecPhaseTests(unittest.TestCase):
    def test_saved_protected_unicode_lyrics_reopen_confirm_and_reach_wrapper(self):
        import json
        from core.storage import StorageManager
        from application.music_spec_revision_service import MusicSpecRevisionService
        from adapters.ace_step_execution import AceStepExecutionArguments
        from audio.ace_step_profiles import resolve_ace_step_profile
        project = self.service.get_project(self.set_id)
        data = deepcopy(project['phase_data']['lyrics']['data'])
        section = data['lyricSections'][0]
        section['text'] = 'José, quédate aquí.\nMi canción conserva tu intención.'
        section['protected_lines'] = [0]
        data['lyricsEditor']['content'] = '\n\n'.join(
            f"## {s['type']}\n{s['text'].strip()}" for s in data['lyricSections']).strip()+'\n'
        self.service.save_project_phase_data(self.set_id,'lyrics',
            {'data':data,'spec_revision_id':project['music_spec_revision_id']})
        reopened = StorageManager(self.store.data_dir)
        record = reopened.get_song_project(self.song)['spec']
        self.assertEqual(record['revision']['user_confirmation_status'],'pending')
        changed = deepcopy(data)
        changed['lyricSections'][0]['text'] = 'Otra voz.\nMi canción conserva tu intención.'
        changed['lyricsEditor']['content'] = '\n\n'.join(
            f"## {s['type']}\n{s['text'].strip()}" for s in changed['lyricSections']).strip()+'\n'
        with self.assertRaisesRegex(ValueError,'protegida'):
            self.service.save_project_phase_data(self.set_id,'lyrics',
                {'data':changed,'spec_revision_id':record['revision']['revision_id']})
        self.assertEqual(reopened.get_song_project(self.song)['spec'],record)
        MusicSpecRevisionService(reopened).confirm_song_specification(self.song,
            {'revision_id':record['revision']['revision_id']})
        confirmed = StorageManager(self.store.data_dir).get_song_project(self.song)['spec']
        lyrics = data['lyricsEditor']['content']
        plan = AceStepPlanCompiler().compile(confirmed,lyrics)
        self.assertEqual(plan['lyrics_source'],'confirmed_music_spec_document')
        self.assertIn('lyrics_confirmation',plan['pending'])
        self.assertEqual(plan['payload']['lyrics'],lyrics)
        entry = next(e for e in plan['input_trace']['entries'] if e['target']=='lyrics')
        self.assertEqual(entry['sources'][0]['field'],'_lyrics_document.markdown')
        output = self.store.data_dir/'qa_wrapper'
        AceStepExecutionArguments().build(dict(plan=plan,effective_status='approved',inputs_current=True),
            resolve_ace_step_profile('turbo'),'python',output,output/'out.wav')
        self.assertEqual((output/'ace_plan_lyrics.md').read_text(encoding='utf-8'),lyrics)
        context = json.loads((output/'ace_execution_context.json').read_text(encoding='utf-8'))
        self.assertEqual(context['approved_inputs']['lyrics'],lyrics)
        with self.assertRaisesRegex(ValueError,'no coincide'):
            AceStepPlanCompiler().compile(confirmed,'Otra letra.')

    def test_full_lyrics_task_trace_is_saved_with_reviewed_text_in_same_revision(self):
        project = self.service.get_project(self.set_id)
        data = deepcopy(project['phase_data']['lyrics']['data'])
        original = data['lyricsEditor']['content']
        proposal = {'markdown':original, 'source_project_id':self.song,
                    'source_revision_id':project['music_spec_revision_id']}
        self.store.create_task('task_full_lyrics', 'propose_full_lyrics', 'assistant', {}, 'Propuesta')
        self.store.update_task('task_full_lyrics', 'completed', 100, 'Lista', {'lyrics_proposal':proposal})
        data['lyricSections'][0]['text'] += '\nAlma sonríe al despertar.'
        data['lyricsEditor']['content'] = '\n\n'.join(f"## {s['type']}\n{s['text'].strip()}" for s in data['lyricSections']).strip() + '\n'
        saved = self.service.save_project_phase_data(self.set_id, 'lyrics', {
            'data':data, 'spec_revision_id':project['music_spec_revision_id'],
            'reviewed_full_lyrics_proposal':{'task_id':'task_full_lyrics'}})
        record = self.store.get_song_project(self.song)['spec']
        trace = record['json_spec']['_editor_phases']['lyrics']['reviewed_assistant_proposals'][-1]
        self.assertEqual(trace['proposed_markdown'],original)
        self.assertEqual(trace['review_result'],'user_modified_or_editor_normalized')
        self.assertEqual(trace['confirmation'],'explicit_user_save')
        self.assertEqual(record['json_spec']['_lyrics_document']['markdown'],data['lyricsEditor']['content'])
        self.assertEqual(record['revision']['user_confirmation_status'],'pending')
        self.assertNotEqual(saved['spec_revision_id'],project['music_spec_revision_id'])
        with self.assertRaisesRegex(ValueError,'otra ficha o revisión'):
            self.service.save_project_phase_data(self.set_id, 'lyrics', {
                'data':data, 'spec_revision_id':saved['spec_revision_id'],
                'reviewed_full_lyrics_proposal':{'task_id':'task_full_lyrics'}})
        self.assertEqual(self.store.get_song_project(self.song)['spec'],record)

    def test_section_assistance_receives_assets_without_persisting_proposal(self):
        project = self.service.get_project(self.set_id)
        section = project['phase_data']['lyrics']['data']['lyricSections'][0]
        before = deepcopy(project['music_spec'])
        with patch.object(self.service.provider_registry,'interpret_with_active_provider',return_value={'summary':section['text'],'mode':'test_mock'}) as provider, patch.object(self.service.model_orchestrator,'run_handoff',return_value={'mode':'test_mock'}) as review:
            result = self.service.transform_lyrics_section({'set_id':self.set_id,'section_id':section['id'],
                'section_type':section['type'],'text':section['text'],'section_draft':section,
                'spec_revision_id':project['music_spec_revision_id']})
        prompt = provider.call_args.args[0]
        for role in ('instrumental','melody','lyrics'):
            self.assertIn(project['assets'][role]['asset_id'],prompt)
        self.assertIn('manifest',prompt)
        self.assertIn(project['music_spec_revision_id'],prompt)
        review_context = review.call_args.args[0]['context']
        self.assertEqual(review_context['original_text'],section['text'])
        self.assertEqual(review_context['proposed_text'],result['text'])
        self.assertEqual(review_context['source_spec_revision_id'],project['music_spec_revision_id'])
        self.assertEqual(review_context['project_context']['section']['id'],section['id'])
        self.assertTrue(result['requires_user_save'])
        self.assertEqual(self.service.get_project(self.set_id)['music_spec'],before)

    def test_section_context_uses_actual_project_projection(self):
        from application.lyrics_transform_context import section_transform_context
        project = self.service.get_project(self.set_id)
        section = project['phase_data']['lyrics']['data']['lyricSections'][0]
        context = section_transform_context(project, {'spec_revision_id':project['music_spec_revision_id'],
            'section_id':section['id'],'section_type':section['type'],'text':section['text'],'section_draft':section})
        self.assertEqual(context['project_name'],project['project']['project_name'])
        self.assertEqual(context['spec_revision_id'],project['music_spec_revision_id'])

    def test_section_direction_persists_without_entering_sung_lyrics(self):
        project = self.service.get_project(self.set_id)
        data = deepcopy(project['phase_data']['lyrics']['data'])
        original = data['lyricsEditor']['content']
        data['lyricSections'][0].update(direction='El coro alcanza el clímax',energy='Creciente',vocal_direction='Cálida',instrument_direction='Piano sin batería')
        saved = self.service.save_project_phase_data(self.set_id,'lyrics',{'data':data,'spec_revision_id':project['music_spec_revision_id']})['project']
        restored = self.service.get_project(self.set_id)['phase_data']['lyrics']['data']
        self.assertEqual(restored['lyricSections'][0]['direction'],'El coro alcanza el clímax')
        self.assertEqual(restored['lyricsEditor']['content'],original)
        self.assertNotEqual(saved['music_spec_revision_id'],project['music_spec_revision_id'])
        invalid = deepcopy(restored)
        invalid['lyricSections'][0]['energy'] = 0.9
        with self.assertRaisesRegex(ValueError,'dirección'):
            self.service.save_project_phase_data(self.set_id,'lyrics',{'data':invalid,'spec_revision_id':saved['music_spec_revision_id']})

    def test_line_unlock_is_required_and_recorded_in_saved_revision(self):
        project = self.service.get_project(self.set_id)
        data = deepcopy(project['phase_data']['lyrics']['data'])
        data['lyricSections'][0]['protected_lines'] = [0]
        current = self.service.save_project_phase_data(self.set_id,'lyrics',{'data':data,'spec_revision_id':project['music_spec_revision_id']})['project']
        edited = deepcopy(current['phase_data']['lyrics']['data'])
        edited['lyricSections'][0]['protected_lines'] = []
        request = {'data':edited,'spec_revision_id':current['music_spec_revision_id']}
        with self.assertRaisesRegex(ValueError,'protegida'):
            self.service.save_project_phase_data(self.set_id,'lyrics',request)
        request['unlocked_line_ids'] = [edited['lyricSections'][0]['id'] + ':0']
        saved = self.service.save_project_phase_data(self.set_id,'lyrics',request)['project']
        self.assertEqual(saved['phase_data']['lyrics']['explicit_user_line_unlocks'], request['unlocked_line_ids'])

    def test_section_lock_rejects_text_change_until_explicit_unlock(self):
        project = self.service.get_project(self.set_id)
        data = deepcopy(project['phase_data']['lyrics']['data'])
        data['lyricSections'][0]['locked'] = True
        saved = self.service.save_project_phase_data(self.set_id,'lyrics',{'data':data,'spec_revision_id':project['music_spec_revision_id']})
        current = saved['project']
        edited = deepcopy(current['phase_data']['lyrics']['data'])
        edited['lyricSections'][0]['text'] += '\nNueva línea.'
        edited['lyricsEditor']['content'] = '\n\n'.join(f"## {s['type']}\n{s['text'].strip()}" for s in edited['lyricSections']).strip()+'\n'
        request = {'data':edited,'spec_revision_id':current['music_spec_revision_id']}
        with self.assertRaisesRegex(ValueError,'protegida'):
            self.service.save_project_phase_data(self.set_id,'lyrics',request)
        edited['lyricSections'][0]['locked'] = False
        with self.assertRaisesRegex(ValueError,'protegida'):
            self.service.save_project_phase_data(self.set_id,'lyrics',request)
        request['unlocked_section_ids'] = [edited['lyricSections'][0]['id']]
        result = self.service.save_project_phase_data(self.set_id,'lyrics',request)
        self.assertFalse(result['project']['phase_data']['lyrics']['data']['lyricSections'][0]['locked'])
    def test_multiple_reviewed_proposals_share_one_saved_revision(self):
        from application.assistant_phase_proposal import bind_phase_proposal
        project = self.service.get_project(self.set_id)
        proposals = []
        for bpm in (109,115):
            question = f'Cambia el BPM a {bpm}'
            proposals.append(bind_phase_proposal(self.service._phase_form_patch_from_question(question, 'intent', project), project, question))
        data = deepcopy(project['phase_data']['intent']['data'])
        data['intent']['bpm'] = 117
        request = {'data':data, 'spec_revision_id':project['music_spec_revision_id'], 'reviewed_assistant_proposals':proposals}
        before = self.store.get_song_project(self.song)['spec']
        broken = deepcopy(request)
        broken['reviewed_assistant_proposals'][1]['source_revision_id'] = 'stale'
        with self.assertRaises(ValueError):
            self.service.save_project_phase_data(self.set_id, 'intent', broken)
        self.assertEqual(self.store.get_song_project(self.song)['spec'], before)
        self.service.save_project_phase_data(self.set_id, 'intent', request)
        current = self.store.get_song_project(self.song)['spec']
        traces = current['json_spec']['_editor_phases']['intent']['reviewed_assistant_proposals']
        self.assertEqual([t['changes']['bpm'] for t in traces], [109,115])
        self.assertEqual(traces[0]['decisions']['bpm']['review_result'], 'superseded_by_later_proposal')
        self.assertEqual(traces[1]['decisions']['bpm']['saved_value'], 117)
        self.assertEqual(current['json_spec']['bpm'], 117)

    def test_reviewed_chat_proposal_is_stored_with_user_modified_value(self):
        from application.assistant_phase_proposal import bind_phase_proposal
        project = self.service.get_project(self.set_id)
        question = 'Cambia el BPM a 105'
        proposal = bind_phase_proposal(self.service._phase_form_patch_from_question(question, 'intent', project), project, question)
        self.assertTrue(proposal['available'])
        self.assertEqual(proposal['changes']['bpm'], 105)
        data = deepcopy(project['phase_data']['intent']['data'])
        data['intent']['bpm'] = 101
        saved = self.service.save_project_phase_data(self.set_id, 'intent', {'data':data,
            'spec_revision_id':project['music_spec_revision_id'], 'reviewed_assistant_proposal':proposal})
        record = self.store.get_song_project(self.song)['spec']
        trace = record['json_spec']['_editor_phases']['intent']['reviewed_assistant_proposal']
        self.assertEqual(trace['decisions']['bpm']['review_result'], 'user_modified')
        self.assertEqual(trace['decisions']['bpm']['saved_value'], 101)
        self.assertEqual(record['json_spec']['bpm'], 101)
        self.assertEqual(record['revision']['user_confirmation_status'], 'pending')
        self.assertTrue(saved['changed'])

    def test_emotional_values_reject_invalid_without_writes_and_persist_boundaries(self):
        project = self.service.get_project(self.set_id)
        for value in (-1, 101, True, float('nan'), float('inf'), '50', ''):
            data = deepcopy(project['phase_data']['intent']['data'])
            data['intent']['warmth'] = value
            with self.assertRaisesRegex(ValueError, '0 y 100'):
                self.service.save_project_phase_data(self.set_id, 'intent',
                    {'data':data, 'spec_revision_id':project['music_spec_revision_id']})
            self.assertEqual(self.service.get_project(self.set_id)['music_spec'], project['music_spec'])
        for boundary in (0, 100):
            project = self.service.get_project(self.set_id)
            data = deepcopy(project['phase_data']['intent']['data'])
            data['intent']['warmth'] = boundary
            self.service.save_project_phase_data(self.set_id, 'intent',
                {'data':data, 'spec_revision_id':project['music_spec_revision_id']})
            self.assertEqual(self.service.get_project(self.set_id)['phase_data']['intent']['data']['intent']['warmth'], boundary)

    def setUp(self):
        consolidation_fixture.ProjectConsolidationTests.setUp(self)
        self.song,self.name,self.set_id = self.projects[1]
        ProjectConsolidation(self.store).execute(self.song,resolution(self.store,self.song,self.name))
        self.service = SongService(self.store)

    def test_phase_edit_updates_both_forms_canonical_request_and_assistant_context(self):
        project = self.service.get_project(self.set_id)
        before_archived = self.store.list_project_phase_data(self.set_id)
        data = deepcopy(project['phase_data']['intent']['data'])
        data['intent']['bpm'] = 97
        saved = self.service.save_project_phase_data(self.set_id,'intent',{'data':data,'spec_revision_id':project['music_spec_revision_id']})
        updated = saved['project']
        self.assertEqual(updated['phase_data']['intent']['data']['intent']['bpm'],97)
        self.assertEqual(updated['phase_data']['music-plan']['data']['musicPlan']['bpm'],97)
        self.assertEqual(self.store.list_project_phase_data(self.set_id),before_archived)
        record = self.store.get_song_project(self.song)['spec']
        self.assertEqual(record['revision']['user_confirmation_status'],'pending')
        copy = deepcopy(record)
        copy['revision']['user_confirmation_status'] = 'confirmed'
        lyrics = record['json_spec']['_lyrics_document']['markdown']
        compiled = AceStepPlanCompiler().compile(copy,lyrics)
        self.assertEqual(compiled['payload']['bpm'],97)
        self.assertEqual(compiled['payload']['lyrics'],lyrics)
        with self.assertRaisesRegex(ValueError,'no coincide'):
            AceStepPlanCompiler().compile(copy,'Otra letra.')
        context = self.service._technical_project_context(updated,{})
        self.assertEqual(context['music_spec']['json_spec']['bpm'],97)
        self.assertEqual(context['music_spec_revision_id'],record['revision']['revision_id'])
        repeat = self.service.save_project_phase_data(self.set_id,'intent',{'data':data,'spec_revision_id':record['revision']['revision_id']})
        self.assertFalse(repeat['changed'])

    def test_stale_or_locked_edits_write_neither_phase_nor_spec(self):
        project = self.service.get_project(self.set_id)
        data = deepcopy(project['phase_data']['intent']['data'])
        data['intent']['bpm'] = 98
        original = self.store.get_song_project(self.song)['spec']
        with self.assertRaisesRegex(ValueError,'Recarga'):
            self.service.save_project_phase_data(self.set_id,'intent',{'data':data,'spec_revision_id':'old'})
        self.assertEqual(self.store.get_song_project(self.song)['spec'],original)
        spec = deepcopy(original['json_spec'])
        spec['_provenance']['bpm']['locked'] = True
        locked = self.store.upsert_song_spec(self.song,spec,True,[],user_confirmation_status='pending')
        with self.assertRaisesRegex(ValueError,'bloqueada'):
            self.service.save_project_phase_data(self.set_id,'intent',{'data':data,'spec_revision_id':locked['revision']['revision_id']})
        self.assertEqual(self.store.get_song_project(self.song)['spec'],locked)

    def test_lyrics_are_persisted_literally_in_revision_and_old_approval_invalidated(self):
        project = self.service.get_project(self.set_id)
        data = deepcopy(project['phase_data']['lyrics']['data'])
        data['lyricSections'][0]['text'] = 'Alma, sueña con la luna.\nMi cariño te acompaña.'
        markdown = '## VERSO\nAlma, sueña con la luna.\nMi cariño te acompaña.\n'
        data['lyricsEditor']['content'] = markdown
        path = self.store.data_dir/'projects'/self.song/'lyrics_approved.json'
        self.store.write_json(path,{'approved_by_qwen':True})
        saved = self.service.save_project_phase_data(self.set_id,'lyrics',{'data':data,'spec_revision_id':project['music_spec_revision_id']})
        record = self.store.get_song_project(self.song)['spec']
        self.assertEqual(record['json_spec']['_lyrics_document']['markdown'],markdown)
        self.assertEqual(saved['project']['assets']['lyrics']['content'],markdown)
        self.assertEqual((path.parent/'lyrics.md').read_text(encoding='utf-8'),markdown)
        self.assertFalse(self.store.read_json(path)['approved_by_qwen'])

    def test_proposals_do_not_persist_and_initialize_does_not_overwrite_canonical(self):
        original = self.store.get_song_project(self.song)['spec']
        proposal = self.service.ai_suggest_project_phase(self.set_id,'intent',{'data':{'intent':{'bpm':120}}})
        self.assertFalse(proposal['persisted'])
        self.assertEqual(self.store.get_song_project(self.song)['spec'],original)
        projected = self.service.initialize_project_phase(self.set_id,'intent',{'data':{'intent':{'bpm':120}}})
        self.assertEqual(projected['saved']['data']['intent']['bpm'],72)
        with self.assertRaises(ValueError):
            self.service.reset_project_phase(self.set_id,'intent')

    def test_optional_details_live_in_revision_without_becoming_engine_parameters(self):
        project = self.service.get_project(self.set_id)
        data = {'instrumental':{'brightness':40,'texture':'suave'}}
        saved = self.service.save_project_phase_data(self.set_id,'instrumental',{'data':data,'spec_revision_id':project['music_spec_revision_id']})
        record = self.store.get_song_project(self.song)['spec']
        self.assertEqual(record['json_spec']['_retained_intent']['instrumental'],data)
        self.assertNotIn('brightness',record['json_spec'])
        projected = saved['project']['phase_data']['instrumental']['data']['instrumental']
        self.assertEqual(projected['brightness'],40)
        self.assertEqual(projected['texture'],'suave')
        self.assertEqual(projected['layers'],record['json_spec']['instruments'])

    def test_editing_shared_spec_updates_phase_projection_without_archived_writes(self):
        project = self.service.get_project(self.set_id)
        old = self.store.list_project_phase_data(self.set_id)
        self.service.edit_music_spec(self.song,{'revision_id':project['music_spec_revision_id'],
            'values':{'bpm':101,'voice_style':'female intimate singer','instruments':['piano','cello']}})
        current = self.service.get_project(self.set_id)
        self.assertEqual(current['phase_data']['music-plan']['data']['musicPlan']['bpm'],101)
        self.assertEqual(current['phase_data']['intent']['data']['intent']['bpm'],101)
        self.assertEqual(current['phase_data']['voice']['data']['voice']['mainVoice'],'female intimate singer')
        self.assertEqual(current['phase_data']['instrumental']['data']['instrumental']['layers'],['piano','cello'])
        self.assertEqual(self.store.list_project_phase_data(self.set_id),old)

    def test_contradictory_lyrics_payload_does_not_replace_active_text(self):
        project = self.service.get_project(self.set_id)
        data = deepcopy(project['phase_data']['lyrics']['data'])
        data['lyricsEditor']['content'] = 'Otra letra que no coincide.'
        before = self.store.get_song_project(self.song)['spec']
        with self.assertRaisesRegex(ValueError,'no coinciden'):
            self.service.save_project_phase_data(self.set_id,'lyrics',{'data':data,'spec_revision_id':project['music_spec_revision_id']})
        self.assertEqual(self.store.get_song_project(self.song)['spec'],before)

    def test_projection_failure_does_not_claim_sqlite_was_not_saved(self):
        project = self.service.get_project(self.set_id)
        data = deepcopy(project['phase_data']['intent']['data'])
        data['intent']['bpm'] = 90
        with patch('application.music_spec_phases.export_music_spec',side_effect=OSError('disk full')):
            saved = self.service.save_project_phase_data(self.set_id,'intent',{'data':data,'spec_revision_id':project['music_spec_revision_id']})
        self.assertIn('SQLite',saved['export_warning'])
        self.assertEqual(self.store.get_song_project(self.song)['spec']['json_spec']['bpm'],90)
