import test from 'node:test';
import assert from 'node:assert/strict';
import {runtimeOptionRows} from '../src/runtime_option_trace.js';

test('trace separates approved zero, delegated wrapper value and missing engine observation',()=>{
  const artifact={metadata:{runtime_evidence:{runtime_options_trace:{schema_version:'runtime_options_v1',entries:[
    {field:'seed',requested_value:0,wrapper_value:0,source:'approved_override'},
    {field:'shift',requested_value:null,wrapper_value:3,source:'wrapper_default_or_cli',provenance:{source:'explicit_user_delegation'}},
  ]},generation_api:{engine_reported_options:{seed:0}}}}};
  const rows=runtimeOptionRows(artifact);
  assert.equal(rows[0].requested,0);
  assert.equal(rows[0].engine,0);
  assert.equal(rows[1].requested,'Delegado por ti');
  assert.equal(rows[1].wrapper,3);
  assert.equal(rows[1].engine,'No reportado');
});
test('old candidate or unknown trace does not invent values',()=>{
  assert.deepEqual(runtimeOptionRows({metadata:{}}),[]);
  assert.deepEqual(runtimeOptionRows({metadata:{runtime_evidence:{runtime_options_trace:{schema_version:'unknown',entries:[]}}}}),[]);
  assert.deepEqual(runtimeOptionRows({metadata:{spec_revision_id:'r2',runtime_evidence:{runtime_options_trace:{schema_version:'runtime_options_v1',spec_revision_id:'r1',entries:[{field:'seed',wrapper_value:42}]}}}}),[]);
});
