import test from 'node:test';
import assert from 'node:assert/strict';
import {phaseToOpenAfterLoad} from '../src/song_builder_flow.js';

const tabs=['intent','instrumental','music-plan','lyrics','midi','voice','production'];
test('project opening follows Builder preparation and does not require a MIDI phase',()=>{
  assert.equal(phaseToOpenAfterLoad({},tabs),'intent');
  const phase_data={intent:{status:'saved'}};
  assert.equal(phaseToOpenAfterLoad({phase_data},tabs),'instrumental');
  phase_data.instrumental={status:'saved'};
  assert.equal(phaseToOpenAfterLoad({phase_data},tabs),'music-plan');
  phase_data['music-plan']={status:'saved'};
  assert.equal(phaseToOpenAfterLoad({phase_data},tabs),'lyrics');
  phase_data.lyrics={status:'saved'};
  assert.equal(phaseToOpenAfterLoad({phase_data},tabs),'production');
});
test('saved navigation is preserved and unknown routes fall back to Builder',()=>{
  for(const phase of tabs) assert.equal(phaseToOpenAfterLoad({ui_state:{last_active_phase:phase}},tabs),phase);
  assert.equal(phaseToOpenAfterLoad({ui_state:{last_active_phase:'unknown'}},tabs),'intent');
});
