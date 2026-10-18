import test from 'node:test';
import assert from 'node:assert/strict';
import {generationPreflight} from '../src/generation_preflight.js';
const p={music_spec_revision_id:'r',music_spec:{revision:{revision_id:'r',user_confirmation_status:'confirmed'}}};
const plan={effective_status:'approved',inputs_current:true,plan:{spec_revision_id:'r'}};
test('approved creative inputs do not certify engine readiness',()=>{
  const state=generationPreflight(p,plan,{readiness:{ready:true}},false);
  assert.equal(state.creativeReady,true);
  assert.match(state.technical,/aún deben comprobarse/);
});
test('dirty and stale inputs cannot enable generation, blocked resources are explained',()=>{
  assert.equal(generationPreflight(p,plan,{},true).creativeReady,false);
  assert.equal(generationPreflight(p,{...plan,plan:{spec_revision_id:'old'}},{},false).creativeReady,false);
  assert.match(generationPreflight(p,plan,{readiness:{ready:false}},false).technical,/bloqueo/);
});
test('pre-release memory reading points to automatic model handoff',()=>{
  const state=generationPreflight(p,plan,{
    readiness:{ready:false,decision:'blocked_ram'},
    settings:{release_llm_before_audio:true,stop_llm_command_configured:true}
  },false);
  assert.equal(state.creativeReady,true);
  assert.match(state.technical,/se liberarán los modelos/);
});
