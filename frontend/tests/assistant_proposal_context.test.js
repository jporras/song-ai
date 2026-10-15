import test from 'node:test';
import assert from 'node:assert/strict';
import {proposalContext, proposalContextMatches} from '../src/assistant_proposal_context.js';

test('proposal accepts the unchanged saved revision and draft', () => {
  const context = proposalContext('alma', 'r1', 'intent', {bpm:97});
  assert.equal(proposalContextMatches(context, proposalContext('alma', 'r1', 'intent', {bpm:97})), true);
});

test('proposal rejects changed project, revision, phase or unsaved user decisions', () => {
  const context = proposalContext('alma', 'r1', 'intent', {bpm:97});
  for (const current of [
    proposalContext('isabella', 'r1', 'intent', {bpm:97}),
    proposalContext('alma', 'r2', 'intent', {bpm:97}),
    proposalContext('alma', 'r1', 'voice', {bpm:97}),
    proposalContext('alma', 'r1', 'intent', {bpm:101}),
  ]) assert.equal(proposalContextMatches(context, current), false);
  assert.equal(proposalContextMatches(null, context), false);
});
