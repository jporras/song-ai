import test from 'node:test';
import assert from 'node:assert/strict';
globalThis.window = { SONG_AI_API_BASE: '' };
const { productionActions } = await import('../src/production_actions.js');

test('list controls keep ordered decisions and do not mutate saved values', () => {
  const saved = ['piano', 'cello'];
  const context = { aceConfigurationDraft: { instruments: saved }, ...productionActions };
  context.setCreativeField({id:'instruments',control:'multi_choice'}, 'piano\nviolin');
  assert.deepEqual(context.aceConfigurationDraft.instruments, ['piano','violin']);
  assert.deepEqual(saved, ['piano','cello']);
});

test('opening and saving without changes makes no request', async () => {
  const context = { ...productionActions, professionalSpecification: {spec:{json_spec:{bpm:72}},catalog:{groups:[]}},
    specificationRevision:{revision_id:'r'}, productionProjectId:'s', addMessage(message){this.message=message;} };
  context.openAceConfiguration();
  await context.saveAceConfiguration();
  assert.equal(context.message,'No hay cambios para guardar.');
  assert.equal(context.aceConfigurationDraft.bpm,undefined);
});

test('catalog declares which creative controls are editable', () => {
  const context = { professionalSpecification:{catalog:{groups:[{fields:[
    {id:'theme',editable_in_spec:true}, {id:'bpm',editable_in_spec:true},
    {id:'src_audio',editable_in_spec:false}]}]}} };
  assert.deepEqual(productionActions.creativeEditorFields.call(context).map(f=>f.id), ['theme']);
});

test('refresh applies saved phase projections and rebuilds discard baselines', async () => {
  const originalFetch = globalThis.fetch;
  globalThis.fetch = async () => ({});
  try {
    let applied, captured = 0;
    const context = { activeProjectId:'set1',productionProjectId:'song1',dirty:false,
      async readApiPayload(){return {ok:true,data:{set:{set_id:'set1'},phase_data:{intent:{data:{intent:{bpm:97}}}}}};},
      applySavedPhaseData(data){applied=data;},captureProjectBaselines(){captured++;} };
    await productionActions.refreshMusicSpecProject.call(context,'song1');
    assert.equal(applied.intent.data.intent.bpm,97);
    assert.equal(captured,1);
  } finally {globalThis.fetch = originalFetch;}
});

test('late projection refresh does not overwrite unsaved changes', async () => {
  const originalFetch = globalThis.fetch;
  let resolveFetch;
  globalThis.fetch = () => new Promise(resolve=>{resolveFetch=resolve;});
  try {
    let applied = false;
    const context = {activeProjectId:'set1',productionProjectId:'song1',dirty:false,
      async readApiPayload(){return {ok:true,data:{}};},applySavedPhaseData(){applied=true;}};
    const pending = productionActions.refreshMusicSpecProject.call(context,'song1');
    context.dirty = true;
    resolveFetch({});
    await pending;
    assert.equal(applied,false);
  } finally {globalThis.fetch = originalFetch;}
});
