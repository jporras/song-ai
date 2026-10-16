import { apiUrl } from "./api_client.js";
import { compareCandidateReports } from "./candidate_comparison.js";
import { runtimeOptionRows } from "./runtime_option_trace.js";
import { candidateRequestIdentity } from "./candidate_request_identity.js";

export const productionActions = {
  async restoreMusicSpec(request) {
    const songId = this.productionProjectId;
    if (!songId || this.specRestoreBusy || this.aceConfigurationDraft || this.dirty) return;
    this.specRestoreBusy = true;
    try {
      const response = await fetch(apiUrl(`/api/pro/projects/${encodeURIComponent(songId)}/spec/restore`), {
        method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(request),
      });
      const payload = await this.readApiPayload(response, {});
      if (songId !== this.productionProjectId) return;
      if (!payload.ok) { this.addMessage(payload.detail || 'No se pudo recuperar la definición.'); return; }
      await this.loadProfessionalSpecification(songId);
      this.addMessage('Definición recuperada como nueva versión. Revisa y confirma antes de generar.');
    } catch (error) {
      if (songId === this.productionProjectId) this.addMessage(`No se pudo recuperar: ${error?.message || 'error de red'}`);
    } finally { this.specRestoreBusy = false; }
  },
  async importSourceAudio(event) {
    const file=event.target.files?.[0], songId=this.productionProjectId;
    if (!file || !songId || this.sourceImportBusy || !this.sourceImportAuthorized) return;
    this.sourceImportBusy=true;
    try {
      if (file.size > 64*1024*1024) throw new Error('El archivo supera 64 MiB.');
      const response=await fetch(apiUrl(`/api/pro/projects/${encodeURIComponent(songId)}/source-audio?filename=${encodeURIComponent(file.name)}&authorized=true`),{method:'POST',headers:{'Content-Type':'audio/wav'},body:file});
      const result=await this.readApiPayload(response,{});
      if (!result.ok) throw new Error(result.detail || 'No se pudo importar el audio.');
      if (this.productionProjectId === songId) {
        await this.loadProfessionalSpecification(songId);
        this.addMessage('Audio importado. Elígelo como fuente o referencia; no se selecciona ni guarda automáticamente.');
      }
    } catch(error) { this.addMessage(`No se pudo importar: ${error.message}`); }
    finally { this.sourceImportBusy=false; event.target.value=''; }
  },

  runtimeOptionRows,
  migrationFieldLabel(field) {
    return (this.professionalSpecification?.catalog?.groups || [])
      .flatMap(group => group.fields || []).find(item => item.id === field)?.label || field;
  },
  async reviewLegacyMigration() {
    const songId = this.productionProjectId;
    const revisionId = this.specificationRevision?.revision_id;
    if (!songId || this.legacyMigrationBusy) return;
    this.legacyMigrationBusy = true;
    try {
      const response = await fetch(apiUrl(`/api/pro/projects/${encodeURIComponent(songId)}/spec/legacy-migration`), {method:'POST'});
      const payload = await this.readApiPayload(response, {});
      if (songId !== this.productionProjectId || revisionId !== this.specificationRevision?.revision_id) return;
      if (!payload.ok) return this.addMessage(payload.detail || 'No se pudo revisar el historial.');
      this.legacyMigrationPreview = payload.data;
    } catch (error) { this.addMessage(`No se pudo revisar: ${error.message}`); }
    finally { this.legacyMigrationBusy = false; }
  },
  async applyLegacyMigration() {
    const songId = this.productionProjectId;
    const proposal = this.legacyMigrationPreview;
    const revisionId = this.specificationRevision?.revision_id;
    if (!proposal || proposal.song_id !== songId || this.legacyMigrationBusy) return;
    this.legacyMigrationBusy = true;
    try {
      const response = await fetch(apiUrl(`/api/pro/projects/${encodeURIComponent(songId)}/spec/legacy-migration/apply`), {
        method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({
          revision_id:proposal.revision_id, source_sha256:proposal.source_sha256, fields:Object.keys(proposal.additions)})});
      const payload = await this.readApiPayload(response, {});
      if (songId !== this.productionProjectId || revisionId !== this.specificationRevision?.revision_id) return;
      if (!payload.ok) return this.addMessage(payload.detail || 'No se pudo migrar.');
      this.professionalSpecification = payload.data;
      this.legacyMigrationPreview = null;
      await this.loadAcePlan(songId);
      this.addMessage('Datos faltantes migrados; revisa técnicamente y confirma la intención.');
    } catch (error) { this.addMessage(`No se pudo migrar: ${error.message}`); }
    finally { this.legacyMigrationBusy = false; }
  },
  async prepareTechnicalProposal() {
    const songId = this.productionProjectId;
    if (!songId || this.specProposalBusy) return;
    this.specProposalBusy = true;
    this.specProposalStartedAt = Date.now();
    this.specProposalRequestId = crypto.randomUUID();
    this.specProposalStep = 1;
    this.specProposalTrackingError = false;
    const requestId = this.specProposalRequestId;
    this.specProposalPollTimer = setInterval(() => this.pollSpecProposalStatus(songId, requestId), 1500);
    this.specProposal = null;
    this.specProposalError = "";
    try {
      const response = await fetch(apiUrl(`/api/pro/projects/${encodeURIComponent(songId)}/spec/proposal?request_id=${encodeURIComponent(requestId)}`), { method: "POST" });
      const payload = await this.readApiPayload(response, {});
      if (songId !== this.productionProjectId) return;
      if (!payload.ok) throw new Error(payload.detail || "No se pudo preparar la propuesta.");
      const result = payload.data?.result;
      if (!result?.spec_proposal) throw new Error(result?.provider_error || "El modelo no devolvio una ficha estructurada completa.");
      if (this.specificationRevision?.revision_id && result.spec_proposal.source_revision_id !== this.specificationRevision.revision_id)
        throw new Error("La ficha cambio durante la revision. Prepara una nueva propuesta.");
      this.specProposal = { ...result.spec_proposal, song_id: songId, task_id: payload.data?.task?.task_id };
      this.specProposalStep = 3;
    } catch (error) { if (songId === this.productionProjectId) { this.specProposalError = error.message; this.addMessage(error.message); } }
    finally {
      clearInterval(this.specProposalPollTimer);
      this.specProposalPollTimer = null;
      this.specProposalBusy = false;
      this.specProposalStartedAt = 0;
      this.specProposalRequestId = "";
    }
  },
  async rejectTechnicalProposal() {
    const songId = this.productionProjectId;
    const proposal = this.specProposal;
    if (!songId || proposal?.song_id !== songId || !proposal.task_id || this.specProposalBusy) return;
    this.specProposalBusy = true;
    try {
      const response = await fetch(apiUrl(`/api/pro/projects/${encodeURIComponent(songId)}/music-actions`), {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({tool_id: 'spec.reject_proposal', revision_id: proposal.source_revision_id,
          user_authorized: true, parameters: {task_id: proposal.task_id}}),
      });
      const payload = await this.readApiPayload(response, {});
      if (!payload.ok) throw new Error(payload.detail || 'No se pudo rechazar la propuesta.');
      if (this.productionProjectId === songId && this.specProposal?.task_id === proposal.task_id) {
        this.specProposal = null;
        this.addMessage('Propuesta rechazada. La ficha guardada se conserva.');
      }
    } catch (error) {
      if (this.productionProjectId === songId) this.addMessage(error.message);
    } finally { this.specProposalBusy = false; }
  },
  async saveSampleListeningFeedback() {
    const songId = this.productionProjectId;
    const setId = this.activeProjectId;
    const sampleId = this.activeSampleCheckpoint?.sample_id;
    if (!songId || !sampleId || this.sampleCheckpointRunning || this.sampleListeningConfirmation !== this.sampleReviewKey) return;
    this.sampleCheckpointRunning = true;
    try {
      const response = await fetch(apiUrl(`/api/pro/projects/${encodeURIComponent(songId)}/samples/${encodeURIComponent(sampleId)}/review`), {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ listened: true, decision: this.sampleFeedbackDecision, notes: this.sampleFeedbackNotes,
          audio_sha256: this.activeSampleCheckpoint.audio_evidence.sha256 }),
      });
      const payload = await this.readApiPayload(response, {});
      if (!payload.ok) return this.addMessage(payload.detail || "No se pudo guardar la opinion del sample.");
      if (this.productionProjectId !== songId || this.activeProjectId !== setId) return;
      this.sampleFeedbackDecision = "";
      this.sampleFeedbackNotes = "";
      this.sampleListeningConfirmation = "";
      await this.loadProject(setId, { quiet: true });
      this.addMessage("Opinion del sample guardada. La aprobacion y la produccion final requieren sus propias comprobaciones.");
    } catch (error) { this.addMessage(`No se pudo guardar: ${error.message}`); }
    finally { this.sampleCheckpointRunning = false; }
  },
  async loadSampleEvaluation() {
    this.sampleRepresentativityReport = null;
    this.sampleListeningReviewView = null;
    const songId = this.productionProjectId;
    const sampleId = this.activeSampleCheckpoint?.sample_id;
    if (!songId || !sampleId || this.activeSampleCheckpoint?.source_song_id !== songId) return;
    const response = await fetch(apiUrl(`/api/pro/projects/${encodeURIComponent(songId)}/samples/${encodeURIComponent(sampleId)}/representativity`));
    const payload = await this.readApiPayload(response, { report: null });
    if (this.productionProjectId === songId && this.activeSampleCheckpoint?.sample_id === sampleId) this.sampleRepresentativityReport = payload.ok ? payload.data?.report : null;
    const reviewResponse = await fetch(apiUrl(`/api/pro/projects/${encodeURIComponent(songId)}/samples/${encodeURIComponent(sampleId)}/review`));
    const reviewPayload = await this.readApiPayload(reviewResponse, { review: null });
    if (this.productionProjectId === songId && this.activeSampleCheckpoint?.sample_id === sampleId) this.sampleListeningReviewView = reviewPayload.ok ? reviewPayload.data?.review : null;
  },
  async evaluateActiveSample() {
    const songId = this.productionProjectId;
    const sampleId = this.activeSampleCheckpoint?.sample_id;
    if (!songId || !sampleId || this.sampleCheckpointRunning) return;
    this.sampleCheckpointRunning = true;
    this.sampleRepresentativityReport = null;
    try {
      const response = await fetch(apiUrl(`/api/pro/projects/${encodeURIComponent(songId)}/samples/${encodeURIComponent(sampleId)}/representativity`), { method: "POST" });
      const payload = await this.readApiPayload(response, {});
      if (!payload.ok) return this.addMessage(payload.detail || "No se pudo evaluar el sample.");
      if (this.productionProjectId === songId && this.activeSampleCheckpoint?.sample_id === sampleId) this.sampleRepresentativityReport = payload.data?.report;
    } catch (error) { this.addMessage(`No se pudo evaluar: ${error.message}`); }
    finally { this.sampleCheckpointRunning = false; }
  },
  async createSampleFromCandidate() {
    const songId = this.productionProjectId;
    const taskId = this.aceCandidateJob?.task_id;
    const setId = this.activeProjectId;
    if (!songId || !taskId || !setId || this.aceCandidateBusy) return;
    this.aceCandidateBusy = true;
    try {
      const response = await fetch(apiUrl(`/api/pro/projects/${encodeURIComponent(songId)}/ace-candidates/${encodeURIComponent(taskId)}/sample`), {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ set_id: setId, create_sample_confirmed: true,
          audio_sha256: this.aceCandidateJob.result?.artifact?.metadata?.audio_evidence?.sha256 }),
      });
      const payload = await this.readApiPayload(response, {});
      if (!payload.ok) return this.addMessage(payload.detail || "No se pudo crear el sample.");
      if (this.productionProjectId !== songId || this.activeProjectId !== setId) return;
      this.sampleListeningConfirmation = "";
      await this.loadProject(setId, { quiet: true });
      this.addMessage(payload.data?.message || "Sample creado; escuchalo y revisalo por separado.");
    } catch (error) { this.addMessage(`No se pudo crear el sample: ${error.message}`); }
    finally { this.aceCandidateBusy = false; }
  },
  async saveCandidateListeningReview() {
    const songId = this.productionProjectId;
    const taskId = this.aceCandidateJob?.task_id;
    if (!songId || !taskId || !this.candidateListeningConfirmed || this.aceCandidateBusy) return;
    this.aceCandidateBusy = true;
    try {
      const response = await fetch(apiUrl(`/api/pro/projects/${encodeURIComponent(songId)}/ace-candidates/${encodeURIComponent(taskId)}/review`), {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ listened: true, decision: this.candidateListeningDecision, notes: this.candidateListeningNotes,
          criteria: this.candidateListeningCriteria,
          audio_sha256: this.aceCandidateJob?.result?.artifact?.metadata?.audio_evidence?.sha256 }),
      });
      const payload = await this.readApiPayload(response, {});
      if (!payload.ok) return this.addMessage(payload.detail || "No se pudo guardar la revision.");
      if (this.productionProjectId !== songId || this.aceCandidateJob?.task_id !== taskId) return;
      this.candidateListeningReview = payload.data?.review;
      this.candidateCorrection = { scope: "", start: null, end: null, target_tracks: [], instruction: "" };
      await this.loadCandidateCorrection(songId, taskId);
      this.candidateListeningConfirmed = false;
      this.addMessage("Opinion guardada para este borrador. El sample y la cancion final necesitan su propia revision.");
    } catch (error) { this.addMessage(`No se pudo guardar la opinion: ${error.message}`); }
    finally { this.aceCandidateBusy = false; }
  },
  async cancelAceCandidateJob() {
    const songId = this.productionProjectId;
    const taskId = this.aceCandidateJob?.task_id;
    if (!songId || !taskId || this.aceCandidateBusy) return;
    this.aceCandidateBusy = true;
    try {
      const response = await fetch(apiUrl(`/api/pro/projects/${encodeURIComponent(songId)}/ace-candidates/${encodeURIComponent(taskId)}/cancel`), { method: "POST" });
      const payload = await this.readApiPayload(response, {});
      if (!payload.ok) this.addMessage(payload.detail || "No se pudo cancelar el trabajo.");
      if (this.productionProjectId === songId) await this.loadAceCandidateJob(songId);
    } catch (error) {
      this.addMessage(`No se pudo cancelar: ${error?.message || "error de red"}`);
    } finally { this.aceCandidateBusy = false; }
  },
  async proposeCandidateCorrection() {
    const songId = this.productionProjectId, taskId = this.aceCandidateJob?.task_id;
    if (!songId || !taskId || this.aceCandidateBusy) return;
    this.aceCandidateBusy = true;
    try {
      const response = await fetch(apiUrl(`/api/pro/projects/${encodeURIComponent(songId)}/ace-candidates/${encodeURIComponent(taskId)}/correction`), {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ...this.candidateCorrection, reviewed_at: this.candidateListeningReview?.reviewed_at }),
      });
      const payload = await this.readApiPayload(response, {});
      if (this.productionProjectId !== songId || this.aceCandidateJob?.task_id !== taskId) return;
      if (!payload.ok) return this.addMessage(payload.detail || "No se pudo registrar la propuesta.");
      await this.loadCandidateCorrection(songId, taskId);
      this.addMessage(`Propuesta registrada (${payload.data.proposal.proposed_parameters.task_type}). Revisa la ficha y prepara un nuevo plan; la generacion sigue pendiente.`);
    } catch (error) { this.addMessage(`No se pudo preparar la correccion: ${error.message}`); }
    finally { this.aceCandidateBusy = false; }
  },
  aceCandidateAudioUrl() {
    const checksum = this.aceCandidateJob?.result?.artifact?.metadata?.audio_evidence?.sha256;
    if (this.aceCandidateJob?.status !== "completed" || !checksum) return "";
    return apiUrl(`/api/pro/projects/${encodeURIComponent(this.productionProjectId)}/ace-candidates/${encodeURIComponent(this.aceCandidateJob.task_id)}/audio?audio_sha256=${encodeURIComponent(checksum)}`);
  },
  aceCandidateDownloadUrl() {
    const audioUrl = this.aceCandidateAudioUrl();
    return audioUrl ? `${audioUrl}&download=true` : '';
  },
  async loadCandidateCorrection(songId, taskId) {
    const response = await fetch(apiUrl(`/api/pro/projects/${encodeURIComponent(songId)}/ace-candidates/${encodeURIComponent(taskId)}/correction`));
    const payload = await this.readApiPayload(response, { proposal: null });
    if (this.productionProjectId === songId && this.aceCandidateJob?.task_id === taskId) this.candidateCorrectionProposal = payload.data?.proposal || null;
  },
  openCandidateCorrectionConfiguration() {
    const proposal = this.candidateCorrectionProposal;
    if (!proposal?.inputs_current || this.aceConfigurationDraft || proposal.task_id !== this.aceCandidateJob?.task_id) return;
    if (proposal.spec_revision_id !== this.specificationRevision?.revision_id) {
      this.addMessage("La definición cambió desde esta propuesta. Actualiza la revisión de escucha y prepara una propuesta vigente.");
      return;
    }
    this.openAceConfiguration();
    Object.assign(this.aceConfigurationDraft, proposal.proposed_parameters, {
      source_artifact_id: proposal.source_artifact_id || "",
      instruction: proposal.proposed_parameters.instruction || "",
      target_tracks: [...(proposal.proposed_parameters.target_tracks || [])],
    });
    this.addMessage("Propuesta cargada en los controles sin guardar. Revisa tambien tus notas en la ficha musical; luego guarda, confirma la nueva revision y prepara el plan.");
  },
  async reviewCandidateCorrection() {
    const songId = this.productionProjectId, taskId = this.aceCandidateJob?.task_id;
    if (!songId || !taskId || !this.candidateCorrectionProposal?.inputs_current || this.aceCandidateBusy) return;
    this.aceCandidateBusy = true;
    try {
      const response = await fetch(apiUrl(`/api/pro/projects/${encodeURIComponent(songId)}/ace-candidates/${encodeURIComponent(taskId)}/correction/review`), {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ review_requested: true, proposal_created_at: this.candidateCorrectionProposal.created_at }),
      });
      const payload = await this.readApiPayload(response, {});
      if (this.productionProjectId !== songId || this.aceCandidateJob?.task_id !== taskId) return;
      if (!payload.ok) return this.addMessage(payload.detail || "No se pudo revisar la propuesta.");
      await this.loadCandidateCorrection(songId, taskId);
      this.addMessage("Revision tecnica registrada. Revisa sus sugerencias antes de editar la ficha; no se aplicaron cambios.");
    } catch (error) { this.addMessage(`No se pudo revisar: ${error.message}`); }
    finally { this.aceCandidateBusy = false; }
  },
  aceComparisonAudioUrl() {
    const task = this.aceCandidateHistory.find(item => item.task_id === this.aceComparisonTaskId);
    const checksum = task?.result?.artifact?.metadata?.audio_evidence?.sha256;
    if (task?.status !== "completed" || task?.payload?.song_id !== this.productionProjectId || !checksum) return "";
    return apiUrl(`/api/pro/projects/${encodeURIComponent(this.productionProjectId)}/ace-candidates/${encodeURIComponent(task.task_id)}/audio?audio_sha256=${encodeURIComponent(checksum)}`);
  },
  aceComparisonReport() {
    const task = this.aceCandidateHistory.find(item => item.task_id === this.aceComparisonTaskId);
    if (task?.status !== "completed" || task?.payload?.song_id !== this.productionProjectId || this.aceCandidateJob?.status !== "completed") return null;
    return compareCandidateReports(this.aceCandidateJob.result?.fidelity_report, task.result?.fidelity_report);
  },
  pauseOtherCandidatePlayers(event) {
    document.querySelectorAll("audio[data-candidate-comparison]").forEach(player => {
      if (player !== event.target) player.pause();
    });
  },
  async loadAceCandidateJob(songId) {
    if (this.aceCandidateTimer) clearTimeout(this.aceCandidateTimer);
    const response = await fetch(apiUrl(`/api/pro/projects/${encodeURIComponent(songId)}/ace-candidates`));
    const payload = await this.readApiPayload(response, { job: null });
    if (this.productionProjectId !== songId) return;
    const previousTask = this.aceCandidateJob?.task_id;
    this.aceCandidateJob = payload.data?.job || null;
    this.aceCandidateHistory = payload.data?.history || [];
    if (!this.aceCandidateHistory.some(task => task.task_id === this.aceComparisonTaskId && task.status === "completed")) this.aceComparisonTaskId = "";
    if (previousTask !== this.aceCandidateJob?.task_id) {
      this.candidateCorrectionProposal = null;
      this.candidateCorrection = { scope: "", start: null, end: null, target_tracks: [], instruction: "" };
      this.candidateListeningConfirmed = false;
      this.candidateListeningDecision = "";
      this.candidateListeningNotes = "";
      this.candidateListeningCriteria = {};
      this.candidateListeningReview = null;
    }
    if (this.aceCandidateJob?.status === "completed") {
      const taskId = this.aceCandidateJob.task_id;
      const reviewResponse = await fetch(apiUrl(`/api/pro/projects/${encodeURIComponent(songId)}/ace-candidates/${encodeURIComponent(taskId)}/review`));
      const reviewPayload = await this.readApiPayload(reviewResponse, { review: null });
      if (this.productionProjectId === songId && this.aceCandidateJob?.task_id === taskId) this.candidateListeningReview = reviewPayload.data?.review || null;
      await this.loadCandidateCorrection(songId, taskId);
    }
    if (["pending", "running", "cancelling"].includes(this.aceCandidateJob?.status)) {
      this.aceCandidateTimer = setTimeout(() => {
        if (this.productionProjectId === songId) this.loadAceCandidateJob(songId).catch(error => this.addMessage(`No se pudo consultar el trabajo: ${error.message}`));
      }, 3000);
    }
  },

  async startAceCandidateJob() {
    const songId = this.productionProjectId;
    if (!songId || !this.generationPreflightState.creativeReady || !this.aceCandidateAuthorized || this.aceCandidateBusy) return;
    this.aceCandidateBusy = true;
    try {
      const identity = candidateRequestIdentity(this.aceCandidateRequest, songId, this.acePlanReview?.plan?.plan_sha256);
      this.aceCandidateRequest = identity;
      const response = await fetch(apiUrl(`/api/pro/projects/${encodeURIComponent(songId)}/ace-candidates`), {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ plan_sha256: identity.planHash, exploratory_audio_authorized: true, request_id: identity.requestId }),
      });
      const payload = await this.readApiPayload(response, {});
      if (!payload.ok) return this.addMessage(payload.detail || "No se pudo iniciar el borrador.");
      if (this.productionProjectId !== songId) return;
      if (this.aceCandidateRequest?.requestId === identity.requestId) this.aceCandidateRequest = null;
      this.aceCandidateAuthorized = false;
      await this.loadAceCandidateJob(songId);
    } catch (error) {
      this.addMessage(`No se pudo iniciar: ${error?.message || "error de red"}`);
    } finally { this.aceCandidateBusy = false; }
  },
  async loadAcePlan(songId) {
    this.sampleRepresentativityReport = null;
    if (this.acePlanProjectId !== songId) {
      this.acePlanReview = null;
      this.acePlanLyricsDraft = null;
      this.acePlanLyricsConfirmed = false;
      this.acePlanProjectId = songId;
      this.aceCandidateAuthorized = false;
      this.aceCandidateJob = null;
      this.aceCandidateHistory = [];
      this.candidateCorrectionProposal = null;
      this.candidateCorrection = { scope: "", start: null, end: null, target_tracks: [], instruction: "" };
      this.aceComparisonTaskId = "";
    }
    const response = await fetch(apiUrl(`/api/pro/projects/${encodeURIComponent(songId)}/ace-plan`));
    const payload = await this.readApiPayload(response, { plan: null });
    if (this.productionProjectId !== songId) return;
    const previous = this.acePlanReview;
    this.acePlanReview = payload.data?.plan || null;
    const current = this.acePlanReview;
    if (!current || previous?.plan_id !== current.plan_id
      || previous?.plan?.plan_sha256 !== current.plan?.plan_sha256
      || previous?.effective_status !== current.effective_status
      || previous?.inputs_current !== current.inputs_current) {
      this.acePlanLyricsConfirmed = false;
      this.aceCandidateAuthorized = false;
    }
    await this.loadAceCandidateJob(songId);
    await this.loadSampleEvaluation();
  },

  startAcePlanReview() {
    this.acePlanLyricsDraft = this.lyricsEditor?.content || "";
    this.acePlanLyricsConfirmed = false;
  },

  async prepareAcePlan() {
    const songId = this.productionProjectId;
    if (!songId || this.acePlanBusy) return;
    this.acePlanBusy = true;
    try {
      const response = await fetch(apiUrl(`/api/pro/projects/${encodeURIComponent(songId)}/ace-plan`), {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ lyrics: this.acePlanLyricsDraft }),
      });
      const payload = await this.readApiPayload(response, {});
      if (!payload.ok) return this.addMessage(payload.detail || "No se pudo preparar el plan.");
      if (this.productionProjectId !== songId) return;
      this.acePlanLyricsDraft = null;
      await this.loadAcePlan(songId);
    } catch (error) {
      this.addMessage(`No se pudo preparar el plan: ${error?.message || "error de red"}`);
    } finally { this.acePlanBusy = false; }
  },

  async approveAcePlan() {
    const songId = this.productionProjectId;
    const item = this.acePlanReview;
    if (!songId || !item || !this.acePlanLyricsConfirmed || this.acePlanBusy) return;
    this.acePlanBusy = true;
    try {
      const response = await fetch(apiUrl(`/api/pro/projects/${encodeURIComponent(songId)}/ace-plan/${encodeURIComponent(item.plan_id)}/approve`), {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ plan_sha256: item.plan.plan_sha256, lyrics_confirmed: true }),
      });
      const payload = await this.readApiPayload(response, {});
      if (!payload.ok) this.addMessage(payload.detail || "No se pudo aprobar el plan.");
      else this.addMessage("Plan y letra aprobados. Puedes iniciar la generación; el sample previo es opcional. El audio generado requiere su propia revisión.");
      await this.loadAcePlan(songId);
    } catch (error) {
      this.addMessage(`No se pudo aprobar: ${error?.message || "error de red"}`);
    } finally { this.acePlanBusy = false; }
  },
  openAceConfiguration() {
    const spec = this.professionalSpecification?.spec?.json_spec || {};
    this.aceConfigurationRevision = this.specificationRevision?.revision_id || "";
    this.aceConfigurationDraft = {
      ...Object.fromEntries((this.professionalSpecification?.catalog?.groups || []).flatMap(group => group.fields || [])
        .filter(field => field.editable_in_spec).map(field => field.id)
        .filter(key => spec[key] !== undefined).map(key => [key, spec[key]])),
      task_type: spec.task_type || "text2music",
      ace_step_config: spec.ace_step_config || "acestep-v15-base",
      generation_api: spec.generation_api || "direct",
      lm_model_path: spec.lm_model_path || "acestep-5Hz-lm-1.7B",
      reference_artifact_id: spec.reference_artifact_id || "",
      seed: spec.seed ?? null,
      inference_steps: spec.inference_steps ?? null,
      guidance_scale: spec.guidance_scale ?? null,
      shift: spec.shift ?? null,
      source_artifact_id: spec.source_artifact_id || "",
      instruction: spec.instruction || "",
      target_tracks: Array.isArray(spec.target_tracks) ? [...spec.target_tracks] : [],
      repainting_start: spec.repainting_start ?? 0,
      repainting_end: spec.repainting_end ?? -1,
      audio_cover_strength: spec.audio_cover_strength ?? 1,
      duration_tolerance_seconds: spec.duration_tolerance_seconds ?? null,
    };
    this.aceConfigurationOriginalDraft = JSON.parse(JSON.stringify(this.aceConfigurationDraft));
  },
  creativeEditorFields() {
    return (this.professionalSpecification?.catalog?.groups || []).flatMap(group => group.fields || [])
      .filter(field => field.editable_in_spec && !['bpm', 'key', 'time_signature', 'language', 'duration_seconds'].includes(field.id));
  },
  async refreshMusicSpecProject(songId) {
    const setId = this.activeProjectId;
    if (!setId || this.productionProjectId !== songId || this.dirty) return;
    const response = await fetch(apiUrl(`/api/projects/${encodeURIComponent(setId)}`));
    const payload = await this.readApiPayload(response, {});
    if (!payload.ok || this.activeProjectId !== setId || this.productionProjectId !== songId || this.dirty) return;
    this.activeProject = payload.data;
    this.selectedSet = payload.data.set;
    this.savedPhaseData = payload.data.phase_data || {};
    this.applySavedPhaseData(this.savedPhaseData);
    this.captureProjectBaselines();
  },
  creativeFieldIsList(field) {
    return ['multi_choice', 'ordered_list', 'list'].includes(field.control);
  },
  setCreativeField(field, text) {
    this.aceConfigurationDraft[field.id] = this.creativeFieldIsList(field)
      ? text.split('\n').map(value => value.trim()).filter(Boolean) : text;
  },

  async saveAceConfiguration() {
    const songId = this.productionProjectId;
    const revisionId = this.aceConfigurationRevision;
    if (!songId || !this.aceConfigurationDraft || this.savingAceConfiguration) return;
    const values = Object.fromEntries(Object.entries(this.aceConfigurationDraft)
      .filter(([key, value]) => JSON.stringify(value) !== JSON.stringify(this.aceConfigurationOriginalDraft?.[key])));
    if (this.professionalSpecification?.spec?.json_spec?._preparation?.requires_deterministic_review) {
      for (const key of ['ace_step_config','task_type','generation_api']) {
        values[key] = this.aceConfigurationDraft[key];
      }
    }
    if (!Object.keys(values).length && this.specificationRevision?.technical_review_mode === 'restored_snapshot_requires_review') {
      values.ace_step_config = this.aceConfigurationDraft.ace_step_config;
    }
    if (!Object.keys(values).length) return this.addMessage('No hay cambios para guardar.');
    if (values.duration_tolerance_seconds === '') values.duration_tolerance_seconds = null;
    this.savingAceConfiguration = true;
    try {
      const response = await fetch(apiUrl(`/api/pro/projects/${encodeURIComponent(songId)}/spec`), {
        method: "PATCH", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ revision_id: this.aceConfigurationRevision, values }),
      });
      const payload = await this.readApiPayload(response, {});
      if (!payload.ok) return this.addMessage(payload.detail || "No se pudo guardar la configuracion.");
      if (this.productionProjectId !== songId || this.aceConfigurationRevision !== revisionId) return;
      this.professionalSpecification = payload.data;
      this.aceConfigurationDraft = null;
      if (this.refreshMusicSpecProject) await this.refreshMusicSpecProject(songId);
      await this.loadAcePlan(songId);
      this.addMessage("Entradas guardadas en una nueva revision. Revisa y confirma la ficha; aun no se genero audio.");
    } catch (error) {
      this.addMessage(`No se pudo guardar: ${error?.message || "error de red"}`);
    } finally {
      this.savingAceConfiguration = false;
    }
  },
  async delegateSpecField(field) {
    if (!field?.can_delegate_to_profile || this.savingAceConfiguration) return;
    if (this.dirty || this.aceConfigurationDraft) return this.addMessage('Guarda o descarta los cambios abiertos antes de delegar este ajuste.');
    const songId = this.productionProjectId;
    const revisionId = this.professionalSpecification?.spec?.revision?.revision_id;
    if (!songId || !revisionId) return;
    this.savingAceConfiguration = true;
    try {
      const response = await fetch(apiUrl(`/api/pro/projects/${encodeURIComponent(songId)}/spec`), {
        method:'PATCH', headers:{'Content-Type':'application/json'},
        body:JSON.stringify({revision_id:revisionId, values:{[field.id]:null}}),
      });
      const payload = await this.readApiPayload(response, {});
      if (!payload.ok) return this.addMessage(payload.detail || 'No se pudo guardar la delegación.');
      if (this.productionProjectId !== songId || this.professionalSpecification?.spec?.revision?.revision_id !== revisionId) return;
      this.professionalSpecification = payload.data;
      if (this.refreshMusicSpecProject) await this.refreshMusicSpecProject(songId);
      await this.loadAcePlan(songId);
      this.addMessage('Delegación guardada. Revisa el perfil y confirma la nueva ficha antes de generar.');
    } catch (error) {
      this.addMessage(`No se pudo delegar: ${error?.message || 'error de red'}`);
    } finally {
      this.savingAceConfiguration = false;
    }
  },
  async createActiveSetSample() {
    if (!this.activeProjectId || this.sampleCheckpointRunning) return;
    this.sampleCheckpointRunning = true;
    try {
      const response = await fetch(apiUrl("/api/samples"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ set_id: this.activeProjectId }),
      });
      const payload = await this.readApiPayload(response, {});
      if (!payload.ok) return this.addMessage(payload.detail || "No se pudo crear el sample.");
      await this.loadProject(this.activeProjectId, { quiet: true });
      this.addMessage("Sample mock creado para el set activo. Revísalo antes de aprobarlo.");
    } finally {
      this.sampleCheckpointRunning = false;
    }
  },

  async approveActiveSetSample() {
    const sampleId = this.activeSampleCheckpoint?.sample_id || "";
    if (!this.activeProjectId || !sampleId || this.sampleCheckpointRunning) return;
    const evidence = this.activeSampleCheckpoint?.audio_evidence;
    if (evidence && this.sampleListeningConfirmation !== this.sampleReviewKey) return this.addMessage("Escucha el audio y confirma que revisaste esta versión.");
    this.sampleCheckpointRunning = true;
    try {
      const response = await fetch(apiUrl(`/api/sets/${encodeURIComponent(this.activeProjectId)}/samples/${encodeURIComponent(sampleId)}/approve`), {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ listened: Boolean(evidence), audio_sha256: evidence?.sha256 || "" }),
      });
      const payload = await this.readApiPayload(response, {});
      if (!payload.ok) return this.addMessage(payload.detail || "No se pudo aprobar el sample.");
      await this.loadProject(this.activeProjectId, { quiet: true });
      this.sampleListeningConfirmation = "";
      this.addMessage("Revisión guardada. La canción completa requiere su propia evaluación; el sample previo es opcional.");
    } finally {
      this.sampleCheckpointRunning = false;
    }
  },

  async loadLocalFinalJob() {
    const response = await fetch(apiUrl("/api/local-final-song/status"));
    const payload = await this.readApiPayload(response, this.localFinalJob);
    this.localFinalJob = payload.data;
    if (this.localFinalJob.status === "running") this.scheduleLocalFinalPoll();
  },

  async loadProfessionalProjects() {
    const response = await fetch(apiUrl("/api/pro/projects"));
    const payload = await this.readApiPayload(response, { projects: [] });
    this.professionalProjects = payload.data.projects || [];
    if (this.productionProjectId && !this.professionalProjects.some((project) => project.id === this.productionProjectId)) {
      this.productionProjectId = "";
      this.exportManifest = { artifacts: [] };
    }
    const linkedUserId = this.activeProjectId ? `set:${this.activeProjectId}` : "";
    if (!linkedUserId) {
      this.productionProjectId = "";
      this.exportManifest = { artifacts: [] };
      this.professionalSpecification = { spec: null, catalog: { groups: [], summary: {} }, revisions: [] };
      return;
    }
    const linkedProject = this.professionalProjects.find((project) => project.user_id === linkedUserId) || null;
    const currentProject = this.professionalProjects.find((project) => project.id === this.productionProjectId);
    let shouldLoadExport = false;
    if (currentProject?.user_id !== linkedUserId) {
      this.productionProjectId = linkedProject?.id || "";
      this.exportManifest = { artifacts: [] };
      shouldLoadExport = Boolean(this.productionProjectId);
    }
    if (!this.productionProjectId && linkedProject) {
      this.productionProjectId = linkedProject.id;
      this.exportManifest = { artifacts: [] };
      shouldLoadExport = true;
    }
    if (shouldLoadExport) await this.loadProfessionalExport(this.productionProjectId);
    if (this.productionProjectId) await this.loadProfessionalSpecification(this.productionProjectId);
  },

  async loadProfessionalSpecification(songId) {
    if (!songId) {
      this.professionalSpecification = { spec: null, catalog: { groups: [], summary: {} }, revisions: [] };
      this.aceConfigurationDraft = null;
      this.acePlanReview = null;
      this.acePlanLyricsDraft = null;
      this.acePlanProjectId = "";
      return;
    }
    const requestedSongId = String(songId);
    const response = await fetch(apiUrl(`/api/pro/projects/${encodeURIComponent(requestedSongId)}/spec`));
    const payload = await this.readApiPayload(response, { spec: null, catalog: { groups: [], summary: {} }, revisions: [] });
    if (this.productionProjectId !== requestedSongId) return;
    this.professionalSpecification = payload.data;
    if (!this.specProposalBusy) this.specProposal = payload.data?.technical_proposal || null;
    if (this.aceConfigurationDraft && this.aceConfigurationRevision !== payload.data?.spec?.revision?.revision_id) {
      this.aceConfigurationDraft = null;
    }
    await this.loadAcePlan(requestedSongId);
  },

  async confirmProfessionalSpecification() {
    const songId = this.productionProjectId;
    const revisionId = this.specificationRevision?.revision_id || "";
    if (!songId || !revisionId || this.confirmingSpecification) return;
    this.confirmingSpecification = true;
    try {
      const response = await fetch(apiUrl(`/api/pro/projects/${encodeURIComponent(songId)}/spec/confirm`), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ revision_id: revisionId }),
      });
      const payload = await this.readApiPayload(response, {});
      if (!payload.ok) {
        this.addMessage(payload.detail || "No se pudo confirmar la especificacion.");
        await this.loadProfessionalSpecification(songId);
        return;
      }
      this.professionalSpecification = payload.data;
      await this.loadProfessionalProjects();
      this.addMessage("Configuracion de la cancion confirmada en una nueva revision.");
    } catch (error) {
      this.addMessage(`No se pudo confirmar la configuracion: ${error?.message || "error de red"}`);
    } finally {
      this.confirmingSpecification = false;
    }
  },

  async ensureProductionProjectForActiveSet() {
    if (!this.activeProjectId) return "";
    await this.loadProfessionalProjects();
    const linkedUserId = `set:${this.activeProjectId}`;
    const existing = this.professionalProjects.find((project) => project.user_id === linkedUserId);
    if (existing) {
      this.productionProjectId = existing.id;
      return existing.id;
    }
    return this.createProfessionalProjectFromActiveSet({ quiet: true });
  },

  async createProfessionalProjectFromActiveSet(options = {}) {
    if (!this.activeProjectId) {
      this.addMessage("Carga un set desde Biblioteca antes de crear el proyecto profesional.");
      return "";
    }
    const response = await fetch(apiUrl("/api/pro/projects"), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        title: this.activeProjectTitle,
        project_name: this.activeProjectTitle,
        user_id: `set:${this.activeProjectId}`,
        source_set_id: this.activeProjectId,
        description: this.activeProjectDescription,
      }),
    });
    const payload = await this.readApiPayload(response, {});
    if (!payload.ok) {
      this.addMessage(payload.detail || "No se pudo crear el proyecto profesional.");
      return "";
    }
    this.productionProjectId = payload.data.project?.id || "";
    await this.loadProfessionalProjects();
    if (!options.quiet) {
      this.addMessage("Proyecto preparado. Revisa la definición, guarda la configuración para validarla y confirma antes de generar.");
    }
    return this.productionProjectId;
  },

  async saveProductionMetadata() {
    if (!this.activeProjectId) {
      this.saveError = "Selecciona un proyecto desde Biblioteca antes de guardar la descripcion.";
      this.addMessage(this.saveError);
      return false;
    }
    if (this.savingPhase) return false;
    this.savingPhase = "production";
    this.saveError = "";
    try {
    const response = await fetch(apiUrl(`/api/projects/${this.activeProjectId}/description`), {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ description: this.projectSet.description }),
    });
    const payload = await this.readApiPayload(response, {});
    if (!payload.ok) {
      this.saveError = payload.detail || "No se pudo guardar la descripcion.";
      this.addMessage(this.saveError);
      return false;
    }
    this.activeProject = payload.data;
    this.selectedSet = payload.data.set;
    this.savingPhase = "";
    if (!await this.savePhaseData("production", { quiet: true })) return false;
    await this.loadSets();
    this.dirty = false;
    this.dirtyPhase = "";
    this.addMessage("Descripcion del proyecto activo guardada.");
    return true;
    } catch (error) {
      this.saveError = `No se pudo guardar Production: ${error?.message || "error de red"}`;
      this.addMessage(this.saveError);
      return false;
    } finally {
      this.savingPhase = "";
    }
  },

  async runProductionStep(step) {
    if (step.phase === 'LYRICS_GENERATION') {
      await this.navigateBuilderStep({ id: 'lyrics', tab: 'lyrics', selector: '.editor-shell' });
      this.addMessage('Solicita y revisa la propuesta en Letra; guarda explícitamente antes de continuar.');
      return;
    }
    if (step.phase === 'SONG_SPEC_COLLECTION' && (this.dirty || this.aceConfigurationDraft)) {
      this.addMessage('Guarda o descarta los cambios pendientes antes de consultar sobre la ficha guardada.');
      return;
    }
    if (this.productionRunningPhase) {
      this.addMessage("Production ya esta ejecutando una accion. Espera a que termine antes de lanzar otra.");
      return;
    }
    if (step.canRun === false) {
      if (step.phase !== "SONG_SPEC_COLLECTION" && this.specificationRevision?.user_confirmation_status !== "confirmed") {
        this.addMessage("Revisa y confirma la ficha completa de la cancion antes de ejecutar esta fase.");
      } else {
        this.addMessage("Ejecuta primero la fase actual de Production; las fases posteriores se habilitan cuando existan sus artefactos.");
      }
      return;
    }
    if (!step.requires) {
      const preparedId = await this.ensureProductionProjectForActiveSet();
      this.addMessage(preparedId ? "Production preparado. Pulsa de nuevo la accion para ejecutarla." : "Selecciona un proyecto desde Biblioteca primero.");
      return;
    }
    this.productionRunningPhase = step.phase;
    const requestedRevision = this.specificationRevision?.revision_id;
    this.addMessage(`${step.label}: ejecutando...`);
    try {
      const response = await fetch(apiUrl(step.url), {
        method: step.method,
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(step.phase === "SONG_SPEC_COLLECTION" ? {
          message: this.productionSpecMessage,
          spec_revision_id: requestedRevision,
        } : {}),
      });
      const payload = await this.readApiPayload(response, {});
      if (!payload.ok) {
        this.addMessage(payload.detail || `No se pudo ejecutar ${step.label}.`);
        await this.loadProfessionalProjects();
        await this.loadResources();
        return;
      }
      if (step.phase === 'SONG_SPEC_COLLECTION' && payload.data?.gemma) {
        if (this.productionProjectId !== step.requires || this.specificationRevision?.revision_id !== requestedRevision || this.dirty) return;
        this.addMessage(payload.data.gemma.message);
        if (payload.data.handoff?.task?.status !== 'completed') return;
        this.addMessage('La ficha sigue sin cambios. Revisa las recomendaciones en Idea y guarda tus decisiones; la propuesta técnica de Qwen se solicita por separado.');
        return;
      }
      await this.loadProfessionalProjects();
      await this.loadResources();
      if (step.requires) await this.loadProfessionalSpecification(step.requires);
      if (step.requires) await this.loadProfessionalExport(step.requires);
      this.addMessage(`${step.label}: ${payload.data?.project?.current_phase || "completado"}`);
    } catch (_error) {
      this.addMessage(`${step.label}: la accion no respondio. Revisa la actividad y vuelve a intentar.`);
      await this.loadProfessionalProjects();
      await this.loadResources();
    } finally {
      this.productionRunningPhase = "";
    }
  },

  async generateLocalFinalSong() {
    if (!this.canGenerateLocalFinalSong) {
      this.addMessage(this.localFinalStatusMessage);
      await this.loadProviders();
      await this.loadResources();
      return;
    }
    const response = await fetch(apiUrl("/api/local-final-song"), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ set_id: this.activeProjectId }),
    });
    const payload = await this.readApiPayload(response, {});
    if (!payload.ok) {
      this.addMessage(payload.detail || "No se pudo iniciar la generacion final local.");
      return;
    }
    this.localFinalJob = payload.data;
    this.addMessage(this.localFinalJob.message || "Generacion final local iniciada.");
    this.scheduleLocalFinalPoll();
    await this.loadProviders();
    await this.loadResources();
  },

  scheduleLocalFinalPoll() {
    if (this.localFinalPollTimer) clearTimeout(this.localFinalPollTimer);
    this.localFinalPollTimer = setTimeout(() => this.pollLocalFinalJob(), 5000);
  },

  async pollLocalFinalJob() {
    const previousStatus = this.localFinalJob?.status || "idle";
    await this.loadLocalFinalJob();
    if (this.localFinalJob.status === "running") return;
    if (this.localFinalPollTimer) {
      clearTimeout(this.localFinalPollTimer);
      this.localFinalPollTimer = null;
    }
    await this.loadProviders();
    await this.loadResources();
    if (previousStatus === "running") this.addMessage(this.localFinalJob.message || "Generacion final local actualizada.");
  },

  async loadProfessionalExport(songId) {
    if (!songId) {
      this.exportManifest = { artifacts: [] };
      return;
    }
    const requestedSongId = String(songId);
    const linkedUserId = this.activeProjectId ? `set:${this.activeProjectId}` : "";
    const requestedProject = this.professionalProjects.find((project) => project.id === requestedSongId);
    if (linkedUserId && requestedProject && requestedProject.user_id !== linkedUserId) return;
    this.exportManifest = { song_id: requestedSongId, artifacts: [] };
    const response = await fetch(apiUrl(`/api/pro/projects/${songId}/export`));
    const payload = await this.readApiPayload(response, { artifacts: [] });
    const currentProject = this.professionalProjects.find((project) => project.id === requestedSongId);
    if (this.productionProjectId && this.productionProjectId !== requestedSongId) return;
    if (linkedUserId && currentProject && currentProject.user_id !== linkedUserId) return;
    this.exportManifest = { ...payload.data, song_id: requestedSongId };
  },

  async saveLatestMp3() {
    this.downloadStatus = "Preparando descarga...";
    const mp3Artifact = this.exportables.find((item) => item.type === "final_song_mp3" && item.url);
    if (mp3Artifact) return this.downloadArtifact(mp3Artifact);
    let downloadUrl = "";
    if (this.productionProjectId) {
      downloadUrl = `/api/pro/projects/${encodeURIComponent(this.productionProjectId)}/artifacts/final_song_mp3/download`;
    } else if (this.activeProjectId) {
      downloadUrl = `/api/projects/${encodeURIComponent(this.activeProjectId)}/audio-exports/download?format=mp3`;
    }
    if (!downloadUrl) {
      const message = "Carga un proyecto antes de descargar el MP3 final.";
      this.downloadStatus = message;
      this.addMessage(message);
      return;
    }
    const response = await fetch(apiUrl(downloadUrl));
    if (!response.ok) {
      const payload = await response.json().catch(() => ({}));
      const message = payload.detail || "No se pudo descargar el MP3 final.";
      this.downloadStatus = message;
      this.addMessage(message);
      return;
    }
    await this.saveBlob(response, "song-ai-final-mix.mp3", "MP3");
  },

  async downloadArtifact(exportable) {
    if (!exportable.url) {
      this.addMessage(`${exportable.name} aun no esta disponible.`);
      return;
    }
    const response = await fetch(apiUrl(exportable.url));
    if (!response.ok) {
      const payload = await response.json().catch(() => ({}));
      this.addMessage(payload.detail || `No se pudo descargar ${exportable.name}.`);
      return;
    }
    await this.saveBlob(response, `${exportable.name}.bin`, exportable.name);
  },

  async saveBlob(response, fallbackName, label) {
    const blob = await response.blob();
    const filename = this.filenameFromDisposition(response.headers.get("content-disposition")) || fallbackName;
    if ("showSaveFilePicker" in window) {
      const handle = await window.showSaveFilePicker({ suggestedName: filename });
      const writable = await handle.createWritable();
      await writable.write(blob);
      await writable.close();
    } else {
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(url);
    }
    this.downloadStatus = `${label} descargado: ${filename}`;
    this.addMessage(this.downloadStatus);
  },

  filenameFromDisposition(disposition) {
    const match = disposition?.match(/filename="?([^"]+)"?/i);
    return match ? match[1] : "";
  },
};
