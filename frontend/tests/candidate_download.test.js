import test from 'node:test';
import assert from 'node:assert/strict';

globalThis.window = {SONG_AI_API_BASE:''};
const {productionActions} = await import('../src/production_actions.js');

test('download identifies the same project, task and checksum as playback',()=>{
  const context={productionProjectId:'song with spaces',aceCandidateJob:{
    task_id:'task-1',status:'completed',result:{artifact:{metadata:{audio_evidence:{sha256:'hash1'}}}}},
    aceCandidateAudioUrl:productionActions.aceCandidateAudioUrl};
  const url=new URL(productionActions.aceCandidateDownloadUrl.call(context),'http://localhost');
  assert.equal(url.pathname,'/api/pro/projects/song%20with%20spaces/ace-candidates/task-1/audio');
  assert.equal(url.searchParams.get('audio_sha256'),'hash1');
  assert.equal(url.searchParams.get('download'),'true');
  for (const job of [null,{status:'running'}, {status:'completed',result:{}}]) {
    context.aceCandidateJob=job;
    assert.equal(productionActions.aceCandidateDownloadUrl.call(context),'');
  }
});
