import test from 'node:test';
import assert from 'node:assert/strict';
import { validPhaseRanges } from '../src/phase_range_validation.js';
test('reject invalid numeric directions and preserve valid boundaries across families', () => {
 for (const [phase, section, key] of [['instrumental','instrumental','brightness'],['voice','voice','vibrato'],['midi','midiPlan','velocity']]) {
  for (const value of [-1,128,'',true,NaN,Infinity]) assert.equal(validPhaseRanges(phase,{[section]:{[key]:value}}),false);
  assert.equal(validPhaseRanges(phase,{[section]:{[key]:0}}),true);
 }
 assert.equal(validPhaseRanges('music-plan',{musicPlan:{sections:[{intensity:101}]}}),false);
 assert.equal(validPhaseRanges('voice',{voice:{layers:[{level:100}]}}),true);
 assert.equal(validPhaseRanges('instrumental',{instrumental:{stems:[{level:null}]}}),false);
 assert.equal(validPhaseRanges('voice',{voice:{}}),true);
});
