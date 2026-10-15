import test from 'node:test';
import assert from 'node:assert/strict';
import {candidateRequestIdentity} from '../src/candidate_request_identity.js';

test('retry keeps identity; changed plan/project or new explicit action creates another', () => {
  let count=0;
  const mint=()=>`id-${++count}`;
  const first=candidateRequestIdentity(null,'isabella','hash',mint);
  assert.equal(candidateRequestIdentity(first,'isabella','hash',mint),first);
  for (const [song,hash] of [['alma','hash'],['isabella','new-hash']]) {
    assert.notEqual(candidateRequestIdentity(first,song,hash,mint).requestId,first.requestId);
  }
  assert.notEqual(candidateRequestIdentity(null,'isabella','hash',mint).requestId,first.requestId);
  assert.deepEqual(first,{songId:'isabella',planHash:'hash',requestId:'id-1'});
});
