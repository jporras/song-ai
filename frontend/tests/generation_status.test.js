import test from 'node:test';
import assert from 'node:assert/strict';
import {generationStatus} from '../src/generation_status.js';
test('only reported progress and explicit cancellable states are shown',()=>{
  assert.equal(generationStatus({status:'running',progress:0}).progress,0);
  for(const value of [undefined,'50',NaN,Infinity,-1,101]) assert.equal(generationStatus({progress:value}).progress,null);
  assert.equal(generationStatus({status:'cancelling'}).cancellable,false);
  assert.equal(generationStatus({status:'running'}).cancellable,true);
  assert.match(generationStatus({status:'completed'}).help,/no acredita calidad/);
  assert.match(generationStatus({status:'unknown'}).title,/sin confirmar/);
});
