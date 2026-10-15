import test from 'node:test';
import assert from 'node:assert/strict';
import {studioCandidateContext} from '../src/studio_candidate_context.js';

test('historical structure comes from candidate evidence, never the current revision',()=>{
  const job={result:{fidelity_report:{spec_revision_id:'old',checks:[{id:'structure',expected:['Intro','Coro'],observed:null}]}}};
  assert.deepEqual(studioCandidateContext(job,'new'),{created:null,revision:'old',current:false,expected:['Intro','Coro'],observed:null});
  assert.equal(studioCandidateContext(job,'old').current,true);
});

test('missing evidence stays unknown rather than implying currentness or alignment',()=>{
  assert.deepEqual(studioCandidateContext({},'new'),{created:null,revision:null,current:null,expected:null,observed:null});
});
