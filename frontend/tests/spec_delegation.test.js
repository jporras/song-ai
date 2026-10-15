import test from 'node:test';
import assert from 'node:assert/strict';
globalThis.window = {SONG_AI_API_BASE:''};
const {productionActions} = await import('../src/production_actions.js');

test('delegation sends an explicit null override with the current revision', async () => {
  const oldFetch = globalThis.fetch;
  let sent;
  globalThis.fetch = async (url, options) => {sent=JSON.parse(options.body); return {};};
  const context = {productionProjectId:'alma', professionalSpecification:{spec:{revision:{revision_id:'r1'}}},
    readApiPayload:async()=>({ok:true,data:{spec:{revision:{revision_id:'r2'}}}}),
    loadAcePlan:async()=>{},addMessage:()=>{}};
  try {
    await productionActions.delegateSpecField.call(context,{id:'seed',can_delegate_to_profile:true});
    assert.deepEqual(sent,{revision_id:'r1',values:{seed:null}});
    assert.equal(context.professionalSpecification.spec.revision.revision_id,'r2');
  } finally {globalThis.fetch=oldFetch;}
});

test('delegation does not overwrite an open user draft', async () => {
  const oldFetch = globalThis.fetch;
  let called = false;
  globalThis.fetch = async()=>{called=true;};
  try {
    for (const state of [{dirty:true},{aceConfigurationDraft:{seed:17}}]) {
      await productionActions.delegateSpecField.call({...state,addMessage:()=>{}},{id:'seed',can_delegate_to_profile:true});
    }
    assert.equal(called,false);
  } finally {globalThis.fetch=oldFetch;}
});
