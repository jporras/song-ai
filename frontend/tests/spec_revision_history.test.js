import test from 'node:test';
import assert from 'node:assert/strict';
import { revisionChanges } from '../src/spec_revision_history.js';

test('restoration review keeps zero, missing fields and lists distinct without mutating snapshots', () => {
  const current = {seed:0, instruments:['piano'], _restoration:{actor:'user'}};
  const previous = {seed:42, instruments:['guitar'], bpm:72};
  const changes = revisionChanges(current,previous,{seed:'Variación'});
  assert.equal(changes.find(c=>c.field==='seed').current,0);
  assert.equal(changes.find(c=>c.field==='seed').label,'Variación');
  assert.equal(changes.find(c=>c.field==='bpm').current,undefined);
  assert.equal(changes.length,3);
  assert.deepEqual(current.instruments,['piano']);
});

test('object key ordering is not a creative change and derived paths stay hidden', () => {
  assert.deepEqual(revisionChanges({section_direction:[{a:1,b:2}],src_audio:'a.wav'},
    {section_direction:[{b:2,a:1}],src_audio:'b.wav'}), []);
});
