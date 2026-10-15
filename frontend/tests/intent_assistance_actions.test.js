import test from 'node:test';
import assert from 'node:assert/strict';

globalThis.window = { SONG_AI_API_BASE: '' };
const { productionActions } = await import('../src/production_actions.js');

function context() {
  return {
    productionProjectId: 'song1', specificationRevision: { revision_id: 'rev1' },
    productionRunningPhase: '', productionSpecMessage: 'Más alegría', dirty: false,
    aceConfigurationDraft: null, messages: [],
    addMessage(message) { this.messages.push(message); },
    async readApiPayload() { return { ok: true, data: {
      gemma: { message: 'Revisa las tres piezas musicales.' }, handoff: { task: { status: 'completed' } },
    } }; },
    async loadProfessionalProjects() { throw Error('La consulta no debe sustituir la ficha'); },
    async loadResources() {},
  };
}
const step = { phase: 'SONG_SPEC_COLLECTION', requires: 'song1', canRun: true,
  label: 'Idea', method: 'POST', url: '/api/pro/projects/song1/spec' };

test('intent advice carries revision and stays separate from saved configuration', async t => {
  const original = globalThis.fetch;
  t.after(() => { globalThis.fetch = original; });
  let sent;
  globalThis.fetch = async (_url, options) => { sent = JSON.parse(options.body); return {}; };
  const vm = context();
  await productionActions.runProductionStep.call(vm, step);
  assert.deepEqual(sent, { message: 'Más alegría', spec_revision_id: 'rev1' });
  assert.ok(vm.messages.includes('Revisa las tres piezas musicales.'));
  assert.equal(vm.specificationRevision.revision_id, 'rev1');
  assert.equal(vm.productionRunningPhase, '');
});

test('pending changes prevent inference and late advice does not cross project boundaries', async t => {
  const original = globalThis.fetch;
  t.after(() => { globalThis.fetch = original; });
  let calls = 0;
  const dirty = context(); dirty.dirty = true;
  globalThis.fetch = async () => { calls++; return {}; };
  await productionActions.runProductionStep.call(dirty, step);
  assert.equal(calls, 0);
  const switched = context();
  globalThis.fetch = async () => { switched.productionProjectId = 'song2'; return {}; };
  await productionActions.runProductionStep.call(switched, step);
  assert.ok(!switched.messages.includes('Revisa las tres piezas musicales.'));
});
