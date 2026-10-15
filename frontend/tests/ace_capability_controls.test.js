import test from 'node:test';
import assert from 'node:assert/strict';
import { capabilityControls } from '../src/ace_capability_controls.js';

test('missing backend contract cannot invent available controls', () => {
  assert.equal(capabilityControls({}, {}), null);
});

test('server ranges and conditional rules drive controls without mutating USER draft', () => {
  const catalog = { capability_profile: { version: 'fixture-v1', choices: {task_type: ['text2music', 'lego']},
    modes: { text2music: { requires_source: false }, lego: { requires_source: true, requires_base: true } },
    numeric_ranges_by_config: { custom: {seed: [0, 100], guidance_scale: [1, 15]} },
    fixed_values_by_config: { custom: {guidance_scale: 1} } } };
  const draft = { task_type: 'lego', ace_step_config: 'custom', guidance_scale: 5 };
  const before = structuredClone(draft);
  const controls = capabilityControls(catalog, draft);
  assert.deepEqual(controls.range('seed'), [0, 100]);
  assert.deepEqual(controls.range('guidance_scale'), [1, 1]);
  assert.equal(controls.mode.requires_source, true);
  assert.equal(controls.lmApplicable, false);
  assert.deepEqual(draft, before);
});

test('one-track actions explain incompatible choices without rewriting USER decisions', () => {
  const catalog={capability_profile:{version:'v1',choices:{},modes:{extract:{requires_base:true,track_cardinality:'one'}}}};
  const draft={task_type:'extract',ace_step_config:'acestep-v15-turbo',target_tracks:['vocals','guitar']};
  const before=structuredClone(draft);
  assert.equal(capabilityControls(catalog,draft).selectionIssues.length,2);
  assert.deepEqual(draft,before);
  assert.deepEqual(capabilityControls(catalog,{...draft,ace_step_config:'acestep-v15-base',target_tracks:['vocals']}).selectionIssues,[]);
});

test('changing to an editing mode preserves the LM choice and explains incompatibility', () => {
  const catalog={capability_profile:{version:'v1',choices:{},modes:{text2music:{},cover:{requires_source:true}}}};
  const draft={task_type:'cover',generation_api:'high_level_lm'};
  assert.equal(capabilityControls(catalog,draft).selectionIssues.length,1);
  assert.equal(draft.generation_api,'high_level_lm');
  assert.equal(capabilityControls(catalog,{...draft,task_type:'text2music'}).lmApplicable,true);
  for (const generation_api of ['direct','high_level']) assert.deepEqual(capabilityControls(catalog,{...draft,generation_api}).selectionIssues,[]);
});
