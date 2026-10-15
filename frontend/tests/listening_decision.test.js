import test from 'node:test';
import assert from 'node:assert/strict';
import {listeningReviewStatus} from '../src/listening_decision.js';
test('accepted opinion does not imply current audio or current configuration',()=>{
  assert.match(listeningReviewStatus({decision:'accepted',audio_current:false,inputs_current:true}),/histórica/);
  assert.match(listeningReviewStatus({decision:'accepted',audio_current:true,inputs_current:false}),/configuración cambió/);
  assert.match(listeningReviewStatus({decision:'accepted'}),/falta confirmar/);
  assert.match(listeningReviewStatus({audio_current:true,inputs_current:true}),/vigente/);
});
