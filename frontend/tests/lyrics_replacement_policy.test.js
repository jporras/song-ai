import test from 'node:test';
import assert from 'node:assert/strict';
import {lyricsReplacementBlockReason} from '../src/lyrics_replacement_policy.js';
test('bulk replacement respects live locks and pending unlock decisions',()=>{
  assert.match(lyricsReplacementBlockReason([{locked:true}]), /Desbloquea/);
  assert.match(lyricsReplacementBlockReason([{locked:false}],['section1']), /Guarda/);
  assert.equal(lyricsReplacementBlockReason([{text:'Texto'}]),'');
});
