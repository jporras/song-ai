import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'backend'))
from core.storage import StorageManager
from application.model_orchestrator import ModelOrchestrator
from application.full_lyrics_proposal import PrepareFullLyricsProposal, reviewed_full_lyrics_trace, valid_lyrics_markdown


class LyricsProposalTest(unittest.TestCase):
    def test_connected_lyrics_format_limit_and_protected_content(self):
        self.assertTrue(valid_lyrics_markdown('## Verse\nAlma canta\n\n## Chorus\nAlma sueña'))
        for text in ('Explicación\n## Verse\nAlma', '## Verse\n', '## Verse\nAlma\n## Chorus\n', '## Verse\n' + 'x' * 4090):
            self.assertFalse(valid_lyrics_markdown(text))
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as folder:
            store = StorageManager(Path(folder))
            song = store.create_song_project('Alma')['id']
            orchestrator = Mock()
            for protection in ({'locked':True}, {'protected_lines':[0]}, {'direction_locked':True}):
                store.upsert_song_spec(song, {'_lyrics_document':{'sections':[protection]}}, False, [])
                with self.assertRaisesRegex(ValueError, 'protegido'):
                    PrepareFullLyricsProposal(store, orchestrator).execute(song)
            orchestrator.run_handoff.assert_not_called()

    def test_task_keeps_active_spec_and_rejects_mock_or_constraint_violations(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as folder:
            store=StorageManager(Path(folder)); song=store.create_song_project('Alma')['id']
            saved=store.upsert_song_spec(song,{'title':'Alma','required_phrases':['Alma'],
                'excluded_content':['Isabella']},False,[])
            registry=Mock()
            registry.active_providers.return_value={'interpreter':{'name':'test-provider','capabilities':[]}}
            service=PrepareFullLyricsProposal(store,ModelOrchestrator(store,registry))
            for mode,text,accepted in [('llama_cpp','## Verse 1\nAlma duerme',True),
                ('local_mock','## Verse 1\nAlma duerme',False),
                ('llama_cpp','## Verse 1\nIsabella duerme',False)]:
                with self.subTest(mode=mode,text=text):
                    registry.interpret_with_active_provider.return_value={'mode':mode,'summary':text}
                    result=service.execute(song)
                    self.assertEqual(result['handoff']['task']['status'],'completed' if accepted else 'failed')
                    self.assertEqual(bool(result['lyrics_proposal']),accepted)
                    if accepted:
                        supplied={'task_id':result['handoff']['task']['task_id']}
                        trace=reviewed_full_lyrics_trace(store,supplied,store.get_song_project(song),
                            {'lyricSections':[{'type':'VERSE 1','text':'Alma despierta'}]})
                        self.assertEqual(trace['confirmation'],'explicit_user_save')
                        self.assertEqual(trace['proposed_markdown'],text)
                        stale=store.get_song_project(song)
                        stale['spec']['revision']['revision_id']='other-revision'
                        with self.assertRaises(ValueError):
                            reviewed_full_lyrics_trace(store,supplied,stale,{'lyricSections':[]})
                    else:
                        with self.assertRaises(ValueError):
                            reviewed_full_lyrics_trace(store,{'task_id':result['handoff']['task']['task_id']},
                                store.get_song_project(song),{'lyricSections':[]})
                    self.assertEqual(store.get_song_project(song)['spec'],saved)
            self.assertFalse((Path(folder)/'projects'/song/'lyrics.md').exists())
            self.assertEqual(len(store.list_tasks()),3)
