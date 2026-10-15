import test from 'node:test';
import assert from 'node:assert/strict';
globalThis.window = { SONG_AI_API_BASE: '' };
const { productionActions } = await import('../src/production_actions.js');

test('technical proposal cannot populate another project after delayed inference', async () => {
  let release;
  globalThis.fetch = () => new Promise(resolve => { release = resolve; });
  const context = { productionProjectId: 'first', specProposal: null, addMessage() {},
    readApiPayload: async () => ({ ok: true, data: { result: { spec_proposal: { source_revision_id: 'r1' } } } }) };
  const request = productionActions.prepareTechnicalProposal.call(context);
  context.productionProjectId = 'second';
  release({});
  await request;
  assert.equal(context.specProposal, null);
  assert.equal(context.specProposalBusy, false);
});

test('proposal tied to an old revision is rejected visibly without changing the active spec', async () => {
  globalThis.fetch = async () => ({});
  const context = { productionProjectId: 'song', specificationRevision: { revision_id: 'new' },
    activeSpec: { bpm: 72 }, addMessage() {},
    readApiPayload: async () => ({ ok: true, data: { result: { spec_proposal: { source_revision_id: 'old', spec: { bpm: 90 } } } } }) };
  await productionActions.prepareTechnicalProposal.call(context);
  assert.equal(context.specProposal, null);
  assert.match(context.specProposalError, /ficha cambio/);
  assert.deepEqual(context.activeSpec, { bpm: 72 });
});
