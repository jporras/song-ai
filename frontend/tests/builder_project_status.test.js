import test from 'node:test';
import assert from 'node:assert/strict';
import {builderProjectStatus} from '../src/builder_project_status.js';
const project = {project:{description:'Canción para Alma'},set:{set_id:'p',instrumental_id:'i',melody_id:'m',lyrics_id:'l'},assets:{instrumental:{asset_id:'i'},melody:{asset_id:'m'},lyrics:{asset_id:'l'}},music_spec_revision_id:'r1',music_spec:{revision:{revision_id:'r1',user_confirmation_status:'confirmed'}}};
test('selected assets do not imply creative or audio approval; stale plan stays pending',()=>{
  const state=builderProjectStatus(project,{effective_status:'approved',inputs_current:true,plan:{spec_revision_id:'r0'}});
  assert.equal(state.items.slice(1,4).every(item=>item.ready),true);
  assert.equal(state.items.at(-1).ready,false);
  assert.equal(state.action.label,'Revisar plan aprobado');
});
test('foreign assets, dirty draft and absent project direct to concrete actions',()=>{
  assert.equal(builderProjectStatus({...project,assets:{}}).action.tab,'instrumental');
  assert.equal(builderProjectStatus(project,null,'lyrics').action.save,true);
  assert.equal(builderProjectStatus(null).action.tab,'library');
});
