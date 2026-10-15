import test from 'node:test';
import assert from 'node:assert/strict';
import {planRequestFields} from '../src/plan_request_review.js';
test('request review preserves zero interval without inventing omitted inputs',()=>{
  const fields=planRequestFields({repainting_start:0,repainting_end:12,bpm:undefined});
  assert.equal(fields.find(f=>f.key==='repainting_start').value,'0');
  assert.equal(fields.some(f=>f.key==='bpm'),false);
  assert.deepEqual(planRequestFields(),[]);
});
