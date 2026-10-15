import test from 'node:test';
import assert from 'node:assert/strict';
import {appendAppliedProposal, MAX_REVIEWED_PROPOSALS} from '../src/assistant_proposal_queue.js';

test('applied proposals retain order and independent original values', () => {
  const first = {phase:'intent', changes:{bpm:109}};
  const list = appendAppliedProposal([], first);
  first.changes.bpm = 222;
  const both = appendAppliedProposal(list, {phase:'intent', changes:{bpm:115}});
  assert.deepEqual(both.map(p=>p.changes.bpm), [109,115]);
  assert.equal(list.length, 1);
});

test('queue refuses more proposals before applying an untraceable change', () => {
  const list = Array.from({length:MAX_REVIEWED_PROPOSALS},()=>({phase:'intent'}));
  assert.throws(()=>appendAppliedProposal(list, {changes:{bpm:115}}), /Guarda o descarta/);
  assert.equal(list.length, MAX_REVIEWED_PROPOSALS);
});
