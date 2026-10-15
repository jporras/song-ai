import test from 'node:test';
import assert from 'node:assert/strict';
globalThis.window = {SONG_AI_API_BASE: ''};
const {productionActions} = await import('../src/production_actions.js');
delete globalThis.window;

function context() {
  return {productionProjectId:'alma', specProposal:{song_id:'alma',task_id:'task',source_revision_id:'r1'},
    specProposalBusy:false, messages:[], addMessage(message){this.messages.push(message);},
    async readApiPayload(response){return response;}};
}

test('explicit rejection binds project, task and revision without editing saved decisions', async () => {
  const ctx=context();
  const originalFetch=globalThis.fetch;
  let sent;
  globalThis.fetch=async (url, options)=>{sent=JSON.parse(options.body);return {ok:true};};
  try {
    await productionActions.rejectTechnicalProposal.call(ctx);
    assert.equal(sent.tool_id,'spec.reject_proposal');
    assert.equal(sent.revision_id,'r1');
    assert.equal(sent.parameters.task_id,'task');
    assert.equal(sent.user_authorized,true);
    assert.equal(ctx.specProposal,null);
    assert.equal(ctx.specProposalBusy,false);
  } finally {globalThis.fetch=originalFetch;}
});

test('failed rejection preserves proposal and late responses preserve another project', async () => {
  const originalFetch=globalThis.fetch;
  try {
    const ctx=context();
    globalThis.fetch=async()=>({ok:false,detail:'La ficha cambio'});
    await productionActions.rejectTechnicalProposal.call(ctx);
    assert.equal(ctx.specProposal.task_id,'task');
    assert.equal(ctx.messages[0],'La ficha cambio');
    globalThis.fetch=async()=>{ctx.productionProjectId='isabella';ctx.specProposal={task_id:'other'};return {ok:true};};
    await productionActions.rejectTechnicalProposal.call(ctx);
    assert.equal(ctx.specProposal.task_id,'other');
  } finally {globalThis.fetch=originalFetch;}
});
