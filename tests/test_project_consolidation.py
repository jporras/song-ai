import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'backend'))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
from core.storage import StorageManager
from models.song_set import SongSet
from models.assets import AssetType, AssetDraft
from models.manifest import Manifest
from models.intent import MusicalIntent
from application.project_consolidation import ProjectConsolidation
from consolidate_song_projects import resolution


class ProjectConsolidationTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.addCleanup(folder.cleanup)
        self.store = StorageManager(Path(folder.name))
        intent = MusicalIntent(96, 'C major', 'warm', ['bass'], 'medium', 'soft', 'mock')
        for kind in AssetType:
            path = self.store.get_asset_draft_dir(kind, kind.value)
            name = {'instrumental':'instrumental.txt','melody':'melody.txt','lyrics':'lyrics.md'}[kind.value]
            self.store.save_asset_draft(AssetDraft(kind.value, kind, Manifest(kind.value, kind.value, 'mock'), intent))
            (path/name).write_text('Isabella original mock', encoding='utf-8')
        self.projects = []
        for index, name in enumerate(('Isabella','Alma')):
            set_id = f'set-{index}'
            self.store.save_song_set(SongSet(set_id,name,'cuna','2026-01-01','instrumental','melody','lyrics'))
            song = self.store.create_song_project(name, f'set:{set_id}')['id']
            self.store.upsert_song_spec(song, {'bpm':72,'key':'C major','duration_seconds':120,'output_format':'mp3','recipient_name':'Isabella'}, True, [])
            self.store.save_project_phase_data(set_id,'lyrics',{
                'lyrics':{'placeholders':{'name':'Isabella'}},
                'lyricSections':[{'id':'verse-1','type':'VERSO','text':f'Duerme, {name}, sueña.'}],
                'lyricsEditor':{'content':f'## VERSO\nDuerme, {name}, sueña.\n'}},'saved')
            self.store.save_project_phase_data(set_id,'voice',{'voice':{'performance':'cantada con ternura','pronunciation':'clara'}},'saved')
            self.projects.append((song,name,set_id))

    def test_two_projects_preserve_lyrics_and_separate_assets_with_pending_review(self):
        for song,name,set_id in self.projects:
            before = self.store.list_project_phase_data(set_id)['lyrics']['data']['lyricsEditor']['content']
            result = ProjectConsolidation(self.store).execute(song, resolution(self.store,song,name))
            saved = self.store.get_song_project(song)
            self.assertEqual(saved['spec']['json_spec']['recipient_name'], name)
            self.assertEqual(saved['spec']['revision']['user_confirmation_status'],'pending')
            self.assertEqual(self.store.get_asset_draft_detail(result['asset_ids']['lyrics'])['content'], before)
            self.assertFalse(self.store.read_json(self.store.data_dir/'projects'/song/'lyrics_approved.json')['approved_by_qwen'])
            self.assertEqual(self.store.list_project_phase_data(set_id)['lyrics']['data']['lyrics']['placeholders']['name'],name)
            revisions = len(self.store.list_song_spec_revisions(song))
            self.assertEqual(ProjectConsolidation(self.store).execute(song,{})['status'],'already_consolidated')
            self.assertEqual(len(self.store.list_song_spec_revisions(song)),revisions)
        sets = self.store.list_indexed_sets()
        self.assertNotEqual(sets[0]['lyrics_id'],sets[1]['lyrics_id'])
        self.assertEqual(self.store.get_asset_draft_detail('lyrics')['content'],'Isabella original mock')

    def test_fixture_is_preserved_but_not_listed_as_a_working_song(self):
        song,name,set_id = self.projects[0]
        self.store.save_song_set(SongSet(set_id,name,'cuna','2026-01-01','instrumental','melody','lyrics',{'workspace_role':'fixture'}))
        self.assertEqual(len(self.store.list_indexed_sets()),1)
        self.assertEqual(len(self.store.list_song_projects()),1)
        self.assertIsNotNone(self.store.get_song_project(song))
        self.assertIsNotNone(self.store.get_indexed_set(set_id))

    def test_incomplete_resolution_writes_nothing(self):
        song,name,set_id = self.projects[0]
        before = self.store.get_song_project(song)['spec']
        with self.assertRaises(ValueError):
            ProjectConsolidation(self.store).execute(song,{'recipient':name,'spec':{}})
        self.assertEqual(self.store.get_song_project(song)['spec'],before)
