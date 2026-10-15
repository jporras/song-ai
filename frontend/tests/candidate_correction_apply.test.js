import test from 'node:test';
import assert from 'node:assert/strict';
globalThis.window = {SONG_AI_API_BASE:''};
const {productionActions} = await import('../src/production_actions.js');

function context() {
  const spec={task_type:'text2music',bpm:97,_field_decisions:{bpm:{source:'USER',locked:true}}};
  return {
    professionalSpecification:{spec:{json_spec:spec}},
    specificationRevision:{revision_id:'r1'},aceCandidateJob:{task_id:'t1'},
    candidateCorrectionProposal:{task_id:'t1',spec_revision_id:'r1',inputs_current:true,
      source_artifact_id:'a1',proposed_parameters:{task_type:'lego',target_tracks:['guitar'],instruction:'guitar'}},
    aceConfigurationDraft:null,messages:[],
    openAceConfiguration(){this.aceConfigurationDraft={task_type:spec.task_type,bpm:spec.bpm};},
    addMessage(message){this.messages.push(message);},
  };
}

test('correction opens a draft, preserving confirmed spec and independent track selection',()=>{
  const c=context(),snapshot=JSON.stringify(c.professionalSpecification);
  productionActions.openCandidateCorrectionConfiguration.call(c);
  assert.equal(c.aceConfigurationDraft.task_type,'lego');
  assert.equal(c.aceConfigurationDraft.source_artifact_id,'a1');
  assert.equal(c.aceConfigurationDraft.bpm,97);
  assert.equal(JSON.stringify(c.professionalSpecification),snapshot);
  c.aceConfigurationDraft.target_tracks.push('bass');
  assert.deepEqual(c.candidateCorrectionProposal.proposed_parameters.target_tracks,['guitar']);
});

test('cached correction cannot be applied to a different revision, task or existing draft',()=>{
  for(const mutation of [c=>c.specificationRevision.revision_id='r2',
    c=>c.aceCandidateJob.task_id='other',c=>c.candidateCorrectionProposal.inputs_current=false,
    c=>c.aceConfigurationDraft={task_type:'cover'}]) {
    const c=context();mutation(c);const before=JSON.stringify(c.aceConfigurationDraft);
    productionActions.openCandidateCorrectionConfiguration.call(c);
    assert.equal(JSON.stringify(c.aceConfigurationDraft),before);
  }
});
