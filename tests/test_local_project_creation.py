import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'backend'))
from application.local_project_creation import CreateLocalProject
import tempfile
from core.storage import StorageManager
from application.music_spec_edit import EditMusicSpec


class CreationTest(unittest.TestCase):
    def test_legacy_sections_without_ids_export_and_preserve_source_text(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as folder:
            store = StorageManager(Path(folder))
            sections = [{'type': 'VERSO', 'text': 'Duerme mi cielo'},
                        {'id': 'legacy-section-1', 'type': 'CORO', 'text': 'Isabella duerme'}]
            phases = {'lyrics': {'data': {'lyricSections': sections}}}
            from application.set_music_spec_projection import SetMusicSpecProjection
            with patch.object(store, 'get_indexed_set', return_value={'set_id': 'set'}), \
                 patch.object(store, 'list_project_phase_data', return_value=phases), \
                 patch.object(SetMusicSpecProjection, '_assets_for_set', return_value={k: {'intent': {}} for k in ('instrumental', 'melody', 'lyrics')}), \
                 patch.object(SetMusicSpecProjection, '_spec_from_set_data', return_value={'title': 'Isabella', 'description': 'Cuna'}), \
                 patch.object(SetMusicSpecProjection, '_lyrics_markdown_from_set', return_value='## VERSO\nDuerme mi cielo\n\n## CORO\nIsabella duerme'):
                project = CreateLocalProject(store).execute({'source_set_id': 'set'})['project']
            spec = project['spec']['json_spec']
            migrated = spec['_lyrics_document']['sections']
            self.assertEqual([s['text'] for s in migrated], [s['text'] for s in sections])
            self.assertEqual(len({s['id'] for s in migrated}), 2)
            self.assertEqual(migrated[1]['id'], 'legacy-section-1')
            self.assertNotIn('id', sections[0])
            self.assertEqual(spec['_preparation']['section_id_migration'][0]['assigned_id'], migrated[0]['id'])
            self.assertEqual(spec['_editor_phases']['lyrics']['data']['lyricSections'], migrated)
            self.assertTrue((Path(folder)/'projects'/project['id']/'lyrics.json').exists())
            self.assertEqual(project['spec']['revision']['user_confirmation_status'], 'pending')

    def test_lost_creation_race_does_not_overwrite_the_winning_definition(self):
        store=Mock()
        store.list_song_projects.return_value=[]
        store.get_indexed_set.return_value={'set_id':'set','project_name':'Alma',
            'instrumental_id':'i','melody_id':'m','lyrics_id':'l'}
        store.get_asset_draft_detail.return_value={'intent':{'mood':'calm'},'content':'Texto'}
        store.list_project_phase_data.return_value={}
        store.create_song_project.return_value={'id':'winner','_creation_reused':True}
        store.get_song_project.return_value={'id':'winner','title':'Original'}
        result=CreateLocalProject(store).execute({'source_set_id':'set'})
        self.assertEqual(result['project']['id'],'winner')
        store.upsert_song_spec.assert_not_called()
        store.create_song_event.assert_not_called()

    def test_repeated_preparation_reuses_revision_and_does_not_mutate_events(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as folder:
            store=StorageManager(Path(folder))
            project=store.create_song_project('Alma','set:existing')
            saved=store.upsert_song_spec(project['id'],{'title':'Alma','bpm':72},False,[],
                deterministic_valid=True,user_confirmation_status='confirmed')
            events=store.list_song_project_events(project['id'])
            creator=CreateLocalProject(store)
            for title in ('Otro título','Otro título más'):
                returned=creator.execute({'source_set_id':'existing','title':title})['project']
                self.assertEqual(returned['id'],project['id'])
                self.assertEqual(returned['title'],'Alma')
                self.assertEqual(returned['spec']['revision']['revision_id'],saved['revision']['revision_id'])
            self.assertEqual(len(store.list_song_projects()),1)
            self.assertEqual(store.list_song_project_events(project['id']),events)

    def test_ambiguous_link_blocks_without_creating_or_changing_projects(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as folder:
            store=StorageManager(Path(folder))
            for title in ('Alma','Duplicado'):
                store.create_song_project(title,'set:ambiguous')
            before=store.list_song_projects()
            with self.assertRaisesRegex(ValueError,'varias fichas'):
                CreateLocalProject(store).execute({'source_set_id':'ambiguous'})
            self.assertEqual(store.list_song_projects(),before)

    def test_preparation_can_be_validated_without_model_approval_and_missing_fields_stay_pending(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as folder:
            store=StorageManager(Path(folder))
            song=store.create_song_project('Alma')['id']
            spec=dict(title='Alma',creative_brief='Canción para Alma',bpm=72,key='Am',language='es',
                duration_seconds=30,emotion='calma',instruments=['piano'],output_format='wav',
                song_type='balada',structure=['verse'],voice_style='voz suave',ace_step_config='acestep-v15-base',
                _preparation={'requires_deterministic_review':True})
            original=store.upsert_song_spec(song,spec,False,[],deterministic_valid=False)
            saved=EditMusicSpec(store).execute(song,{'revision_id':original['revision']['revision_id'],
                'values':{'ace_step_config':'acestep-v15-base'}})
            self.assertTrue(saved['revision']['deterministic_valid'])
            self.assertFalse(saved['approved_by_qwen'])
            self.assertEqual(saved['revision']['user_confirmation_status'],'pending')
            del spec['voice_style']
            original=store.upsert_song_spec(song,spec,False,[],deterministic_valid=False)
            saved=EditMusicSpec(store).execute(song,{'revision_id':original['revision']['revision_id'],
                'values':{'ace_step_config':'acestep-v15-base'}})
            self.assertFalse(saved['revision']['deterministic_valid'])
            self.assertIn('voice_style',saved['missing_fields'])

    def test_missing_piece_blocks_before_project_write(self):
        store=Mock()
        store.list_song_projects.return_value=[]
        store.get_indexed_set.return_value={'set_id':'set','instrumental_id':'i','melody_id':'m'}
        store.get_asset_draft_detail.return_value={'intent':{'mood':'calm'}}
        with self.assertRaisesRegex(ValueError,'instrumental'):
            CreateLocalProject(store).execute({'source_set_id':'set'})
        store.create_song_project.assert_not_called()

    def test_set_intents_remain_separate_without_approvals_or_models(self):
        store=Mock()
        store.list_song_projects.return_value=[]
        store.get_indexed_set.return_value={'set_id':'set','project_name':'Alma',
            'instrumental_id':'i','melody_id':'m','lyrics_id':'l'}
        store.get_asset_draft_detail.side_effect=lambda key:{'intent':{'chosen':key},'content':'Texto para Alma'}
        store.list_project_phase_data.return_value={}
        store.create_song_project.return_value={'id':'song'}
        store.get_song_project.return_value={'id':'song','current_phase':'SONG_SPEC_COLLECTION'}
        with patch('application.local_project_creation.export_music_spec'):
            CreateLocalProject(store).execute({'source_set_id':'set','title':'Alma'})
        args=store.upsert_song_spec.call_args
        spec=args.args[1]
        self.assertFalse(args.args[2])
        self.assertFalse(args.kwargs['deterministic_valid'])
        self.assertEqual(args.kwargs['user_confirmation_status'],'pending')
        self.assertEqual(spec['_retained_intent'],{'instrumental':{'chosen':'i'},'melody':{'chosen':'m'},'lyrics':{'chosen':'l'}})
        self.assertIn('Alma',spec['_lyrics_document']['markdown'])
