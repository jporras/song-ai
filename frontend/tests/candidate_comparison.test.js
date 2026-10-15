import test from "node:test";
import assert from "node:assert/strict";

globalThis.window = { SONG_AI_API_BASE: "" };
const { productionActions } = await import("../src/production_actions.js");
const { compareCandidateReports } = await import("../src/candidate_comparison.js");

test("comparison audio requires completed candidate from selected project", () => {
  const task = { task_id: "old", status: "completed", payload: { song_id: "song" },
    result: { artifact: { metadata: { audio_evidence: { sha256: "hash" } } } } };
  const context = { productionProjectId: "song", aceComparisonTaskId: "old", aceCandidateHistory: [task] };
  assert.match(productionActions.aceComparisonAudioUrl.call(context), /old\/audio\?audio_sha256=hash$/);
  task.status = "failed";
  assert.equal(productionActions.aceComparisonAudioUrl.call(context), "");
  task.status = "completed";
  task.payload.song_id = "other";
  assert.equal(productionActions.aceComparisonAudioUrl.call(context), "");
});

test("starting one comparison player pauses the others", () => {
  let paused = 0;
  const active = { pause: () => assert.fail("active player must keep playing") };
  globalThis.document = { querySelectorAll: selector => {
    assert.equal(selector, "audio[data-candidate-comparison]");
    return [active, { pause: () => paused++ }];
  } };
  productionActions.pauseOtherCandidatePlayers({ target: active });
  assert.equal(paused, 1);
});

test("comparison distinguishes measured duration and unmeasured musical requirements", () => {
  const a = { plan_sha256: "p1", spec_revision_id: "r1", checks: [
    { id: "duration", expected: 60, observed: 64, method: "wav_frames_sample_rate", status: "outside_tolerance" },
    { id: "lyrics", expected: "Coro", observed: null, method: "not_measured" }] };
  const b = { plan_sha256: "p2", spec_revision_id: "r2", checks: [
    { id: "duration", expected: 30, observed: 30, method: "wav_frames_sample_rate", status: "within_tolerance" },
    { id: "lyrics", expected: "Verso", observed: "not a measurement", method: "not_measured" }] };
  const result = compareCandidateReports(a, b);
  assert.equal(result.samePlan, false);
  assert.equal(result.sameRevision, false);
  assert.equal(result.checks[0].expectedChanged, true);
  assert.match(result.checks[0].observedA, /fuera del margen/);
  assert.match(result.checks[1].observedB, /Pendiente/);
  assert.equal(result.finalQualityVerified, false);
});

test("missing evidence cannot imply identical plans or measured values", () => {
  const result = compareCandidateReports(undefined, { checks: [{ id: "duration", expected: 0, observed: NaN, method: "wav_frames_sample_rate" }] });
  assert.equal(result.samePlan, false);
  assert.equal(result.sameRevision, false);
  assert.equal(result.checks[0].expectedB, "0");
  assert.equal(result.checks[0].missingReport, true);
  assert.match(result.checks[0].observedB, /Pendiente/);
});

test("object key ordering does not invent changes or mutate original reports", () => {
  const a = { checks: [{ id: "voice", expected: { range: "alto", energy: 2 } }] };
  const b = { checks: [{ id: "voice", expected: { energy: 2, range: "alto" } }] };
  const before = JSON.stringify(a);
  assert.equal(compareCandidateReports(a, b).checks[0].expectedChanged, false);
  assert.equal(JSON.stringify(a), before);
});

test("correction opens existing controls without saving or overwriting an active draft", () => {
  const proposal = { inputs_current: true, task_id: "t", source_artifact_id: "audio", proposed_parameters: { task_type: "repaint", repainting_start: 2, repainting_end: 6 } };
  let opened = 0;
  const context = { candidateCorrectionProposal: proposal, aceCandidateJob: { task_id: "t" }, aceConfigurationDraft: null,
    openAceConfiguration() { opened++; this.aceConfigurationDraft = { ace_step_config: "acestep-v15-base", audio_cover_strength: 1 }; },
    addMessage() {} };
  productionActions.openCandidateCorrectionConfiguration.call(context);
  assert.equal(context.aceConfigurationDraft.source_artifact_id, "audio");
  assert.equal(context.aceConfigurationDraft.repainting_start, 2);
  assert.deepEqual(context.aceConfigurationDraft.target_tracks, []);
  productionActions.openCandidateCorrectionConfiguration.call(context);
  assert.equal(opened, 1);
  context.aceConfigurationDraft = null;
  proposal.inputs_current = false;
  productionActions.openCandidateCorrectionConfiguration.call(context);
  assert.equal(opened, 1);
});

test("late correction response cannot populate a different selected project", async () => {
  const previousFetch = globalThis.fetch;
  globalThis.fetch = async () => ({});
  const context = { productionProjectId: "other", aceCandidateJob: { task_id: "t" }, candidateCorrectionProposal: null,
    async readApiPayload() { return { data: { proposal: { task_id: "t" } } }; } };
  try {
    await productionActions.loadCandidateCorrection.call(context, "song", "t");
    assert.equal(context.candidateCorrectionProposal, null);
  } finally { globalThis.fetch = previousFetch; }
});

test("Base correction keeps selected tracks and instruction in the reviewable draft", () => {
  const proposal = { inputs_current: true, task_id: "t", source_artifact_id: "audio",
    proposed_parameters: { task_type: "complete", ace_step_config: "acestep-v15-base", target_tracks: ["guitar", "drums"], instruction: "guitar drums" } };
  const context = { candidateCorrectionProposal: proposal, aceCandidateJob: { task_id: "t" }, aceConfigurationDraft: null,
    openAceConfiguration() { this.aceConfigurationDraft = { ace_step_config: "acestep-v15-turbo" }; }, addMessage() {} };
  productionActions.openCandidateCorrectionConfiguration.call(context);
  assert.equal(context.aceConfigurationDraft.ace_step_config, "acestep-v15-base");
  assert.deepEqual(context.aceConfigurationDraft.target_tracks, ["guitar", "drums"]);
  context.aceConfigurationDraft.target_tracks.pop();
  assert.equal(proposal.proposed_parameters.target_tracks.length, 2);
  assert.equal(context.aceConfigurationDraft.instruction, "guitar drums");
});

test("polling keeps explicit decisions only for the same current plan", async () => {
  const previousFetch = globalThis.fetch;
  globalThis.fetch = async () => ({});
  const plan = { plan_id: "p", plan: { plan_sha256: "hash" }, effective_status: "approved", inputs_current: true };
  try {
    for (const [next, preserved] of [[structuredClone(plan), true], [{ ...plan, inputs_current: false }, false],
      [{ ...plan, plan_id: "other" }, false], [{ ...plan, effective_status: "stale" }, false],
      [{ ...plan, plan: { plan_sha256: "changed" } }, false], [null, false]]) {
      const context = { productionProjectId: "song", acePlanProjectId: "song", acePlanReview: plan,
        acePlanLyricsConfirmed: true, aceCandidateAuthorized: true,
        async readApiPayload() { return { data: { plan: next } }; },
        async loadAceCandidateJob() {}, async loadSampleEvaluation() {} };
      await productionActions.loadAcePlan.call(context, "song");
      assert.equal(context.acePlanLyricsConfirmed, preserved);
      assert.equal(context.aceCandidateAuthorized, preserved);
    }
  } finally { globalThis.fetch = previousFetch; }
});
