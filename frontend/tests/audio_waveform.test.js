import test from 'node:test';
import assert from 'node:assert/strict';
import {audioPeaks, validAudioInterval} from '../src/audio_waveform.js';

test('peaks cover the full file and every channel, without normalizing silence', () => {
  assert.deepEqual(audioPeaks([new Float32Array([0,0,0,0])],2),[0,0]);
  assert.deepEqual(audioPeaks([new Float32Array([.25,0,0]),new Float32Array([0,-.5,1])],2),[.25,1]);
  assert.deepEqual(audioPeaks([new Float32Array([0,0,1])],2),[0,1]);
  assert.throws(()=>audioPeaks([]));
});

test('only a finite interval inside the decoded duration can be selected', () => {
  assert.equal(validAudioInterval(0,12,12),true);
  for (const values of [[0,0,12],[-1,2,12],[0,13,12],['0',2,12],[0,NaN,12],[0,2,Infinity]]) {
    assert.equal(validAudioInterval(...values),false);
  }
});
