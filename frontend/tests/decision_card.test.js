import test from 'node:test';
import assert from 'node:assert/strict';
import {decisionValue} from '../src/decision_card.js';
test('explicit false and zero remain decisions, missing fields stay undecided',()=>{
  assert.equal(decisionValue(false),'No');
  assert.equal(decisionValue(0),'0');
  assert.equal(decisionValue([false,0]),'No, 0');
  assert.equal(decisionValue(null),'Por decidir');
  assert.equal(decisionValue([]),'Por decidir');
  assert.equal(decisionValue({direction:'Sin batería'}).includes('Sin batería'),true);
});
