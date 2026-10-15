import test from 'node:test';
import assert from 'node:assert/strict';
globalThis.window = {SONG_AI_API_BASE: ''};
const {productionActions} = await import('../src/production_actions.js');

test('explicit musical save sends USER BPM to shared revision endpoint', async () => {
  const oldFetch = globalThis.fetch;
  let request;
  globalThis.fetch = async (url, options) => {request={url,options};return {};};
  try {
    const context = {productionProjectId:'song1', aceConfigurationRevision:'r1',
      aceConfigurationDraft:{bpm:97}, savingAceConfiguration:false,
      readApiPayload:async()=>({ok:true,data:{revision:'r2'}}),
      loadAcePlan:async()=>{}, addMessage:()=>{}};
    await productionActions.saveAceConfiguration.call(context);
    assert.equal(request.options.method,'PATCH');
    assert.match(request.url,/song1\/spec$/);
    assert.equal(JSON.parse(request.options.body).values.bpm,97);
    assert.equal(JSON.parse(request.options.body).revision_id,'r1');
    assert.equal(context.aceConfigurationDraft,null);
  } finally {globalThis.fetch=oldFetch;}
});

test('late save response cannot overwrite a newer edit revision', async () => {
  const oldFetch=globalThis.fetch;
  const context={productionProjectId:'song1',aceConfigurationRevision:'r1',
    aceConfigurationDraft:{bpm:97},savingAceConfiguration:false,
    professionalSpecification:{current:true}, addMessage:()=>{},
    readApiPayload:async()=>{context.aceConfigurationRevision='r2';return {ok:true,data:{stale:true}};},
    loadAcePlan:async()=>{throw new Error('must not refresh stale response');}};
  globalThis.fetch=async()=>({});
  try {
    await productionActions.saveAceConfiguration.call(context);
    assert.deepEqual(context.professionalSpecification,{current:true});
    assert.deepEqual(context.aceConfigurationDraft,{bpm:97});
  } finally {globalThis.fetch=oldFetch;}
});
