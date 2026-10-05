import { apiUrl } from "./api_client.js";

export const productionActions = {
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
  aceCandidateAudioUrl() {
    const checksum = this.aceCandidateJob?.result?.artifact?.metadata?.audio_evidence?.sha256;
    if (this.aceCandidateJob?.status !== "completed" || !checksum) return "";
    return apiUrl(`/api/pro/projects/${encodeURIComponent(this.productionProjectId)}/ace-candidates/${encodeURIComponent(this.aceCandidateJob.task_id)}/audio?audio_sha256=${encodeURIComponent(checksum)}`);
  },
  async loadAceCandidateJob(songId) {
    if (this.aceCandidateTimer) clearTimeout(this.aceCandidateTimer);
    const response = await fetch(apiUrl(`/api/pro/projects/${encodeURIComponent(songId)}/ace-candidates`));
    const payload = await this.readApiPayload(response, { job: null });
    if (this.productionProjectId !== songId) return;
    this.aceCandidateJob = payload.data?.job || null;
    if (["pending", "running", "cancelling"].includes(this.aceCandidateJob?.status)) {
      this.aceCandidateTimer = setTimeout(() => {
        if (this.productionProjectId === songId) this.loadAceCandidateJob(songId).catch(error => this.addMessage(`No se pudo consultar el trabajo: ${error.message}`));
      }, 3000);
    }
  },

  async startAceCandidateJob() {
    const songId = this.productionProjectId;
    if (!songId || !this.aceCandidateAuthorized || this.aceCandidateBusy) return;
    this.aceCandidateBusy = true;
    try {
      const response = await fetch(apiUrl(`/api/pro/projects/${encodeURIComponent(songId)}/ace-candidates`), {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ plan_sha256: this.acePlanReview?.plan?.plan_sha256, exploratory_audio_authorized: true }),
      });
      const payload = await this.readApiPayload(response, {});
      if (!payload.ok) return this.addMessage(payload.detail || "No se pudo iniciar el borrador.");
      if (this.productionProjectId !== songId) return;
      this.aceCandidateAuthorized = false;
      await this.loadAceCandidateJob(songId);
    } catch (error) {
      this.addMessage(`No se pudo iniciar: ${error?.message || "error de red"}`);
    } finally { this.aceCandidateBusy = false; }
  },
  async loadAcePlan(songId) {
    if (this.acePlanProjectId !== songId) {
      this.acePlanReview = null;
      this.acePlanLyricsDraft = null;
      this.acePlanLyricsConfirmed = false;
      this.acePlanProjectId = songId;
      this.aceCandidateAuthorized = false;
      this.aceCandidateJob = null;
    }
    const response = await fetch(apiUrl(`/api/pro/projects/${encodeURIComponent(songId)}/ace-plan`));
    const payload = await this.readApiPayload(response, { plan: null });
    if (this.productionProjectId !== songId) return;
    this.acePlanReview = payload.data?.plan || null;
    this.acePlanLyricsConfirmed = false;
    this.aceCandidateAuthorized = false;
    await this.loadAceCandidateJob(songId);
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
      else this.addMessage("Plan y letra aprobados. La ejecucion real y el sample representativo siguen pendientes.");
      await this.loadAcePlan(songId);
    } catch (error) {
      this.addMessage(`No se pudo aprobar: ${error?.message || "error de red"}`);
    } finally { this.acePlanBusy = false; }
  },
  openAceConfiguration() {
    const spec = this.professionalSpecification?.spec?.json_spec || {};
    this.aceConfigurationRevision = this.specificationRevision?.revision_id || "";
    this.aceConfigurationDraft = {
      task_type: spec.task_type || "text2music",
      ace_step_config: spec.ace_step_config || "acestep-v15-base",
      source_artifact_id: spec.source_artifact_id || "",
      instruction: spec.instruction || "",
      target_tracks: Array.isArray(spec.target_tracks) ? [...spec.target_tracks] : [],
      repainting_start: spec.repainting_start ?? 0,
      repainting_end: spec.repainting_end ?? -1,
      audio_cover_strength: spec.audio_cover_strength ?? 1,
      duration_tolerance_seconds: spec.duration_tolerance_seconds ?? null,
    };
  },

  async saveAceConfiguration() {
    const songId = this.productionProjectId;
    if (!songId || !this.aceConfigurationDraft || this.savingAceConfiguration) return;
    this.savingAceConfiguration = true;
    try {
      const response = await fetch(apiUrl(`/api/pro/projects/${encodeURIComponent(songId)}/ace-configuration`), {
        method: "PUT", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ revision_id: this.aceConfigurationRevision, values: {
          ...this.aceConfigurationDraft,
          duration_tolerance_seconds: this.aceConfigurationDraft.duration_tolerance_seconds === "" ? null : this.aceConfigurationDraft.duration_tolerance_seconds,
        } }),
      });
      const payload = await this.readApiPayload(response, {});
      if (!payload.ok) return this.addMessage(payload.detail || "No se pudo guardar la configuracion.");
      if (this.productionProjectId !== songId) return;
      this.professionalSpecification = payload.data;
      this.aceConfigurationDraft = null;
      await this.loadAcePlan(songId);
      this.addMessage("Entradas guardadas en una nueva revision. Revisa y confirma la ficha; aun no se genero audio.");
    } catch (error) {
      this.addMessage(`No se pudo guardar: ${error?.message || "error de red"}`);
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
      this.addMessage("Revisión guardada. La producción real sigue pendiente del sample representativo verificado.");
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
      this.addMessage("Production preparado para el proyecto activo. Ejecuta 'Enviar intent' para aprobar la especificacion y continuar el cierre completo.");
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
    this.addMessage(`${step.label}: ejecutando...`);
    try {
      const response = await fetch(apiUrl(step.url), {
        method: step.method,
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(step.phase === "SONG_SPEC_COLLECTION" ? { message: this.productionSpecMessage } : {}),
      });
      const payload = await this.readApiPayload(response, {});
      if (!payload.ok) {
        this.addMessage(payload.detail || `No se pudo ejecutar ${step.label}.`);
        await this.loadProfessionalProjects();
        await this.loadResources();
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
