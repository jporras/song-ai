import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'backend'))
from core.storage import StorageManager
from application.music_spec_edit import EditMusicSpec
from application.ace_step_plan_compiler import AceStepPlanCompiler


class MusicSpecEditTest(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.addCleanup(self.folder.cleanup)
        self.store = StorageManager(Path(self.folder.name))
        self.song = self.store.create_song_project('Idea')['id']
        self.original = self.store.upsert_song_spec(self.song,
            dict(bpm=72, key='Am', language='es', time_signature='4/4', duration_seconds=120,
                 song_type='balada', emotion='triste', ace_step_config='acestep-v15-base'),
            True, [], user_confirmation_status='confirmed')

    def test_explicit_patch_persists_user_value_and_compiles_after_confirmation(self):
        saved = EditMusicSpec(self.store).execute(self.song, {
            'revision_id': self.original['revision']['revision_id'], 'values': {'bpm': 97}})
        reloaded = StorageManager(Path(self.folder.name)).get_song_project(self.song)['spec']
        self.assertEqual(reloaded['json_spec']['bpm'], 97)
        self.assertEqual(reloaded['json_spec']['emotion'], 'triste')
        self.assertEqual(reloaded['revision']['user_confirmation_status'], 'pending')
        with self.assertRaises(ValueError):
            AceStepPlanCompiler().compile(reloaded, 'Letra')
        # Compiler input after an explicit confirmation; DB confirmation is separately covered.
        saved['revision']['user_confirmation_status'] = 'confirmed'
        plan = AceStepPlanCompiler().compile(saved, 'Letra')
        self.assertEqual(plan['payload']['bpm'], 97)
        self.assertEqual(saved['json_spec']['_provenance']['bpm']['source'], 'explicit_user_control')
        with self.assertRaisesRegex(ValueError, 'revision cambio'):
            EditMusicSpec(self.store).execute(self.song, {
                'revision_id': self.original['revision']['revision_id'], 'values': {'bpm': 80}})

    def test_invalid_or_unconnected_edits_do_not_write(self):
        for values in ({'bpm':97.5}, {'key':'bad'}, {'time_signature':'7/8'},
                       {'language':'invalid'}, {'duration_seconds':601}, {'src_audio':'other.wav'}):
            with self.subTest(values=values), self.assertRaises(ValueError):
                EditMusicSpec(self.store).execute(self.song, {
                    'revision_id':self.original['revision']['revision_id'], 'values':values})
        self.assertEqual(self.store.get_song_project(self.song)['spec']['json_spec']['bpm'],72)

    def test_creative_user_decisions_reach_caption_and_retained_spec(self):
        values = {'song_type':'nana', 'emotion':'tierna', 'instruments':['piano','cello'],
                  'voice_style':'female warm singer', 'vocal_expression':'cantada suave',
                  'dynamic_arc':'calm ending', 'groove':'slow pulse', 'vocal_range':'middle register',
                  'mix_balance':'clear voice', 'structure':['verse','chorus','verse'],
                  'required_phrases':['Alma'], 'excluded_content':['Isabella'],
                  'creative_brief':'Una canción para Alma.', 'recipient_name':'Alma'}
        saved = EditMusicSpec(self.store).execute(self.song, {
            'revision_id': self.original['revision']['revision_id'], 'values': values})
        saved['revision']['user_confirmation_status'] = 'confirmed'
        plan = AceStepPlanCompiler().compile(saved, 'Duerme, Alma.')
        for field,value in values.items():
            self.assertEqual(plan['retained_spec'][field],value)
            self.assertEqual(saved['json_spec']['_provenance'][field]['source'],'explicit_user_control')
        self.assertIn('piano, cello',plan['payload']['captions'])
        self.assertEqual(plan['payload']['lyrics'],'Duerme, Alma.')
        self.assertEqual(saved['revision']['user_confirmation_status'],'confirmed')
        self.assertEqual(self.store.get_song_project(self.song)['spec']['revision']['user_confirmation_status'],'pending')

    def test_invalid_creative_values_and_locked_decisions_do_not_write(self):
        for values in ({'structure':[]}, {'instruments':'piano'}, {'required_phrases':['']},
                       {'output_format':'zip'}, {'emotion':''}, {'_provenance':{}}):
            with self.subTest(values=values), self.assertRaises(ValueError):
                EditMusicSpec(self.store).execute(self.song,{'revision_id':self.original['revision']['revision_id'],'values':values})
        spec = dict(self.original['json_spec'])
        spec['_provenance'] = {'bpm':{'source':'USER','locked':True}}
        locked = self.store.upsert_song_spec(self.song,spec,True,[], user_confirmation_status='confirmed')
        with self.assertRaisesRegex(ValueError,'bloqueada'):
            EditMusicSpec(self.store).execute(self.song,{'revision_id':locked['revision']['revision_id'],'values':{'bpm':80}})
        self.assertEqual(self.store.get_song_project(self.song)['spec']['json_spec']['bpm'],72)
