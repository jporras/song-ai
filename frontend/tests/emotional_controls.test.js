import test from 'node:test';
import assert from 'node:assert/strict';
import {emotionalControls,validEmotionalValues} from '../src/emotional_controls.js';

test('all emotional controls accept boundaries and reject invalid numeric drafts',()=>{
  for(const boundary of [0,100]) assert.equal(validEmotionalValues(Object.fromEntries(emotionalControls.map(c=>[c.key,boundary]))),true);
  for(const {key} of emotionalControls) for(const value of [-1,101,NaN,Infinity,'',null,true,'50']) {
    const values=Object.fromEntries(emotionalControls.map(c=>[c.key,50]));values[key]=value;
    assert.equal(validEmotionalValues(values),false);
  }
});
