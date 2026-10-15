import test from 'node:test';
import assert from 'node:assert/strict';
import {studioDeliveryState} from '../src/studio_delivery.js';

test('mock or stale sample never implies audio quality or currentness',()=>{
  const mock=studioDeliveryState({projectId:'p',sample:{approval_status:'approved'}});
  assert.match(mock.sampleText,/sin audio/);
  assert.equal(mock.action.destination,'review');
  const stale=studioDeliveryState({projectId:'p',sampleAudio:'audio',sample:{approval_status:'approved',freshness_status:'stale'}});
  assert.match(stale.sampleText,/desactualizado/);
});
test('only actual final links enable the available-files route',()=>{
  const base={projectId:'p',exports:[{type:'midi',url:'midi'},{type:'final_song_mp3',url:''}]};
  assert.equal(studioDeliveryState(base).action.destination,'review');
  const available=studioDeliveryState({...base,exports:[{type:'final_song_wav',url:'wav'}]});
  assert.equal(available.action.destination,'final');
  assert.match(available.finalText,/no acredita/);
});

test('candidate delivery has its own route and sample remains optional',()=>{
  const state=studioDeliveryState({projectId:'p',candidateAudio:'wav'});
  assert.equal(state.action.destination,'candidate');
  assert.match(state.finalText,/revisión anterior/);
  assert.equal(studioDeliveryState({projectId:'p',candidateRunning:true,candidateAudio:'old'}).action.destination,'candidate');
  assert.match(studioDeliveryState({projectId:'p'}).action.label,/definición/);
});
test('running and generation readiness come from observed state rather than export names',()=>{
  assert.equal(studioDeliveryState({projectId:'p',running:true}).action.destination,'final');
  assert.equal(studioDeliveryState({projectId:'p',canGenerate:true}).action.destination,'final');
  assert.equal(studioDeliveryState({}).action.destination,'library');
});
