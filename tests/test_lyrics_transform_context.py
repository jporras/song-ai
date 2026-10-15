import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'backend'))
from application.lyrics_transform_context import section_transform_context, validate_section_result, creative_spec_context


class TransformContextTests(unittest.TestCase):
    def test_compact_projection_preserves_creative_fields_without_history(self):
        record = {'revision':{'revision_id':'r1'},'json_spec':{'theme':'Alma','mandatory_requirements':['Sin batería'],
            '_consolidation':{'history':'Large diagnostic'},'_provenance':{'theme':{'source':'USER'}}}}
        context = creative_spec_context(record)
        self.assertEqual(context['json_spec'],{'theme':'Alma','mandatory_requirements':['Sin batería']})
        self.assertEqual(context['revision']['revision_id'],'r1')
        self.assertIn('_provenance',record['json_spec'])
    def setUp(self):
        self.section = {'id':'verse','type':'VERSO','text':'Alma\nMi verso','protected_lines':[0],'direction':'Íntima'}
        self.project = {'music_spec_revision_id':'r1','project':{'project_name':'Alma'},'phase_data':{
            'lyrics':{'data':{'lyricSections':[self.section],'lyrics':{'theme':'Alma'}}},
            'instrumental':{'data':{'instrumental':{'layers':['piano']}}}}}
        self.request = {'section_id':'verse','section_type':'VERSO','text':self.section['text'],
            'section_draft':dict(self.section),'spec_revision_id':'r1','project_name':'Wrong'}

    def test_persisted_intention_wins_and_protected_lines_are_enforced(self):
        context = section_transform_context(self.project,self.request)
        self.assertEqual(context['project_name'],'Alma')
        self.assertEqual(context['instrumental']['layers'],['piano'])
        self.assertEqual(context['section']['direction'],'Íntima')
        validate_section_result(context,'Alma\nNuevo verso')
        with self.assertRaises(ValueError):
            validate_section_result(context,'Isabella\nNuevo verso')

    def test_stale_revision_foreign_section_and_implicit_unlock_rejected(self):
        for change in ({'spec_revision_id':'r0'}, {'section_id':'other'},
                       {'section_draft':{**self.section,'protected_lines':[]}}):
            with self.assertRaises(ValueError):
                section_transform_context(self.project,{**self.request,**change})
