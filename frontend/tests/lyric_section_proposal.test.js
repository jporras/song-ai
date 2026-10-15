import test from 'node:test';
import assert from 'node:assert/strict';
import {canApplySectionProposal} from '../src/lyric_section_proposal.js';
test('proposal requires same project, context and section including locks and direction', () => {
  const section = {id:'v',text:'Alma\nVerso',protected_lines:[0],direction:'Suave'};
  const proposal = {projectId:'p',context:'r1',sectionSnapshot:JSON.stringify(section),text:'Alma\nNuevo verso'};
  assert.equal(canApplySectionProposal(proposal,section,'p','r1'),true);
  assert.equal(canApplySectionProposal(proposal,section,'other','r1'),false);
  assert.equal(canApplySectionProposal(proposal,section,'p','r2'),false);
  assert.equal(canApplySectionProposal(proposal,{...section,direction:'Fuerte'},'p','r1'),false);
  assert.equal(canApplySectionProposal({...proposal,text:'Isabella\nVerso'},section,'p','r1'),false);
  assert.equal(canApplySectionProposal(proposal,{...section,locked:true},'p','r1'),false);
});
