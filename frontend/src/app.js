import { validPhaseRanges } from "./phase_range_validation.js";
import { createApp } from "vue";
import { emotionalControls, validEmotionalValues } from "./emotional_controls.js";
import { apiUrl, readApiPayload } from "./api_client.js";
import { productionActions } from "./production_actions.js";
import { capabilityControls } from "./ace_capability_controls.js";
import { proposalContext, proposalContextMatches } from "./assistant_proposal_context.js";
import { appendAppliedProposal } from "./assistant_proposal_queue.js";
import "./styles.css";
import "./design_system.css";
import { builderSteps, phaseToOpenAfterLoad } from "./song_builder_flow.js";
import { BuilderShell } from "./builder_shell.js";
import { StudioDelivery, studioDeliveryState } from "./studio_delivery.js";
import { SpecRevisionHistory } from "./spec_revision_history.js";
import { lyricsReplacementBlockReason } from "./lyrics_replacement_policy.js";
import { protectedLinesUnchanged } from "./lyric_line_protection.js";
import { canApplySectionProposal } from "./lyric_section_proposal.js";
import { builderProjectStatus } from "./builder_project_status.js";
import { BuilderProjectSummary } from "./builder_project_summary.js";
import { DecisionCard } from "./decision_card.js";
import { GenerationPreflight, generationPreflight } from "./generation_preflight.js";
import { GenerationStatus } from "./generation_status.js";
import { productionNextAction } from "./production_guidance.js";
import { ListeningDecision, ListeningReviewSummary } from "./listening_decision.js";
import { PlanRequestReview } from "./plan_request_review.js";
import { CandidateComparisonView } from "./candidate_comparison_view.js";
import { AudioWaveform } from "./audio_waveform.js";
import { StudioCandidateContext } from "./studio_candidate_context.js";
import { containDialogTab, syncDialog } from "./dialog_keyboard.js";

const ROUTE_BY_TAB = {
  library: "/library",
  intent: "/intent",
  lyrics: "/lyrics",
  "music-plan": "/music-plan",
  midi: "/midi",
  instrumental: "/instrumental",
  voice: "/voice",
  production: "/production",
};

const TAB_BY_ROUTE = Object.fromEntries(Object.entries(ROUTE_BY_TAB).map(([tab, route]) => [route, tab]));
for (const step of builderSteps) if (step.path) TAB_BY_ROUTE[step.path] = step.tab;

const PHASE_STATUS = {
  EMPTY: { icon: "○", label: "Vacio", color: "gray" },
  PROCESSING: { icon: "⟳", label: "Procesando", color: "blue" },
  READY: { icon: "✔", label: "Listo", color: "green" },
  DIRTY: { icon: "●", label: "Cambios sin guardar", color: "yellow" },
  OUTDATED: { icon: "⚠", label: "Desactualizado", color: "orange" },
  ERROR: { icon: "✖", label: "Error", color: "red" },
};

const DEPENDENCIES = {
  intent: ["lyrics", "music-plan", "midi", "instrumental", "voice", "production"],
  lyrics: ["music-plan", "midi", "voice", "production"],
  "music-plan": ["midi", "instrumental", "voice", "production"],
  midi: ["instrumental", "voice", "production"],
  instrumental: ["production"],
  voice: ["production"],
};

const INSPIRATION_CATALOG = [
  { tag: "lullaby suave", detail: "Tonos suaves, pulso lento y ambiente relajante." },
  { tag: "piano calido", detail: "Piano cercano, redondo, con ataque delicado." },
  { tag: "cinematografico intimo", detail: "Profundidad emocional sin volverse grandilocuente." },
  { tag: "ambient pad", detail: "Colchon armonico sutil para sostener la voz." },
  { tag: "cuento nocturno", detail: "Imagenes narrativas tiernas y sensacion de proteccion." },
  { tag: "minimal pop", detail: "Arreglo limpio, repeticion controlada y foco en melodia." },
  { tag: "strings suaves", detail: "Cuerdas largas, calidas, sin dramatismo excesivo." },
  { tag: "dream folk", detail: "Textura organica, respirada y humana." },
];

function nowLabel() {
  return new Date().toLocaleString("es-CO", {
    hour12: false,
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
}

function cloneJson(value) {
  return JSON.parse(JSON.stringify(value));
}

createApp({
  components: {SpecRevisionHistory, StudioDelivery, BuilderShell, BuilderProjectSummary, DecisionCard, GenerationPreflight, GenerationStatus, ListeningDecision, ListeningReviewSummary, PlanRequestReview, CandidateComparisonView, AudioWaveform, StudioCandidateContext},
  data() {
    return {
      activeTab: "library",
      pendingTab: "",
      showUnsavedModal: false,
      dirty: false,
      dirtyPhase: "",
      savingPhase: "",
      saveError: "",
      createError: "",
      creatingSet: false,
      createRequestId: "",
      createRequestSignature: "",
      preparingDraft: "",
      selectedDrafts: { instrumental: "", melody: "", lyrics: "" },
      defaultPhasePayloads: {},
      projectBaselinePayloads: {},
      dirtyOutdatedSnapshot: [],
      historyIndex: 0,
      pendingHistoryDelta: 0,
      outdatedPhases: [],
      tabs: [
        { id: "library", label: "Biblioteca", path: "/library", hint: "Proyectos vivos, favoritos, busqueda y carga rapida." },
        { id: "intent", label: "Intent", path: "/intent", hint: "Identidad emocional y musical de la cancion." },
        { id: "lyrics", label: "Lyrics", path: "/lyrics", hint: "Composicion narrativa por secciones editables." },
        { id: "music-plan", label: "Music Plan", path: "/music-plan", hint: "Direccion musical, estructura, dinamica y transiciones." },
        { id: "midi", label: "MIDI", path: "/midi", hint: "Composicion editable: melodia, acordes, timing y velocity." },
        { id: "instrumental", label: "Instrumental", path: "/instrumental", hint: "Escultura sonora, capas, texturas y previews." },
        { id: "voice", label: "Voice", path: "/voice", hint: "Direccion de interpretacion vocal por seccion." },
        { id: "production", label: "Production", path: "/production", hint: "Metadata, exportables y cierre del pipeline." },
      ],
      phaseDefinitions: [
        { id: "intent", label: "Intent", tooltip: "Identidad emocional, idioma, destinatario, BPM e instrumentos generales." },
        { id: "lyrics", label: "Lyrics", tooltip: "Letra cantable por secciones, variables y plantillas." },
        { id: "music-plan", label: "Music Plan", tooltip: "Plan tecnico musical con tonalidad, compas, dinamica y transiciones." },
        { id: "midi", label: "MIDI", tooltip: "Melodia guia, acordes, timing, velocity y humanizacion." },
        { id: "instrumental", label: "Instrumental", tooltip: "Audio instrumental, stems, texturas, capas y previews." },
        { id: "voice", label: "Voice", tooltip: "Interpretacion vocal, armonias, respiraciones y conversion opcional." },
        { id: "production", label: "Production", tooltip: "Mezcla, mastering, exportables y ZIP del proyecto." },
      ],
      options: {
        genres: [],
        moods: [],
        energies: [],
        bpm_presets: [],
        keys: [],
        instrument_families: {},
        vocal_styles: [],
        vocal_ranges: [],
        song_structures: [],
        languages: [],
        lyric_themes: [],
        placeholder_presets: {},
        help_texts: {},
      },
      intent: {
        description: "Cancion de cuna completa, tierna y poetica con soundtrack suave y voz cantada.",
        songType: "cancion de cuna",
        language: "Spanish",
        recipient: "Isabella",
        warmth: 82,
        energy: 22,
        nostalgia: 36,
        cinematic: 58,
        bpm: 72,
        key: "C major",
        vocalType: "femenina",
        instruments: ["piano", "music box", "soft pad", "strings"],
        inspirations: ["lullaby suave", "piano calido", "noche tranquila"],
        inspirationInput: "",
      },
      lyrics: {
        language: "Spanish",
        tone: "tender",
        theme: "lullaby for {name}",
        structure: "intro, verse 1, chorus, verse 2, bridge, final chorus, outro",
        placeholders: { name: "Isabella", image: "estrellita", promise: "siempre cuidarte" },
        templateSearch: "",
      },
      lyricsEditor: {
        selectedAssetId: "",
        content: "",
        path: "",
      },
      lyricSections: [
        { id: "intro-1", type: "INTRO", text: "Duerme suave, Isabella,\nla luna canta por ti." },
        { id: "verso-1", type: "VERSO", text: "Cierro mis manos al cielo,\npara guardar tu jardin." },
        { id: "coro-1", type: "CORO", text: "Duerme, mi amor, sin miedo,\nyo voy a estar aqui." },
      ],
      transformingSections: {},
      lyricTemplates: [],
      musicPlan: {
        bpm: 72,
        key: "C major",
        timeSignature: "4/4",
        progression: "C - G - Am - F",
        dynamicArc: "crece suavemente hasta el coro final",
        transition: "crescendo",
        sections: [
          { id: "intro", name: "Intro", seconds: 8, intensity: 18, transition: "ambient bridge" },
          { id: "verse-1", name: "Verse 1", seconds: 24, intensity: 34, transition: "fill" },
          { id: "chorus", name: "Chorus", seconds: 28, intensity: 58, transition: "crescendo" },
          { id: "bridge", name: "Bridge", seconds: 18, intensity: 42, transition: "ambient bridge" },
          { id: "outro", name: "Outro", seconds: 10, intensity: 20, transition: "riser" },
        ],
        instrumentationNotes: "Piano suave al frente, cuerdas largas, pad calido y textura ligera de caja musical.",
      },
      midiPlan: {
        humanization: 18,
        velocity: 62,
        melodyDensity: 42,
        chordRhythm: "half notes",
        timingOffset: 0,
        swing: 8,
        tracks: [
          { id: "vocal", name: "Vocal melody", role: "melodia", enabled: true, color: "#7C8CFF" },
          { id: "chords", name: "Chords", role: "armonia", enabled: true, color: "#4ADE80" },
          { id: "bass", name: "Bass guide", role: "base", enabled: true, color: "#60A5FA" },
        ],
        notes: [
          { id: "n1", track: "vocal", pitch: "E4", start: 1, length: 2, velocity: 62 },
          { id: "n2", track: "vocal", pitch: "G4", start: 4, length: 2, velocity: 68 },
          { id: "n3", track: "vocal", pitch: "A4", start: 7, length: 3, velocity: 64 },
          { id: "n4", track: "chords", pitch: "C3", start: 1, length: 4, velocity: 54 },
          { id: "n5", track: "chords", pitch: "G3", start: 6, length: 4, velocity: 54 },
          { id: "n6", track: "bass", pitch: "C2", start: 1, length: 3, velocity: 48 },
        ],
      },
      melody: {
        vocal_style: "soft lullaby singing",
        range_hint: "medium",
        structure: "intro, verse 1, chorus, verse 2, final chorus, outro",
        mood: "tender",
        energy: "low",
      },
      instrumental: {
        texture: "suave y envolvente",
        ambience: "noche calida",
        layers: ["piano", "strings", "ambient pad"],
        quality: "demo local",
        depth: 62,
        brightness: 38,
        movement: 44,
        stereoWidth: 58,
        stems: [
          { id: "piano", name: "Piano", role: "armonia", level: 78, muted: false, solo: false },
          { id: "strings", name: "Strings", role: "sosten", level: 54, muted: false, solo: false },
          { id: "pad", name: "Ambient pad", role: "ambiente", level: 46, muted: false, solo: false },
          { id: "music-box", name: "Music box", role: "detalle", level: 34, muted: false, solo: false },
        ],
      },
      voice: {
        mainVoice: "femenina suave",
        emotion: "tierna",
        performance: "susurrada y cantada con ternura",
        pronunciation: "clara, suave, vocales redondas",
        breaths: 28,
        humanization: 46,
        vibrato: 18,
        layerBlend: 40,
        harmonies: false,
        conversion: false,
        callResponse: false,
        layers: [
          { id: "lead", name: "Lead", role: "voz principal", level: 80, enabled: true },
          { id: "harmony-high", name: "Harmony high", role: "harmonia", level: 38, enabled: false },
          { id: "soft-choir", name: "Soft choir", role: "coro", level: 26, enabled: false },
        ],
        sectionDirection: [
          { id: "intro", section: "Intro", singer: "lead", voices: 1, mode: "solo", harmony: false },
          { id: "verse-1", section: "Verse 1", singer: "lead", voices: 1, mode: "solo", harmony: false },
          { id: "chorus", section: "Chorus", singer: "lead + harmony", voices: 2, mode: "coro suave", harmony: true },
          { id: "bridge", section: "Bridge", singer: "lead", voices: 1, mode: "call & response", harmony: false },
          { id: "outro", section: "Outro", singer: "soft choir", voices: 3, mode: "coro", harmony: true },
        ],
        sections: {},
      },
      projectSet: {
        project_name: "Cancion de cuna para Isabella",
        description: "Cancion de cuna completa, tierna y poetica con soundtrack suave y voz cantada.",
      },
      productionSummaryOpen: false,
      drafts: [],
      sets: [],
      selectedSet: null,
      activeProject: null,
      pendingActiveProjectId: "",
      professionalProjects: [],
      professionalSpecification: { spec: null, catalog: { groups: [], summary: {} }, revisions: [] },
      specRestoreBusy: false,
      confirmingSpecification: false,
      aceConfigurationDraft: null,
      aceConfigurationRevision: "",
      savingAceConfiguration: false,
      legacyMigrationPreview: null,
      legacyMigrationBusy: false,
      aceConfigurationOriginalDraft: null,
      acePlanReview: null,
      specProposal: null,
      specProposalBusy: false,
      specProposalError: "",
      assistantPendingPatch: null,
      fullLyricsProposal: null,
      appliedFullLyricsProposal: null,
      fullLyricsBusy: false,
      assistantAppliedPatches: [],
      builderSteps,
      emotionalControls,
      builderStepId: '',
      uiPanels: {},
      uiPanelsProjectId: '',
      uiStateSaveQueue: Promise.resolve(),
      pendingBuilderStep: null,
      pendingLyricDeletion: null,
      unlockedLyricSectionIds: [],
      unlockedLyricLineIds: [],
      unlockedLyricDirectionIds: [],
      lyricSectionProposals: {},
      acePlanLyricsDraft: null,
      acePlanLyricsConfirmed: false,
      acePlanBusy: false,
      acePlanProjectId: "",
      aceCandidateJob: null,
      aceCandidateHistory: [],
      aceComparisonTaskId: "",
      sourceImportBusy: false,
      sourceImportAuthorized: false,
      aceCandidateBusy: false,
      aceCandidateRequest: null,
      aceCandidateAuthorized: false,
      aceCandidateTimer: null,
      candidateListeningConfirmed: false,
      candidateListeningDecision: "",
      candidateListeningNotes: "",
      candidateListeningCriteria: {},
      sampleRepresentativityReport: null,
      sampleFeedbackDecision: "",
      sampleFeedbackNotes: "",
      sampleListeningReviewView: null,
      candidateListeningReview: null,
      candidateCorrection: { scope: "", start: null, end: null, target_tracks: [], instruction: "" },
      candidateCorrectionProposal: null,
      aceTrackOptions: [
        ["vocals", "Voz principal"], ["backing_vocals", "Coros"], ["drums", "Bateria"], ["bass", "Bajo"],
        ["guitar", "Guitarra"], ["keyboard", "Teclado"], ["percussion", "Percusion"], ["strings", "Cuerdas"],
        ["synth", "Sintetizador"], ["fx", "Efectos"], ["brass", "Metales"], ["woodwinds", "Vientos de madera"],
      ].map(([value, label]) => ({ value, label })),
      sampleCheckpointRunning: false,
      sampleListeningConfirmation: "",
      productionProjectId: "",
      productionRunningPhase: "",
      exportManifest: { artifacts: [] },
      favoriteProjects: {},
      archived: [],
      deleteDialog: {
        open: false,
        loading: false,
        setId: "",
        name: "",
        error: "",
      },
      librarySearch: "",
      tagSearch: "",
      gemmaAssistant: {
        question: "Que sigue para terminar esta cancion?",
        response: null,
        loading: false,
        error: "",
      },
      providers: {},
      studioStatus: {},
      localPipeline: {},
      systemStatus: { components: [], bootstrap: {} },
      showAdvancedSystem: false,
      resourceStatus: { snapshot: {}, readiness: { recommendations: [] }, settings: {} },
      resourceHistory: { snapshots: [] },
      resourceRefreshing: false,
      resourceAutoRefresh: true,
      resourceLastUpdated: "",
      resourceRefreshTimer: null,
      productionEventsSongId: "",
      productionEvents: [],
      uiClockNow: Date.now(),
      uiClockTimer: null,
      localFinalJob: { status: "idle", message: "Generacion final local no iniciada.", result: {} },
      localFinalPollTimer: null,
      projectPhases: { phases: [] },
      modelStatus: {},
      orchestrationStatus: {},
      tasks: [],
      modelRuns: [],
      projectEvents: [],
      jsonConfigs: [],
      messages: [],
      downloadStatus: "",
      savedPhaseData: {},
    };
  },
  computed: {
    studioDeliveryState() {
      return studioDeliveryState({projectId:this.activeProjectId,sample:this.activeSampleCheckpoint,
        sampleAudio:this.sampleAudioUrl,running:this.localFinalRunning,canGenerate:this.canGenerateLocalFinalSong,
        finalMessage:this.localFinalStatusMessage,exports:this.exportables,
        candidateAudio:this.aceCandidateAudioUrl(),candidateRunning:['pending','running','cancelling'].includes(this.aceCandidateJob?.status)});
    },
    generationPreflightState() {
      const activeSpec = this.professionalSpecification?.spec;
      const project = this.productionProjectId && activeSpec
        ? {...this.activeProject,music_spec_revision_id:activeSpec.revision?.revision_id,music_spec:activeSpec}
        : this.activeProject;
      return generationPreflight(project,this.acePlanReview,this.resourceStatus,this.dirty);
    },
    currentFinalAvailable() {
      const finalMetadata = this.exportManifest?.artifacts?.find(item => item.type === "final_song_wav")?.metadata || {};
      return Boolean(this.exportManifest?.song_id === this.productionProjectId
        && this.exportManifest?.quality?.export_ready === true
        && finalMetadata.ace_plan_id
        && finalMetadata.ace_plan_id === this.acePlanReview?.plan_id
        && finalMetadata.spec_revision_id === this.specificationRevision?.revision_id);
    },
    productionNextAction() {
      return productionNextAction({projectId:this.productionProjectId,dirty:this.dirty,
        editing:Boolean(this.aceConfigurationDraft),revision:this.specificationRevision,
        plan:this.acePlanReview,running:Boolean(this.productionRunningPhase),
        exportReady:this.currentFinalAvailable,
        resourceBlocked:this.resourceStatus?.readiness?.ready === false});
    },
    builderSummaryStatus() {
      return builderProjectStatus(this.activeProject, this.acePlanReview, this.dirty ? this.dirtyPhase : '');
    },
    lyricsReplacementBlocked() {
      return lyricsReplacementBlockReason(this.lyricSections, [...this.unlockedLyricSectionIds, ...this.unlockedLyricLineIds, ...this.unlockedLyricDirectionIds]);
    },
    currentBuilderStep() {
      const selected = builderSteps.find(step => step.id === this.builderStepId && step.tab === this.activeTab);
      return selected || builderSteps.find(step => step.tab === this.activeTab)
        || builderSteps.find(step => step.id === (this.activeTab === 'voice' ? 'sound' : 'composition'));
    },
    nextBuilderStep() {
      return builderSteps[builderSteps.findIndex(step => step.id === this.currentBuilderStep?.id) + 1] || null;
    },
    currentTab() {
      return this.tabs.find((tab) => tab.id === this.activeTab) || this.tabs[0];
    },
    activeProjectTitle() {
      return this.activeProject?.project?.project_name || this.selectedSet?.project_name || "Sin proyecto activo";
    },
    activeProjectDescription() {
      return this.activeProject?.project?.description || this.selectedSet?.description || "";
    },
    activeProjectId() {
      return this.activeProject?.set?.set_id || this.selectedSet?.set_id || "";
    },
    activeProfessionalProject() {
      const linkedUserId = this.activeProjectId ? `set:${this.activeProjectId}` : "";
      const byId = this.professionalProjects.find((project) => project.id === this.productionProjectId) || null;
      if (linkedUserId) {
        if (byId?.user_id === linkedUserId) return byId;
        return this.professionalProjects.find((project) => project.user_id === linkedUserId) || null;
      }
      return byId;
    },
    productionGlobalStatus() {
      if (!this.productionProjectId) return "Selecciona un proyecto";
      if (this.productionNextAction.target === "downloads") return "Canción disponible para esta revisión";
      if (this.productionNextAction.target === "spec") return "Revisar configuración";
      if (this.productionNextAction.target === "plan") return "Preparar y aprobar el plan";
      if (this.productionNextAction.target === "preflight") return "Revisar recursos";
      if (this.productionRunningPhase) return "Generación en curso";
      return "Listo para generar";
    },
    specificationCoverage() {
      const summary = this.professionalSpecification?.catalog?.summary || {};
      return {
        decided: Number(summary.decided || 0),
        total: Number(summary.total || 0),
        requiredDecided: Number(summary.required_decided || 0),
        required: Number(summary.required || 0),
      };
    },
    aceCapabilityControls() {
      return capabilityControls(this.professionalSpecification?.catalog, this.aceConfigurationDraft || {});
    },
    specificationRevision() {
      return this.professionalSpecification?.spec?.revision || null;
    },
    canConfirmSpecification() {
      const revision = this.specificationRevision;
      return Boolean(
        revision?.revision_id
        && revision?.deterministic_valid
        && revision?.user_confirmation_status !== "confirmed"
        && !(this.professionalSpecification?.spec?.missing_fields || []).length
      );
    },
    activeSampleCheckpoint() {
      return (this.activeProject?.samples || [])[0] || null;
    },
    sampleCheckpointStatus() {
      const sample = this.activeSampleCheckpoint;
      if (!sample) return { state: "missing", title: "Sample opcional", detail: "Puedes generar la canción completa con un set válido y el plan confirmado, o crear un fragmento para revisarlo primero.", ready: false };
      if (sample.freshness_status === "stale") return { state: "stale", title: "Sample desactualizado", detail: "Cambió la canción desde la última revisión. Si quieres usar este sample como evidencia, regénéralo; no bloquea generar la canción completa.", ready: false };
      if (sample.approval_status !== "approved") return { state: "pending", title: "Sample listo para revisar", detail: sample.audio_evidence ? "Escucha el audio y confirma que revisaste esta versión." : "Este checkpoint es mock y no contiene audio. Su aprobación solo valida el recorrido de prueba.", ready: false };
      return { state: "approved", title: sample.audio_evidence ? "Audio revisado" : "Checkpoint mock aprobado", detail: "La revisión corresponde a este sample. La canción completa requiere su propia evaluación; generar no exige sample previo.", ready: false };
    },
    sampleReviewKey() {
      const sample = this.activeSampleCheckpoint;
      return sample?.audio_evidence ? `${this.activeProjectId}:${sample.sample_id}:${sample.audio_evidence.sha256}` : "";
    },
    sampleAudioUrl() {
      const sample = this.activeSampleCheckpoint;
      if (!sample?.audio_evidence) return "";
      return apiUrl(`/api/sets/${encodeURIComponent(this.activeProjectId)}/samples/${encodeURIComponent(sample.sample_id)}/audio?audio_sha256=${encodeURIComponent(sample.audio_evidence.sha256)}`);
    },
    productionTimingEstimate() {
      const spec = this.activeProfessionalProject?.spec?.json_spec || {};
      const requestedSeconds = Number(spec.duration_seconds || this.musicPlanDuration || 0) || 0;
      const limits = this.localPipeline?.limits || {};
      const maxSeconds = Number(
        limits.max_full_song_duration_seconds
        || this.modelStatus?.local?.max_full_song_duration_seconds
        || requestedSeconds
        || 0,
      );
      const timeoutSeconds = Number(
        limits.local_command_timeout_seconds
        || this.modelStatus?.local?.local_command_timeout_seconds
        || 0,
      );
      const clampedSeconds = maxSeconds ? Math.min(requestedSeconds || maxSeconds, maxSeconds) : requestedSeconds;
      const fullSong = (this.localPipeline?.requirements || []).find((item) => item.role === "full_song") || {};
      const runtime = String(fullSong.runtime || "").trim();
      const gpuReady = runtime.includes("gpu") || runtime.includes("xpu");
      const cpuSlow = !gpuReady && (runtime.includes("cpu") || runtime.includes("slow"));
      let minMinutes = 0;
      let maxMinutes = 0;
      if (clampedSeconds > 0) {
        if (gpuReady) {
          minMinutes = Math.max(3, Math.ceil(clampedSeconds / 4));
          maxMinutes = Math.max(minMinutes + 2, Math.ceil(clampedSeconds / 1.5));
        } else if (cpuSlow) {
          minMinutes = Math.max(45, Math.ceil(clampedSeconds * 1.0));
          maxMinutes = Math.max(minMinutes + 30, Math.ceil(clampedSeconds * 2.5));
        } else {
          minMinutes = Math.max(10, Math.ceil(clampedSeconds / 2));
          maxMinutes = Math.max(minMinutes + 10, Math.ceil(clampedSeconds * 1.25));
        }
      }
      const maxEstimateSeconds = maxMinutes * 60;
      return {
        requestedSeconds,
        clampedSeconds,
        maxSeconds,
        timeoutSeconds,
        runtime: runtime || "unavailable",
        estimateLabel: minMinutes ? `${this.formatMinutes(minMinutes)} - ${this.formatMinutes(maxMinutes)}` : "Sin estimacion",
        songLengthLabel: clampedSeconds ? this.formatDuration(clampedSeconds) : "Sin duracion",
        requestedLabel: requestedSeconds ? this.formatDuration(requestedSeconds) : "Sin duracion",
        maxLabel: maxSeconds ? this.formatDuration(maxSeconds) : "Sin limite visible",
        timeoutLabel: timeoutSeconds ? this.formatDuration(timeoutSeconds) : "Sin timeout visible",
        clipped: Boolean(requestedSeconds && maxSeconds && requestedSeconds > maxSeconds),
        exceedsTimeout: Boolean(timeoutSeconds && maxEstimateSeconds > timeoutSeconds),
        cpuSlow,
      };
    },
    fullSongRuntimeInfo() {
      const fullSong = (this.localPipeline?.requirements || []).find((item) => item.role === "full_song") || {};
      const accelerator = fullSong.accelerator || {};
      const runtime = String(fullSong.runtime || "unavailable");
      const device = String(fullSong.device || accelerator.recommended_backend || "cpu");
      const deviceName = accelerator.xpu_device_name || accelerator.cuda_device_name || "";
      const xpuReady = Boolean(accelerator.xpu_available);
      const cpuActive = runtime.includes("cpu") || device === "cpu";
      return {
        provider: "ACE-Step",
        runtime,
        device,
        deviceName,
        activeLabel: deviceName ? `${device.toUpperCase()} / ${deviceName}` : device.toUpperCase(),
        fallbackReason: accelerator.fallback_reason || "",
        warning: xpuReady
          ? ""
          : cpuActive
            ? "CPU para audio pesado: puede tardar horas. Instala PyTorch XPU/driver Intel para usar la iGPU."
            : "",
      };
    },
    productionActivityLog() {
      const currentEvents = this.productionEventsSongId === this.productionProjectId
        ? this.productionEvents : (this.activeProfessionalProject?.events || []);
      const projectEvents = currentEvents.map((event) => ({
        id: event.event_id || event.id || `${event.created_at}-${event.phase}`,
        time: this.formatResourceTime(event.created_at),
        text: `${event.phase || "Production"}: ${event.message || event.status || ""}`,
      }));
      const seen = new Set();
      return [...projectEvents, ...this.messages]
        .filter((item) => {
          const key = String(item.text || "");
          if (seen.has(key)) return false;
          seen.add(key);
          return true;
        })
        .slice(0, 40);
    },
    inspirationCatalog() {
      return INSPIRATION_CATALOG;
    },
    intentPreview() {
      return [
        `${this.intent.songType} para ${this.intent.recipient}`,
        `${this.intent.language}, ${this.intent.bpm} BPM, ${this.intent.key}`,
        `Voz ${this.intent.vocalType}`,
        `Emocion: calidez ${this.intent.warmth}, energia ${this.intent.energy}, nostalgia ${this.intent.nostalgia}, cine ${this.intent.cinematic}`,
      ].join(" / ");
    },
    selectedInstrumentCount() {
      return this.intent.instruments.length;
    },
    allTags() {
      const tags = new Set(["suave", "warm", "epico", "piano", "cinematografico", "tierno", "ambiental"]);
      for (const songSet of this.sets) {
        this.tagsForSet(songSet).forEach((tag) => tags.add(tag));
      }
      return [...tags].sort();
    },
    suggestedTags() {
      const query = this.tagSearch.trim().toLowerCase();
      if (!query) return this.allTags.slice(0, 8);
      return this.allTags.filter((tag) => tag.includes(query)).slice(0, 8);
    },
    visibleLibrarySets() {
      const query = this.librarySearch.trim().toLowerCase();
      return this.sets.filter((songSet) => {
        const archived = this.archived.includes(songSet.set_id);
        const haystack = `${songSet.set_id} ${songSet.project_name} ${songSet.description || ""} ${this.tagsForSet(songSet).join(" ")}`.toLowerCase();
        if (query) return haystack.includes(query);
        return !archived;
      });
    },
    searchResultSets() {
      if (!this.librarySearch.trim()) return [];
      return this.visibleLibrarySets;
    },
    favoriteSets() {
      if (this.librarySearch.trim()) return [];
      return this.sets
        .filter((songSet) => !this.archived.includes(songSet.set_id))
        .filter((songSet) => Boolean(this.favoriteProjects[songSet.set_id]))
        .sort((a, b) => String(this.favoriteProjects[b.set_id]?.favorited_at || "").localeCompare(String(this.favoriteProjects[a.set_id]?.favorited_at || "")));
    },
    recentSets() {
      if (this.librarySearch.trim()) return [];
      return this.sets
        .filter((songSet) => !this.archived.includes(songSet.set_id))
        .filter((songSet) => !this.favoriteProjects[songSet.set_id])
        .slice()
        .sort((a, b) => String(b.updated_at || b.created_at).localeCompare(String(a.updated_at || a.created_at)))
        .slice(0, 5);
    },
    productionProjectsBySet() {
      return this.professionalProjects.reduce((index, project) => {
        const userId = String(project.user_id || "");
        if (userId.startsWith("set:")) index[userId.slice(4)] = project;
        return index;
      }, {});
    },
    draftReadiness() {
      const counts = this.drafts.reduce(
        (summary, draft) => {
          summary[draft.asset_type] = (summary[draft.asset_type] || 0) + 1;
          return summary;
        },
        { instrumental: 0, melody: 0, lyrics: 0 },
      );
      return [
        { label: "Instrumental", type: "instrumental", count: counts.instrumental || 0 },
        { label: "Melodia", type: "melody", count: counts.melody || 0 },
        { label: "Lyrics", type: "lyrics", count: counts.lyrics || 0 },
      ];
    },
    canCreateSet() {
      return !this.creatingSet && this.draftReadiness.every((item) => item.count > 0)
        && ["instrumental", "melody", "lyrics"].every((type) => this.drafts.some((draft) => draft.asset_type === type && draft.asset_id === this.selectedDrafts[type]));
    },
    lyricsDrafts() {
      return this.drafts.filter((draft) => draft.asset_type === "lyrics");
    },
    variableNames() {
      const text = this.sectionsToMarkdown();
      return [...new Set([...text.matchAll(/\{([A-Za-z0-9_-]+)\}/g)].map((match) => match[1]))];
    },
    lyricStats() {
      const text = this.lyricSections.map((section) => section.text).join("\n");
      const words = text.trim() ? text.trim().split(/\s+/).length : 0;
      return {
        sections: this.lyricSections.length,
        words,
        variables: this.variableNames.length,
      };
    },
    filteredLyricTemplates() {
      const query = this.lyrics.templateSearch.trim().toLowerCase();
      if (!query) return this.lyricTemplates;
      return this.lyricTemplates.filter((template) => `${template.name} ${template.created_at}`.toLowerCase().includes(query));
    },
    musicPlanDuration() {
      return this.musicPlan.sections.reduce((total, section) => total + Number(section.seconds || 0), 0);
    },
    musicPlanSummary() {
      return `${this.musicPlan.bpm} BPM / ${this.musicPlan.key} / ${this.musicPlan.timeSignature} / ${this.musicPlanDuration}s`;
    },
    midiSummary() {
      return `${this.midiPlan.tracks.filter((track) => track.enabled).length} tracks / velocity ${this.midiPlan.velocity} / humanizacion ${this.midiPlan.humanization}`;
    },
    instrumentalSummary() {
      return `${this.instrumental.stems.filter((stem) => !stem.muted).length} stems activos / ${this.instrumental.texture} / ${this.instrumental.ambience}`;
    },
    voiceSummary() {
      const activeLayers = this.voice.layers.filter((layer) => layer.enabled).length;
      const harmonySections = this.voice.sectionDirection.filter((section) => section.harmony).length;
      return `${this.voice.mainVoice} / ${this.voice.emotion} / ${activeLayers} capa(s) / ${harmonySections} seccion(es) con armonia`;
    },
    waveformBars() {
      return Array.from({ length: 48 }, (_, index) => {
        const wave = Math.sin(index * 0.72) * 0.5 + Math.sin(index * 0.21) * 0.5;
        return Math.max(14, Math.round(38 + wave * 26 + (index % 5) * 3));
      });
    },
    pianoRows() {
      return ["C5", "B4", "A4", "G4", "F4", "E4", "D4", "C4", "B3", "A3", "G3", "F3", "E3", "D3", "C3", "C2"];
    },
    exportables() {
      const manifestArtifacts = this.exportManifest?.artifacts || [];
      if (manifestArtifacts.length > 0) {
        return manifestArtifacts
          .filter((artifact) => ["final_song_mp3", "final_song_flac", "final_song_wav", "midi", "project_zip", "instrumental_wav", "vocals_wav", "mix_wav", "export_manifest_json"].includes(artifact.type))
          .map((artifact) => ({
            name: this.exportLabel(artifact.type),
            type: artifact.type,
            size: this.formatSize(artifact.size_bytes || 0),
            url: artifact.download_url,
            note: this.exportNote(artifact),
          }));
      }
      return [
        { name: "MP3", type: "final_song_mp3", size: "pendiente", url: "" },
        { name: "FLAC", type: "final_song_flac", size: "pendiente", url: "" },
        { name: "WAV", type: "final_song_wav", size: "pendiente", url: "" },
        { name: "ZIP proyecto completo", type: "project_zip", size: "pendiente", url: "" },
      ];
    },
    productionPipelineSteps() {
      const songId = this.activeProfessionalProject?.id || "";
      return [
        { phase: "SONG_SPEC_COLLECTION", label: "Idea", summary: "Asistencia sobre la ficha guardada; decisiones por revisar", action: "Consultar idea", method: "POST", url: `/api/pro/projects/${songId}/spec/messages`, requires: songId },
        { phase: "LYRICS_GENERATION", label: "Letra", summary: "Propuesta por revisar y guardar en el editor", action: "Revisar propuesta de letra", method: "POST", url: `/api/pro/projects/${songId}/lyrics`, requires: songId },
        { phase: "LYRICS_TECHNICAL_REVIEW", label: "Revision", summary: "Comprobación de reglas; aprobación del usuario y audio separadas", action: "Comprobar letra", method: "POST", url: `/api/pro/projects/${songId}/lyrics/review`, requires: songId },
        { phase: "MUSIC_PLAN_GENERATION", label: "Plan musical", summary: "BPM, tonalidad, estructura y dinamica", action: "Generar plan", method: "POST", url: `/api/pro/projects/${songId}/music-plan`, requires: songId },
        { phase: "MIDI_GENERATION", label: "MIDI", summary: "Melodia guia y base armonica editable", action: "Crear MIDI", method: "POST", url: `/api/pro/projects/${songId}/midi`, requires: songId },
        { phase: "INSTRUMENTAL_GENERATION", label: "Instrumental", summary: "Audio base desde el plan musical", action: "Generar instrumental", method: "POST", url: `/api/pro/projects/${songId}/instrumental`, requires: songId },
        { phase: "VOCAL_SYNTHESIS", label: "Voz", summary: "Voz cantada sincronizada con la letra", action: "Generar voz", method: "POST", url: `/api/pro/projects/${songId}/vocals`, requires: songId },
        { phase: "VOICE_CONVERSION", label: "Conversion", summary: "Color vocal opcional o voz personalizada", action: "Resolver conversion", method: "POST", url: `/api/pro/projects/${songId}/voice-conversion`, requires: songId },
        { phase: "MIXING", label: "Mezcla", summary: "Balance de instrumental y voz", action: "Mezclar", method: "POST", url: `/api/pro/projects/${songId}/mix`, requires: songId },
        { phase: "MASTERING", label: "Mastering", summary: "Cancion final con voz integrada", action: "Masterizar", method: "POST", url: `/api/pro/projects/${songId}/master`, requires: songId },
        { phase: "EXPORT", label: "Export", summary: "MP3, WAV, FLAC, MIDI y ZIP", action: "Preparar export", method: "POST", url: `/api/pro/projects/${songId}/export`, requires: songId },
      ];
    },
    productionProcessSteps() {
      const phaseOrder = this.productionPipelineSteps.map((step) => step.phase);
      const currentPhase = this.activeProfessionalProject?.current_phase || "";
      const currentIndex = phaseOrder.indexOf(currentPhase);
      const projectStatus = String(this.activeProfessionalProject?.status || "").toLowerCase();
      const latestEventByPhase = {};
      const events = [...(this.activeProfessionalProject?.events || [])].sort((a, b) => {
        const left = Date.parse(a.created_at || "") || 0;
        const right = Date.parse(b.created_at || "") || 0;
        return left - right;
      });
      for (const event of events) {
        latestEventByPhase[event.phase] = event;
      }
      const artifactTypes = new Set([
        ...(this.exportManifest?.artifacts || []).map((artifact) => artifact.type),
        ...(this.activeProfessionalProject?.artifacts || []).map((artifact) => artifact.type),
      ]);
      const completedByArtifact = {
        MIDI_GENERATION: ["midi"],
        INSTRUMENTAL_GENERATION: ["instrumental_wav"],
        VOCAL_SYNTHESIS: ["vocals_wav"],
        MIXING: ["mix_wav"],
        MASTERING: ["final_song_wav", "final_song_mp3", "final_song_flac"],
        EXPORT: ["project_zip", "export_manifest_json"],
      };
      const statusCopy = {
        disabled: { icon: "○", label: "Sin proyecto" },
        pending: { icon: "○", label: "Pendiente" },
        current: { icon: "⟳", label: "En curso" },
        complete: { icon: "✓", label: "Generado" },
        error: { icon: "✕", label: "Error" },
      };
      return this.productionPipelineSteps.map((step, index) => {
        const latestEvent = latestEventByPhase[step.phase] || {};
        const latestStatus = String(latestEvent.status || "").toLowerCase();
        const hasArtifact = (completedByArtifact[step.phase] || []).some((type) => artifactTypes.has(type));
        let state = "pending";
        const isBeforeCurrent = currentIndex > -1 && index < currentIndex;
        const isCurrent = currentIndex > -1 && index === currentIndex;
        if (!step.requires) {
          state = "disabled";
        } else if (latestStatus === "failed" || (projectStatus.includes("failed") && currentPhase === step.phase)) {
          state = "error";
        } else if (hasArtifact || latestStatus === "completed" || latestStatus === "skipped" || projectStatus === "completed" || isBeforeCurrent) {
          state = "complete";
        } else if (isCurrent) {
          state = "current";
        }
        const localRunning = this.productionRunningPhase === step.phase;
        const runningEvent = latestStatus === "running" ? latestEvent : null;
        const closedStatus = ["completed", "failed", "skipped"].includes(latestStatus);
        const projectClaimsRunning = isCurrent && !closedStatus && (projectStatus.includes("running") || projectStatus.includes("loading"));
        const isActuallyRunning = Boolean(runningEvent) || localRunning || projectClaimsRunning;
        if (isActuallyRunning && state !== "complete") {
          state = "current";
        }
        const copy = statusCopy[state] || statusCopy.pending;
        const stateLabel = state === "current" && !isActuallyRunning ? "Listo para ejecutar" : copy.label;
        const specConfirmed = this.specificationRevision?.user_confirmation_status === "confirmed";
        const requiresConfirmedSpec = step.phase !== "SONG_SPEC_COLLECTION";
        const blockedBySpec = requiresConfirmedSpec && !specConfirmed;
        const aceFinal = step.phase === "MASTERING" && this.professionalSpecification?.spec?.json_spec?.task_type === "text2music";
        const canRun = aceFinal
          ? Boolean(step.requires) && this.generationPreflightState.creativeReady && !this.aceConfigurationDraft
            && !this.productionRunningPhase && !isActuallyRunning
            && !["pending", "running", "cancelling"].includes(this.aceCandidateJob?.status)
          : Boolean(step.requires) && ["current", "complete", "error"].includes(state)
            && !this.productionRunningPhase && !isActuallyRunning && !blockedBySpec;
        return {
          ...step,
          state,
          canRun,
          stateIcon: copy.icon,
          stateLabel,
          statusDetail: aceFinal && !canRun
            ? "Confirma la ficha y aprueba un plan ACE-Step vigente para generar el final."
            : blockedBySpec
            ? "Confirma primero la ficha completa de la cancion."
            : latestEvent.message || step.summary,
          statusTime: latestEvent.created_at ? this.formatResourceTime(latestEvent.created_at) : "",
          startedAt: isActuallyRunning && runningEvent?.created_at ? this.formatResourceTime(runningEvent.created_at) : "",
          elapsedLabel: isActuallyRunning && runningEvent?.created_at ? this.formatElapsedSince(runningEvent.created_at) : "",
          activeModel: latestEvent.active_model || "",
          activeDevice: latestEvent.payload?.active_device || latestEvent.payload?.backend_active || "",
          requestedDevice: latestEvent.payload?.requested_device || "",
          buttonLabel: localRunning ? "Generando..." : state === "complete" ? "Rehacer" : step.action,
        };
      });
    },
    productionFlowSteps() {
      const byPhase = Object.fromEntries(this.productionPipelineSteps.map((step) => [step.phase, step]));
      return [
        {
          number: "1",
          title: "Preparar idea",
          purpose: "Revisa la idea, el instrumental, la melodía vocal y la letra antes de confirmar la configuración.",
          phases: "Idea → Instrumental, melodía vocal y letra → Revisar",
          action: null,
          actionLabel: "Preparar en los pasos del proyecto",
        },
        {
          number: "2",
          title: "Generar canción",
          purpose: "Ejecuta ACE-Step local para crear una canción completa con voz integrada.",
          phases: "Configuración y plan confirmados → Canción completa",
          action: byPhase.MASTERING,
          actionLabel: "Generar canción completa",
        },
        {
          number: "3",
          title: "Preparar descargas",
          purpose: "Revisa los archivos disponibles y descarga solo los que estén generados y verificados.",
          phases: "Studio → Archivos disponibles",
          action: byPhase.EXPORT,
          actionLabel: byPhase.EXPORT?.action || "Exportar",
        },
      ];
    },
    productionSpecMessage() {
      const duration = this.productionTimingEstimate.clampedSeconds || this.musicPlanDuration || 120;
      return [
        this.intent.description,
        `Tipo: ${this.intent.songType}`,
        `Destinatario: ${this.intent.recipient}`,
        `Idioma: ${this.intent.language}`,
        `Duracion ${duration} segundos`,
        `Voz ${this.voice.mainVoice || this.intent.vocalType}`,
        `Instrumentos ${this.intent.instruments.join(", ")}`,
        `${this.musicPlan.bpm} bpm en ${this.musicPlan.key}`,
        `Estructura ${this.lyrics.structure}`,
        `Salida mp3 y wav`,
      ].join(". ");
    },
    bootstrapRunning() {
      return this.systemStatus.bootstrap?.status === "running";
    },
    localFinalRunning() {
      return this.localFinalJob?.status === "running";
    },
    canGenerateLocalFinalSong() {
      return Boolean(this.localPipeline.ready) && !this.bootstrapRunning && !this.localFinalRunning;
    },
    audioResourcesReady() {
      return this.resourceStatus?.readiness?.ready !== false;
    },
    localFinalStatusMessage() {
      if (this.localFinalRunning) return this.localFinalJob.message || "Generando cancion final local en segundo plano.";
      if (this.localFinalJob?.status === "error") return this.localFinalJob.message || "La generacion final local fallo.";
      if (this.localFinalJob?.status === "ready") return this.localFinalJob.message || "Cancion final local lista.";
      if (this.bootstrapRunning) return "Bootstrap preparando dependencias locales. Consulta estado en unos minutos.";
      if (this.localPipeline.ready) return "Pipeline local listo: Full Song puede generar cancion con voz integrada.";
      return `Falta configurar: ${this.localPipeline.missing?.join(", ") || "requisitos locales"}.`;
    },
    resourceSnapshot() {
      return this.resourceStatus?.snapshot || {};
    },
    resourceRecommendations() {
      return this.resourceStatus?.readiness?.recommendations || [];
    },
    acceleratorSummary() {
      const accelerators = this.resourceSnapshot.accelerators || {};
      const nodes = accelerators.device_nodes || {};
      const driCount = (nodes.dri || []).length;
      const dxgCount = (nodes.dxg || []).length;
      const nvidiaCount = (nodes.nvidia || []).length;
      const accelCount = (nodes.accel || []).length;
      if (accelerators.xpu_available) return `Intel XPU disponible (${accelerators.xpu_device_name || "iGPU Intel"})`;
      if (accelerators.cuda_available) return `CUDA disponible (${nvidiaCount || 1} dispositivo)`;
      if (driCount || dxgCount) return `iGPU visible (${driCount + dxgCount} dispositivo Linux)`;
      if (accelCount) return `Acelerador visible (${accelCount} dispositivo)`;
      return "Sin acelerador visible";
    },
    acceleratorDetail() {
      const accelerators = this.resourceSnapshot.accelerators || {};
      const cpu = accelerators.cpu_affinity_count || accelerators.visible_cpu_count || 0;
      const fallback = accelerators.fallback_reason ? ` ${accelerators.fallback_reason}` : "";
      return `${cpu || "--"} CPUs visibles. ${accelerators.note || "Sin diagnostico de aceleradores."}${fallback}`;
    },
    resourceDecisionClass() {
      const decision = String(this.resourceStatus?.readiness?.decision || "");
      if (this.resourceStatus?.readiness?.ready === false) return "blocked";
      if (decision.startsWith("warning")) return "warning";
      return "ready";
    },
    resourceHistoryRows() {
      return (this.resourceHistory.snapshots || []).slice(0, 8).map((snapshot) => ({
        id: snapshot.id,
        time: this.formatResourceTime(snapshot.created_at),
        phase: snapshot.phase,
        ram: `${Math.round(snapshot.ram_available_mb || 0)} MB`,
        swap: `${Math.round(snapshot.swap_free_mb || 0)} MB`,
        cpu: `${Math.round(snapshot.cpu_percent || 0)}%`,
        decision: snapshot.decision || "observed",
      }));
    },
    systemComponentMap() {
      return (this.systemStatus.components || []).reduce((items, component) => {
        items[component.id] = component;
        return items;
      }, {});
    },
    essentialSystemItems() {
      const components = this.systemComponentMap;
      const gemma = components.llm_gemma || {};
      const qwen = components.llm_qwen || {};
      const fullSong = components.full_song || {};
      const ffmpeg = components.ffmpeg || {};
      const models = components.song_ai_model_root || {};
      const cache = components.song_ai_provider_cache || {};
      const bootstrap = components.bootstrap || {};
      const textReady = gemma.status === "ready" && qwen.status === "ready";
      const audioReady = fullSong.status === "ready" && ffmpeg.status === "ready";
      const storageReady = models.status === "ready" && cache.status === "ready";
      return [
        {
          id: "text_models",
          label: "Modelos de texto",
          status: textReady ? "ready" : "missing",
          detail: textReady ? "Gemma y Qwen disponibles para la charla creativa." : "Falta Gemma o Qwen; usa Preparar/reiniciar o Recrear modelos.",
        },
        {
          id: "audio_engine",
          label: "Audio local",
          status: audioReady ? "ready" : "missing",
          detail: audioReady ? "ACE-Step y ffmpeg listos para generar y exportar canción final." : fullSong.detail || "Falta preparar ACE-Step o ffmpeg.",
        },
        {
          id: "storage",
          label: "Almacenamiento local",
          status: storageReady ? "ready" : "missing",
          detail: storageReady ? "Modelos y datos persistentes en data/." : "Revisa data/models y data/providers.",
        },
        {
          id: "bootstrap",
          label: "Preparación",
          status: bootstrap.status === "running" ? "running" : "ready",
          detail: bootstrap.detail || "Dependencias y modelos se preparan localmente.",
        },
      ];
    },
    advancedSystemComponents() {
      const hidden = new Set(["sqlite", "ffmpeg", "bootstrap", "llm_gemma", "llm_qwen", "full_song", "song_ai_model_root", "song_ai_provider_cache"]);
      return (this.systemStatus.components || []).filter((component) => !hidden.has(component.id));
    },
  },
  async mounted() {
    this.defaultPhasePayloads = Object.fromEntries(this.phaseDefinitions.map(({ id }) => [id, cloneJson(this.phasePayload(id))]));
    window.history.replaceState({ songAiIndex: 0 }, "", window.location.pathname);
    this.popstateHandler = (event) => this.handlePopstate(event);
    this.beforeUnloadHandler = (event) => {
      if (!this.dirty) return;
      event.preventDefault();
      event.returnValue = "";
    };
    window.addEventListener("popstate", this.popstateHandler);
    this.restoreLocalUiState();
    this.activateFromPath(window.location.pathname);
    await this.loadOptions();
    await this.refreshDrafts();
    await this.loadSets();
    await this.restoreActiveProject();
    await this.loadProfessionalProjects();
    await this.loadProviders();
    await this.loadResources();
    await this.loadLocalFinalJob();
    await this.loadOrchestration();
    await this.loadJsonConfigs();
    this.startResourceAutoRefresh();
    this.startUiClock();
    await this.$nextTick();
    const copilot = document.querySelector('.gemma-footer');
    if (copilot && window.ResizeObserver) {
      this.copilotResizeObserver = new ResizeObserver(() => {
        document.documentElement.style.setProperty('--copilot-height', `${Math.ceil(copilot.getBoundingClientRect().height)}px`);
      });
      this.copilotResizeObserver.observe(copilot);
    }
  },
  beforeUnmount() {
    this.copilotResizeObserver?.disconnect();
    document.documentElement.style.removeProperty('--copilot-height');
    window.removeEventListener("popstate", this.popstateHandler);
    window.removeEventListener("beforeunload", this.beforeUnloadHandler);
    this.stopResourceAutoRefresh();
    this.stopUiClock();
  },
  watch: {
    async saveError(message) {
      if (!message) return;
      await this.$nextTick();
      document.querySelector(this.showUnsavedModal ? '#unsaved-changes-dialog [role="alert"]' : '#phase-save-error')?.focus();
    },
    showUnsavedModal(open) { return syncDialog(this, 'unsaved-changes-dialog', open); },
    'deleteDialog.open'(open) { return syncDialog(this, 'delete-project-dialog', open); },
    pendingLyricDeletion(value) { return syncDialog(this, 'remove-section-dialog', Boolean(value)); },
    dirty(value) {
      if (value) window.addEventListener("beforeunload", this.beforeUnloadHandler);
      else window.removeEventListener("beforeunload", this.beforeUnloadHandler);
    },
  },
  methods: {
    navigateSummaryAction(action) {
      if (action.tab === 'production') return this.navigateBuilderStep(builderSteps.find(step => step.id === action.stepId));
      return this.requestNavigation(action.tab);
    },
    goToProductionNextAction() {
      const target = this.productionNextAction.target;
      if (target === "library") {
        return this.requestNavigation("library");
      }
      if (target === "spec") return this.navigateBuilderStep(builderSteps.find(step => step.id === "review"));
      if (target === "downloads") return this.navigateBuilderStep(builderSteps.find(step => step.id === "studio"));
      const element = document.getElementById(`production-${target}`);
      element?.scrollIntoView({behavior:"smooth",block:"start"});
      element?.focus({preventScroll:true});
    },
    lyricProposalContext() {
      return JSON.stringify({baseline:this.projectBaselinePayloads, intent:this.intent, lyrics:this.lyrics, voice:this.voice});
    },
    canApplyLyricProposal(section) {
      return canApplySectionProposal(this.lyricSectionProposals[section.id], section, this.activeProjectId, this.lyricProposalContext());
    },
    discardLyricProposal(sectionId) {
      const proposals = {...this.lyricSectionProposals};
      delete proposals[sectionId];
      this.lyricSectionProposals = proposals;
    },
    applyLyricProposal(section) {
      if (!this.canApplyLyricProposal(section)) {
        this.addMessage('La propuesta ya no corresponde al proyecto o a sus decisiones actuales. Descártala y solicita otra.');
        return;
      }
      section.text = this.lyricSectionProposals[section.id].text;
      this.discardLyricProposal(section.id);
      this.markDirty('lyrics');
      this.addMessage('Propuesta aplicada al borrador de esta sección. Revisa y guarda para conservarla.');
    },
    toggleLyricDirectionLock(section) {
      section.direction_locked = !section.direction_locked;
      const baseline = this.projectBaselinePayloads?.lyrics?.lyricSections?.find(item => item.id === section.id);
      this.unlockedLyricDirectionIds = this.unlockedLyricDirectionIds.filter(id => id !== section.id);
      if (!section.direction_locked && baseline?.direction_locked) this.unlockedLyricDirectionIds.push(section.id);
      this.markDirty('lyrics');
    },
    editLyricSection(section, event) {
      if (!protectedLinesUnchanged(section, event.target.value)) {
        event.target.value = section.text;
        this.addMessage('La edición cambia una línea protegida o su posición. Desbloquéala primero.');
        return;
      }
      section.text = event.target.value;
      this.markDirty('lyrics');
    },
    toggleLyricLineLock(section, index) {
      if (section.locked) return;
      const indexes = section.protected_lines || [];
      section.protected_lines = indexes.includes(index) ? indexes.filter(i => i !== index) : [...indexes, index];
      const key = `${section.id}:${index}`;
      const baseline = this.projectBaselinePayloads?.lyrics?.lyricSections?.find(item => item.id === section.id);
      this.unlockedLyricLineIds = this.unlockedLyricLineIds.filter(id => id !== key);
      if (!section.protected_lines.includes(index) && baseline?.protected_lines?.includes(index)) this.unlockedLyricLineIds.push(key);
      this.markDirty('lyrics');
    },
    toggleLyricSectionLock(section) {
      const baseline = this.projectBaselinePayloads?.lyrics?.lyricSections?.find(item => item.id === section.id);
      section.locked = !section.locked;
      this.unlockedLyricSectionIds = this.unlockedLyricSectionIds.filter(id => id !== section.id);
      if (!section.locked && baseline?.locked) this.unlockedLyricSectionIds.push(section.id);
      this.markDirty('lyrics');
    },
    selectLyricSection(id) {
      const card = document.getElementById(`lyric-section-${id}`);
      card?.scrollIntoView({block:'center'});
      card?.querySelector('textarea')?.focus();
    },
    syncLyricStructure() {
      this.lyrics.structure = this.lyricSections.map(section => section.type.toLowerCase()).join(', ');
      this.markDirty('lyrics');
    },
    confirmRemoveLyricSection() {
      const index = this.lyricSections.findIndex(section => section.id === this.pendingLyricDeletion?.id);
      if (index >= 0 && !this.lyricSections[index].locked && !this.lyricSections[index].protected_lines?.length && !this.lyricSections[index].direction_locked && this.lyricSections.length > 1) {
        this.lyricSections.splice(index, 1);
        this.syncLyricStructure();
      }
      this.pendingLyricDeletion = null;
    },
    panelOpen(key) { return this.uiPanelsProjectId === this.activeProjectId && this.uiPanels[key] === true; },
    rememberPanel(event) {
      const key = event.target?.dataset?.uiPanel;
      if (!key || !this.activeProjectId || this.uiPanelsProjectId !== this.activeProjectId) return;
      const open = event.target.open;
      if (Boolean(this.uiPanels[key]) === open) return;
      this.uiPanels = { ...this.uiPanels, [key]:open };
      this.persistActivePhase();
    },
    navigateStudioDelivery(destination) {
      if (destination === 'library') return this.requestNavigation('library');
      if (destination === 'review') return this.navigateBuilderStep(builderSteps.find(step => step.id === 'review'));
      const selectors={sample:'.sample-checkpoint-panel',candidate:'.studio-panel',review:'.specification-panel',final:'.final-delivery-panel'};
      this.focusBuilderTarget({selector:selectors[destination] || '.specification-panel'});
    },
    containDialogTab,
    focusBuilderTarget(step) {
      const target = document.querySelector(step?.selector || '.topbar');
      if (!target) return;
      target.setAttribute('tabindex', '-1');
      target.focus({preventScroll:true});
      target.scrollIntoView({block:'start',behavior:'auto'});
    },
    async navigateBuilderStep(step) {
      if (!step) return;
      if (this.dirty && this.activeProjectId && step.tab !== this.activeTab) {
        this.requestNavigation(step.tab);
        this.pendingBuilderStep = step;
        return;
      }
      this.requestNavigation(step.tab);
      if (this.activeTab !== step.tab) return;
      this.builderStepId = step.id;
      if (step.path && window.location.pathname !== step.path) {
        window.history.pushState({ songAiIndex: ++this.historyIndex }, "", step.path);
      }
      this.persistActivePhase();
      await this.$nextTick();
      this.focusBuilderTarget(step);
    },
    ...productionActions,
    addMessage(text) {
      this.messages.unshift({
        id: `${Date.now()}-${Math.random().toString(16).slice(2)}`,
        time: nowLabel(),
        text,
      });
    },
    restoreLocalUiState() {
      const storedFavorites = JSON.parse(localStorage.getItem("song-ai:favorites") || "{}");
      this.favoriteProjects = Array.isArray(storedFavorites)
        ? Object.fromEntries(storedFavorites.map((id) => [id, { favorited_at: nowLabel() }]))
        : storedFavorites;
      this.archived = JSON.parse(localStorage.getItem("song-ai:archived") || "[]");
      this.lyricTemplates = JSON.parse(localStorage.getItem("song-ai:lyric-templates") || "[]");
      this.pendingActiveProjectId = localStorage.getItem("song-ai:active-project-id") || "";
    },
    persistLocalUiState() {
      localStorage.setItem("song-ai:favorites", JSON.stringify(this.favoriteProjects));
      localStorage.setItem("song-ai:archived", JSON.stringify(this.archived));
      localStorage.setItem("song-ai:lyric-templates", JSON.stringify(this.lyricTemplates));
    },
    async restoreActiveProject() {
      const setId = String(this.pendingActiveProjectId || "").trim();
      if (!setId || !this.sets.some((songSet) => songSet.set_id === setId)) return;
      await this.loadProject(setId, { preserveRoute: true, quiet: true });
    },
    activateFromPath(path, push = false) {
      const tab = TAB_BY_ROUTE[path] || "library";
      this.activeTab = tab;
      const routeStep = builderSteps.find(step => step.path === path);
      this.builderStepId = routeStep?.id || (tab === "production" ? "review" : "");
      if (push) window.history.pushState({ songAiIndex: ++this.historyIndex }, "", path);
      if (tab === "production") {
        this.loadResources({ silent: true });
        const projectId = this.activeProfessionalProject?.id || this.productionProjectId;
        if (projectId) this.loadProfessionalExport(projectId);
      }
      this.persistActivePhase(tab);
    },
    requestNavigation(tab) {
      if (tab === this.activeTab) return;
      if (this.dirty && this.activeProjectId) {
        this.pendingTab = tab;
        this.pendingHistoryDelta = 0;
        this.saveError = "";
        this.showUnsavedModal = true;
        return;
      }
      this.activateFromPath(ROUTE_BY_TAB[tab], true);
    },
    discardAndContinue() {
      this.fullLyricsProposal = null;
      this.appliedFullLyricsProposal = null;
      this.lyricSectionProposals = {};
      this.unlockedLyricSectionIds = [];
      this.unlockedLyricLineIds = [];
      this.unlockedLyricDirectionIds = [];
      this.assistantAppliedPatches = [];
      this.restorePhase(this.dirtyPhase);
      this.outdatedPhases = [...this.dirtyOutdatedSnapshot];
      this.dirty = false;
      this.dirtyPhase = "";
      this.showUnsavedModal = false;
      this.completePendingNavigation();
      this.pendingTab = "";
      this.saveError = "";
    },
    cancelNavigation() {
      this.pendingBuilderStep = null;
      this.pendingTab = "";
      this.pendingHistoryDelta = 0;
      this.saveError = "";
      this.showUnsavedModal = false;
    },
    async saveAndContinue() {
      if (this.savingPhase) return;
      this.saveError = "";
      const saved = await this.saveCurrentPhase();
      if (!saved) return;
      this.showUnsavedModal = false;
      this.completePendingNavigation();
      this.pendingTab = "";
    },
    completePendingNavigation() {
      const builderStep = this.pendingBuilderStep;
      this.pendingBuilderStep = null;
      if (this.pendingHistoryDelta) {
        const delta = this.pendingHistoryDelta;
        this.pendingHistoryDelta = 0;
        window.history.go(delta);
      } else if (this.pendingTab) {
        this.activateFromPath(ROUTE_BY_TAB[this.pendingTab], true);
        if (builderStep && this.activeTab === builderStep.tab) {
          this.navigateBuilderStep(builderStep);
        }
      }
    },
    handlePopstate(event) {
      const nextIndex = Number(event.state?.songAiIndex);
      const delta = Number.isFinite(nextIndex) ? nextIndex - this.historyIndex : -1;
      if (this.dirty && this.activeProjectId && delta) {
        this.pendingTab = TAB_BY_ROUTE[window.location.pathname] || "library";
        this.pendingHistoryDelta = delta;
        this.saveError = "";
        this.showUnsavedModal = true;
        window.history.go(-delta);
        return;
      }
      this.historyIndex = Number.isFinite(nextIndex) ? nextIndex : this.historyIndex;
      this.activateFromPath(window.location.pathname);
    },
    markDirty(phase = this.activeTab) {
      if (!this.dirty) this.dirtyOutdatedSnapshot = [...this.outdatedPhases];
      this.dirty = true;
      this.dirtyPhase = phase;
      this.outdatedPhases = [...new Set([...(this.outdatedPhases || []), ...(DEPENDENCIES[phase] || [])])];
    },
    phaseStatus(phaseId) {
      if (this.dirty && this.dirtyPhase === phaseId) return "DIRTY";
      if (this.outdatedPhases.includes(phaseId)) return "OUTDATED";
      if (this.activeProjectId) {
        if (phaseId === "production") return this.productionSidebarStatus();
        return this.persistedEditorPhaseStatus(phaseId);
      }
      return "EMPTY";
    },
    persistedEditorPhaseStatus(phaseId) {
      const phase = this.savedPhaseData?.[phaseId] || {};
      const rawStatus = String(phase.phase_status || phase.status || "").toUpperCase();
      if (!rawStatus || rawStatus === "NOT_CREATED") return "EMPTY";
      if (rawStatus === "INITIALIZED") return "EMPTY";
      if (rawStatus === "DRAFT") return "DIRTY";
      return this.normalizePhaseStatus(rawStatus);
    },
    productionSidebarStatus() {
      if (!this.activeProfessionalProject) return "EMPTY";
      if (this.productionRunningPhase) return "PROCESSING";
      const projectStatus = String(this.activeProfessionalProject.status || "").toLowerCase();
      if (projectStatus.includes("failed") || projectStatus.includes("interrupted")) return "ERROR";
      if (projectStatus.includes("running") || projectStatus.includes("loading")) return "PROCESSING";
      const processSteps = this.productionProcessSteps || [];
      if (processSteps.some((step) => step.state === "error")) return "ERROR";
      if (processSteps.some((step) => step.state === "current")) return "PROCESSING";
      if (this.exportManifest?.artifacts?.length || processSteps.some((step) => step.phase === "EXPORT" && step.state === "complete")) return "READY";
      return "EMPTY";
    },
    phaseUi(phaseId) {
      const status = this.phaseStatus(phaseId);
      const copy = PHASE_STATUS[status] || PHASE_STATUS.EMPTY;
      const phase = this.savedPhaseData?.[phaseId] || {};
      const persistedLabel = this.phaseStatusLabel(phase.phase_status || phase.status || "");
      return { ...copy, label: status === "READY" ? (persistedLabel || copy.label) : copy.label };
    },
    normalizePhaseStatus(status) {
      const value = String(status || "").toLowerCase();
      if (!value) return "";
      if (value.includes("error") || value.includes("failed")) return "ERROR";
      if (value.includes("running") || value.includes("progress") || value.includes("processing")) return "PROCESSING";
      if (value.includes("draft")) return "DIRTY";
      if (value.includes("initialized") || value.includes("not_created")) return "EMPTY";
      if (value.includes("pending") || value.includes("pend")) return "EMPTY";
      if (value.includes("saved") || value.includes("complete") || value.includes("ready") || value.includes("approved") || value.includes("aprob")) return "READY";
      return "READY";
    },
    phaseStatusLabel(status) {
      const value = String(status || "").toLowerCase();
      if (!value) return "";
      if (value.includes("error") || value.includes("failed")) return "Con errores";
      if (value.includes("running") || value.includes("progress") || value.includes("processing")) return "En progreso";
      if (value.includes("draft")) return "Borrador";
      if (value.includes("initialized")) return "Inicializada";
      if (value.includes("not_created")) return "Pendiente";
      if (value.includes("approved") || value.includes("aprob")) return "Aprobada por el usuario";
      if (value.includes("pending") || value.includes("pend")) return "Pendiente";
      if (value.includes("saved") || value.includes("complete") || value.includes("ready")) return "Completada";
      return status;
    },
    async saveCurrentPhase() {
      if (this.activeTab === "production") {
        return this.saveProductionMetadata();
      } else {
        return this.savePhaseData(this.activeTab);
      }
    },
    async loadOptions() {
      const response = await fetch(apiUrl("/api/options"));
      const payload = await response.json();
      this.options = payload.data;
    },
    async loadProviders() {
      const [providersResponse, studioResponse, modelResponse, localPipelineResponse, systemResponse, phasesResponse] = await Promise.all([
        fetch(apiUrl("/api/providers")),
        fetch(apiUrl("/api/studio/status")),
        fetch(apiUrl("/api/models/status")),
        fetch(apiUrl("/api/local-pipeline/status")),
        fetch(apiUrl("/api/system/status")),
        fetch(apiUrl(`/api/projects/phases${this.activeProjectId ? `?set_id=${this.activeProjectId}` : ""}`)),
      ]);
      this.providers = (await this.readApiPayload(providersResponse, {})).data;
      this.studioStatus = (await this.readApiPayload(studioResponse, {})).data;
      this.modelStatus = (await this.readApiPayload(modelResponse, {})).data;
      this.localPipeline = (await this.readApiPayload(localPipelineResponse, {})).data;
      this.systemStatus = (await this.readApiPayload(systemResponse, {})).data;
      this.projectPhases = (await this.readApiPayload(phasesResponse, { phases: [] })).data;
    },
    async loadResources(options = {}) {
      if (this.resourceRefreshing && !options.force) return;
      this.resourceRefreshing = true;
      try {
        const [statusResponse, historyResponse] = await Promise.all([
          fetch(apiUrl("/api/resources/status")),
          fetch(apiUrl("/api/resources/history?limit=25")),
        ]);
        this.resourceStatus = (await this.readApiPayload(statusResponse, this.resourceStatus)).data;
        this.resourceHistory = (await this.readApiPayload(historyResponse, { snapshots: [] })).data;
        this.resourceLastUpdated = nowLabel();
      } catch (error) {
        this.addMessage(`No se pudo transformar la seccion: ${error?.message || "error de red"}`);
      } finally {
        this.resourceRefreshing = false;
      }
    },
    async checkAudioReadiness() {
      this.resourceRefreshing = true;
      const response = await fetch(apiUrl("/api/resources/check-audio-readiness"), { method: "POST" });
      const payload = await this.readApiPayload(response, {});
      if (!payload.ok) {
        this.resourceRefreshing = false;
        this.addMessage(payload.detail || "No se pudo revisar recursos.");
        return;
      }
      await this.loadResources({ force: true });
      this.addMessage(payload.data.readiness?.message || "Recursos revisados.");
    },
    async refreshProductionActivity() {
      const songId = this.productionProjectId;
      if (!songId) return;
      try {
        const response = await fetch(apiUrl(`/api/pro/projects/${encodeURIComponent(songId)}/events`));
        const payload = await this.readApiPayload(response, { events: [] });
        if (songId !== this.productionProjectId || !payload.ok) return;
        this.productionEventsSongId = songId;
        this.productionEvents = payload.data.events || [];
      } catch (_) {
        // La actividad conserva la última lectura si falla una actualización automática.
      }
    },
    startResourceAutoRefresh() {
      this.stopResourceAutoRefresh();
      this.resourceRefreshTimer = setInterval(() => {
        if (!this.resourceAutoRefresh || this.activeTab !== "production" || this.builderStepId !== "generate" || document.hidden) return;
        this.loadResources({ silent: true });
        this.refreshProductionActivity();
      }, 10000);
    },
    stopResourceAutoRefresh() {
      if (!this.resourceRefreshTimer) return;
      clearInterval(this.resourceRefreshTimer);
      this.resourceRefreshTimer = null;
    },
    toggleResourceAutoRefresh() {
      this.resourceAutoRefresh = !this.resourceAutoRefresh;
      if (this.resourceAutoRefresh) {
        this.loadResources({ silent: true });
        this.refreshProductionActivity();
        this.startResourceAutoRefresh();
      }
    },
    startUiClock() {
      this.stopUiClock();
      this.uiClockTimer = setInterval(() => {
        this.uiClockNow = Date.now();
      }, 1000);
    },
    stopUiClock() {
      if (!this.uiClockTimer) return;
      clearInterval(this.uiClockTimer);
      this.uiClockTimer = null;
    },
    async loadOrchestration() {
      const [statusResponse, tasksResponse, runsResponse, eventsResponse] = await Promise.all([
        fetch(apiUrl("/api/orchestration/status")),
        fetch(apiUrl("/api/tasks")),
        fetch(apiUrl("/api/model-runs")),
        fetch(apiUrl("/api/project-events")),
      ]);
      this.orchestrationStatus = (await statusResponse.json()).data;
      this.tasks = (await tasksResponse.json()).data;
      this.modelRuns = (await runsResponse.json()).data;
      this.projectEvents = (await eventsResponse.json()).data;
    },
    async refreshDrafts() {
      const response = await fetch(apiUrl("/api/drafts"));
      const payload = await response.json();
      this.drafts = payload.data;
      for (const type of ["instrumental", "melody", "lyrics"]) {
        if (!this.drafts.some((draft) => draft.asset_type === type && draft.asset_id === this.selectedDrafts[type])) {
          this.selectedDrafts[type] = "";
        }
      }
    },
    async loadSets() {
      const response = await fetch(apiUrl("/api/sets"));
      const payload = await response.json();
      this.sets = payload.data;
    },
    async loadJsonConfigs() {
      const response = await fetch(apiUrl("/api/json-configs"));
      const payload = await response.json();
      this.jsonConfigs = payload.data;
    },
    async readApiPayload(response, fallbackData = {}) {
      return readApiPayload(response, fallbackData);
    },
    async loadProject(setId, options = {}) {
      this.assistantPendingPatch = null;
      this.assistantAppliedPatches = [];
      this.specProposal = null;
      this.specProposalError = "";
      const response = await fetch(apiUrl(`/api/projects/${setId}`));
      const payload = await this.readApiPayload(response, {});
      if (!payload.ok) {
        this.addMessage(payload.detail || "No se pudo cargar el proyecto.");
        return;
      }
      this.productionProjectId = "";
      this.exportManifest = { artifacts: [] };
      this.uiPanels = { ...(payload.data.ui_state?.open_panels || {}) };
      this.uiPanelsProjectId = setId;
      this.activeProject = payload.data;
      this.sampleFeedbackDecision = "";
      this.sampleFeedbackNotes = "";
      this.sampleListeningConfirmation = "";
      this.selectedSet = payload.data.set;
      localStorage.setItem("song-ai:active-project-id", payload.data.set.set_id);
      this.projectSet.project_name = payload.data.project.project_name;
      this.projectSet.description = payload.data.project.description;
      this.intent.description = payload.data.project.description;
      const lyricsAsset = payload.data.assets.lyrics;
      this.lyricsEditor = {
        selectedAssetId: lyricsAsset.asset_id,
        content: lyricsAsset.content || "",
        path: lyricsAsset.content_path || "",
      };
      this.parseLyricsToSections();
      this.applySavedPhaseData(payload.data.phase_data || {});
      this.projectSet = { ...this.projectSet,
        project_name: payload.data.project.project_name,
        description: payload.data.project.description };
      if (!payload.data.phase_data?.lyrics) {
        this.lyricsEditor = { selectedAssetId: lyricsAsset.asset_id, content: lyricsAsset.content || "", path: lyricsAsset.content_path || "" };
        this.parseLyricsToSections();
      }
      if (!payload.data.phase_data?.intent) {
        const instrumentalIntent = payload.data.assets.instrumental.intent || {};
        this.intent = { ...this.intent, description: payload.data.project.description,
          bpm: instrumentalIntent.bpm ?? this.intent.bpm,
          key: instrumentalIntent.key || this.intent.key,
          instruments: [...(instrumentalIntent.instruments || this.intent.instruments)] };
      }
      if (!payload.data.phase_data?.lyrics) {
        const lyricIntent = payload.data.assets.lyrics.intent || {};
        this.lyrics = { ...this.lyrics,
          language: payload.data.assets.lyrics.metadata?.metadata?.language || this.lyrics.language,
          tone: lyricIntent.mood || this.lyrics.tone,
          placeholders: { ...(lyricIntent.placeholders || this.lyrics.placeholders) } };
      }
      if (!payload.data.phase_data?.voice) {
        const melodyIntent = payload.data.assets.melody.intent || {};
        this.voice = { ...this.voice, mainVoice: melodyIntent.vocal_style || this.voice.mainVoice };
      }
      this.captureProjectBaselines();
      this.projectEvents = payload.data.events;
      if (!options.quiet) this.addMessage(`Proyecto cargado con datos guardados: ${payload.data.project.project_name}`);
      await this.loadProviders();
      const productionId = await this.ensureProductionProjectForActiveSet();
      if (productionId) await this.loadProfessionalExport(productionId);
      const targetPhase = this.phaseToOpenAfterLoad(payload.data);
      const savedStep = builderSteps.find(step => step.id === payload.data?.ui_state?.builder_step);
      const routeStep = builderSteps.find(step => step.path === window.location.pathname);
      this.builderStepId = options.preserveRoute && routeStep ? routeStep.id : savedStep && savedStep.tab === targetPhase ? savedStep.id : targetPhase === 'production' ? 'review' : '';
      if (!options.preserveRoute) {
        this.activateFromPath(savedStep?.path || ROUTE_BY_TAB[targetPhase] || ROUTE_BY_TAB.intent, true);
      }
      await this.$nextTick();
      const focusStep = builderSteps.find(step => step.id === this.builderStepId);
      if (focusStep?.tab === this.activeTab && focusStep.selector) {
        this.focusBuilderTarget(focusStep);
      }
    },
    phaseToOpenAfterLoad(projectData) {
      return phaseToOpenAfterLoad(projectData, Object.keys(ROUTE_BY_TAB));
    },
    async persistActivePhase(phase = this.activeTab) {
      if (!this.activeProjectId || !ROUTE_BY_TAB[phase]) return;
      const projectId = this.activeProjectId;
      const builder_step = builderSteps.find(step => step.id === this.builderStepId && step.tab === phase)?.id || '';
      const open_panels = this.uiPanelsProjectId === projectId ? { ...this.uiPanels } : undefined;
      // Serialize writes so older navigation cannot overwrite the latest step.
      this.uiStateSaveQueue = this.uiStateSaveQueue.catch(() => {}).then(() => fetch(apiUrl(`/api/projects/${projectId}/ui-state`), {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ phase, builder_step, open_panels }),
      }));
      await this.uiStateSaveQueue.catch(() => {});
    },
    async createSet() {
      if (!this.canCreateSet || this.creatingSet) return;
      this.creatingSet = true;
      this.createError = "";
      const selection = { ...this.projectSet,
        instrumental_id: this.selectedDrafts.instrumental,
        melody_id: this.selectedDrafts.melody,
        lyrics_id: this.selectedDrafts.lyrics };
      const signature = JSON.stringify(selection);
      if (signature !== this.createRequestSignature) {
        this.createRequestId = crypto.randomUUID();
        this.createRequestSignature = signature;
      }
      try {
        const response = await fetch(apiUrl("/api/sets"), {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ ...selection, request_id: this.createRequestId }),
        });
        const payload = await this.readApiPayload(response, {});
        if (!payload.ok) throw new Error(payload.detail || "No se pudo crear el proyecto/set.");
        await this.loadSets();
        await this.loadProject(payload.data.id);
        await this.loadJsonConfigs();
        this.createRequestId = "";
        this.createRequestSignature = "";
      } catch (error) {
        this.createError = error?.message || "No se pudo crear el proyecto/set.";
        this.addMessage(this.createError);
      } finally {
        this.creatingSet = false;
      }
    },
    async createInstrumental() {
      const created = await this.createDraft(
        "/api/instrumentals",
        {
          genre: this.intent.songType,
          mood: "warm",
          bpm: this.intent.bpm,
          key: this.intent.key,
          instruments: this.intent.instruments,
          energy: this.intent.energy > 55 ? "medium" : "low",
        },
        "Instrumental guardado",
      );
      await this.refreshDrafts();
      if (created?.id) this.selectedDrafts.instrumental = created.id;
      return Boolean(created);
    },
    async createMelody() {
      const created = await this.createDraft(
        "/api/melodies",
        {
          vocal_style: this.voice.mainVoice || this.melody.vocal_style,
          range_hint: this.melody.range_hint,
          structure: this.lyrics.structure || this.melody.structure,
          mood: this.voice.emotion || this.melody.mood,
          energy: this.intent.energy > 55 ? "medium" : "low",
          bpm: this.intent.bpm,
          key: this.intent.key,
        },
        "Melodia guia guardada",
      );
      await this.refreshDrafts();
      if (created?.id) this.selectedDrafts.melody = created.id;
      return Boolean(created);
    },
    async requestFullLyricsProposal() {
      const songId = this.activeProject?.music_spec_song_id;
      if (!songId || this.fullLyricsBusy || this.dirty || this.lyricsReplacementBlocked) return;
      const revision = this.activeProject.music_spec_revision_id;
      this.fullLyricsProposal = null;
      this.fullLyricsBusy = true;
      try {
        const response = await fetch(apiUrl(`/api/pro/projects/${songId}/lyrics`), { method: 'POST' });
        const payload = await this.readApiPayload(response, {});
        if (!payload.ok) throw new Error(payload.detail || 'No se pudo proponer la letra.');
        if (this.activeProject?.music_spec_song_id !== songId || this.activeProject.music_spec_revision_id !== revision || this.dirty) {
          this.addMessage('La ficha o el borrador cambió durante la solicitud. No se cargó la propuesta.');
          return;
        }
        const proposal = payload.data.lyrics_proposal;
        this.fullLyricsProposal = proposal ? { ...proposal, task_id: payload.data.handoff.task.task_id } : null;
        this.addMessage(payload.data.handoff.summary);
      } catch (error) { this.addMessage(error.message || 'No se pudo proponer la letra.'); }
      finally { this.fullLyricsBusy = false; }
    },
    applyFullLyricsProposal() {
      const proposal = this.fullLyricsProposal;
      if (!proposal || proposal.source_project_id !== this.activeProject?.music_spec_song_id ||
          proposal.source_revision_id !== this.activeProject.music_spec_revision_id || this.lyricsReplacementBlocked || this.dirty) {
        return this.addMessage('La ficha cambió o hay cambios pendientes. Revisa y solicita una nueva propuesta.');
      }
      this.lyricsEditor.content = proposal.markdown;
      this.parseLyricsToSections();
      this.syncLyricStructure();
      this.appliedFullLyricsProposal = { task_id: proposal.task_id };
      this.fullLyricsProposal = null;
      this.addMessage('Propuesta cargada como borrador. Revísala y pulsa Guardar letra para confirmarla.');
    },
    async createLyrics() {
      const hasEditedSections = JSON.stringify(this.lyricSections) !== JSON.stringify(this.defaultPhasePayloads.lyrics?.lyricSections || []);
      const created = await this.createDraft("/api/lyrics", {
        ...this.lyrics, ...(hasEditedSections ? { content: this.sectionsToMarkdown() } : {}),
      }, "Letra guardada");
      await this.refreshDrafts();
      if (created?.id) {
        this.selectedDrafts.lyrics = created.id;
        await this.loadLyricsDraft(created.id);
      }
      return Boolean(created);
    },
    async prepareDraft(type) {
      if (this.preparingDraft) return;
      this.preparingDraft = type;
      this.createError = "";
      try {
        const action = { instrumental: this.createInstrumental, melody: this.createMelody, lyrics: this.createLyrics }[type];
        if (!action || !await action.call(this)) this.createError = `No se pudo preparar ${type}. Revisa la actividad e intentalo de nuevo.`;
      } catch (error) {
        this.createError = error?.message || `No se pudo preparar ${type}.`;
        this.addMessage(this.createError);
      } finally {
        this.preparingDraft = "";
      }
    },
    async createDraft(url, body, successLabel) {
      const controller = new AbortController();
      const timeoutId = window.setTimeout(() => controller.abort(), 20000);
      try {
        const response = await fetch(apiUrl(url), {
          method: "POST", headers: { "Content-Type": "application/json" },
          body: JSON.stringify(body), signal: controller.signal,
        });
        const payload = await this.readApiPayload(response, {});
        if (!payload.ok) throw new Error(payload.detail || "No se pudo preparar el draft.");
        this.addMessage(`${successLabel}: ${payload.data.id}`);
        return payload.data;
      } catch (error) {
        this.addMessage(error?.name === "AbortError" ? "La preparacion del draft agoto el tiempo de espera." : error?.message || "Error de red.");
        return null;
      } finally {
        window.clearTimeout(timeoutId);
      }
    },
    async loadLyricsDraft(assetId = this.lyricsEditor.selectedAssetId) {
      if (this.lyricsReplacementBlocked) return this.addMessage(this.lyricsReplacementBlocked);
      const projectId = this.activeProjectId;
      const originalSections = JSON.stringify(this.lyricSections);
      if (!assetId) {
        this.addMessage("Selecciona una letra para editar.");
        return;
      }
      const response = await fetch(apiUrl(`/api/lyrics/${assetId}`));
      const payload = await response.json();
      if (!payload.ok) {
        this.addMessage(payload.detail || "No se pudo cargar la letra.");
        return;
      }
      if (this.activeProjectId !== projectId || this.lyricsReplacementBlocked || JSON.stringify(this.lyricSections) !== originalSections) {
        return this.addMessage('La letra cambió durante la carga. No se sustituyó el borrador.');
      }
      this.lyricsEditor = { selectedAssetId: payload.data.asset_id, content: payload.data.content, path: payload.data.path };
      this.parseLyricsToSections();
      this.syncLyricStructure();
    },
    async saveLyricsDraft() {
      this.lyricsEditor.content = this.sectionsToMarkdown();
      const saved = await this.savePhaseData("lyrics", { quiet: true });
      if (!saved) return;
      this.dirty = false;
      this.dirtyPhase = "";
      this.addMessage("Letra guardada en el proyecto activo.");
    },
    parseLyricsToSections() {
      const lines = String(this.lyricsEditor.content || "").split(/\r?\n/);
      const sections = [];
      let current = null;
      for (const line of lines) {
        const heading = line.match(/^##\s+(.+)/);
        if (heading) {
          if (current) sections.push(current);
          current = { id: `${Date.now()}-${sections.length}`, type: heading[1].toUpperCase(), text: "" };
        } else if (current) {
          current.text += `${line}\n`;
        }
      }
      if (current) sections.push(current);
      if (sections.length > 0) {
        this.lyricSections = sections.map((section) => ({ ...section, text: section.text.trim() }));
      }
    },
    sectionsToMarkdown() {
      return this.lyricSections.map((section) => `## ${section.type}\n${section.text.trim()}`).join("\n\n").trim() + "\n";
    },
    addLyricSection(type = "VERSO") {
      this.lyricSections.push({ id: `${Date.now()}-${Math.random().toString(16).slice(2)}`, type, text: this.sectionStarter(type) });
      this.syncLyricStructure();
    },
    moveSection(index, direction) {
      const target = index + direction;
      if (target < 0 || target >= this.lyricSections.length) return;
      const sections = [...this.lyricSections];
      [sections[index], sections[target]] = [sections[target], sections[index]];
      this.lyricSections = sections;
      this.syncLyricStructure();
    },
    duplicateSection(index) {
      const original = this.lyricSections[index];
      if (!original) return;
      this.lyricSections.splice(index + 1, 0, { ...original, id: `${Date.now()}-${Math.random().toString(16).slice(2)}` });
      this.syncLyricStructure();
    },
    removeSection(index) {
      const section = this.lyricSections[index];
      if (!section || section.locked || section.protected_lines?.length || section.direction_locked || this.lyricSections.length <= 1) return;
      this.pendingLyricDeletion = {id:section.id, label:this.sectionDisplayName(section,index)};
    },
    async transformSection(index, mode) {
      const section = this.lyricSections[index];
      if (!section || section.locked || this.transformingSections[section.id]) return;
      const originalText = section.text;
      const projectId = this.activeProjectId;
      const context = this.lyricProposalContext();
      const sectionSnapshot = JSON.stringify(section);
      this.transformingSections = { ...this.transformingSections, [section.id]: mode };
      try {
        const response = await fetch(apiUrl("/api/lyrics/section-transform"), {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            mode,
            section_type: section.type,
            text: section.text,
            set_id: this.activeProjectId,
            section_id: section.id,
            section_draft: {...section},
            spec_revision_id: this.activeProject?.music_spec_revision_id,
            project_name: this.activeProjectTitle,
            description: this.activeProjectDescription,
            lyrics: { ...this.lyrics },
            intent: { ...this.intent },
          }),
        });
        const payload = await this.readApiPayload(response, {});
        if (!payload.ok) {
          this.addMessage(payload.detail || "No se pudo transformar la seccion con Gemma.");
          return;
        }
        const transformed = String(payload.data?.text || "").trim();
        if (!transformed) {
          this.addMessage("Gemma no devolvio texto para esta seccion.");
          return;
        }
        const proposal = {projectId, context, sectionSnapshot, text:transformed, originalText, mode,
          technicalReview:payload.data?.technical_handoff,
          source:payload.data?.mode === 'llama_cpp' ? 'Gemma' : 'Guía local (fallback o ejemplo)'};
        if (!this.lyricSections.includes(section) || !canApplySectionProposal(proposal, section, this.activeProjectId, this.lyricProposalContext())) {
          this.addMessage('La sección cambió durante la consulta. No se reemplazó el texto; puedes consultar de nuevo.');
          return;
        }
        this.lyricSectionProposals = {...this.lyricSectionProposals, [section.id]:proposal};
        this.addMessage(`Propuesta de ${proposal.source} lista para revisar. La letra no cambió.`);
      } finally {
        const next = { ...this.transformingSections };
        delete next[section.id];
        this.transformingSections = next;
      }
    },
    sectionStarter(type) {
      return {
        INTRO: "Respira la noche suave,\nla melodia empieza a abrir.",
        VERSO: "Una imagen clara y cantable,\nun detalle que pueda vivir.",
        "PRE-CORO": "Sube despacio la promesa,\nprepara el corazon para seguir.",
        CORO: "Frase central memorable,\nemocion simple para repetir.",
        "POST-CORO": "Eco corto, dulce y ligero,\npara dejar la idea latir.",
        PUENTE: "Cambia la mirada un momento,\nabre una puerta antes de volver.",
        BREAKDOWN: "Menos elementos, mas espacio,\nla voz queda cerca de la piel.",
        INTERLUDIO: "Melodia sin palabras,\nuna pausa para respirar.",
        SOLO: "Linea instrumental expresiva,\nresponde a la voz sin competir.",
        OUTRO: "Cierra suave la historia,\ndejando calma al final.",
      }[type] || "Nueva seccion cantable...";
    },
    sectionDisplayName(section, index) {
      const sameTypeBefore = this.lyricSections.slice(0, index + 1).filter((item) => item.type === section.type).length;
      return `${section.type} ${sameTypeBefore}`;
    },
    saveLyricTemplate() {
      const name = `${this.activeProjectTitle}-lyrics-${this.lyricTemplates.length + 1}`;
      this.lyricTemplates = [
        {
          id: `${Date.now()}-${Math.random().toString(16).slice(2)}`,
          name,
          sections: this.lyricSections.map((section) => ({ type: section.type, text: section.text,
            direction: section.direction || '', energy: section.energy || '',
            vocal_direction: section.vocal_direction || '', instrument_direction: section.instrument_direction || '' })),
          placeholders: { ...this.lyrics.placeholders },
          created_at: nowLabel(),
        },
        ...this.lyricTemplates,
      ];
      this.persistLocalUiState();
      this.addMessage(`Plantilla lyrics guardada: ${name}`);
    },
    addMusicSection() {
      this.musicPlan.sections.push({
        id: `${Date.now()}-${Math.random().toString(16).slice(2)}`,
        name: "Nueva seccion",
        seconds: 16,
        intensity: 40,
        transition: "fill",
      });
      this.markDirty("music-plan");
    },
    removeMusicSection(index) {
      this.musicPlan.sections.splice(index, 1);
      this.markDirty("music-plan");
    },
    moveMusicSection(index, direction) {
      const target = index + direction;
      if (target < 0 || target >= this.musicPlan.sections.length) return;
      const sections = [...this.musicPlan.sections];
      [sections[index], sections[target]] = [sections[target], sections[index]];
      this.musicPlan.sections = sections;
      this.markDirty("music-plan");
    },
    toggleMidiTrack(trackId) {
      const track = this.midiPlan.tracks.find((item) => item.id === trackId);
      if (!track) return;
      track.enabled = !track.enabled;
      this.markDirty("midi");
    },
    addMidiNote(trackId = "vocal") {
      this.midiPlan.notes.push({
        id: `${Date.now()}-${Math.random().toString(16).slice(2)}`,
        track: trackId,
        pitch: "C4",
        start: 2,
        length: 2,
        velocity: this.midiPlan.velocity,
      });
      this.markDirty("midi");
    },
    removeMidiNote(noteId) {
      this.midiPlan.notes = this.midiPlan.notes.filter((note) => note.id !== noteId);
      this.markDirty("midi");
    },
    noteStyle(note) {
      const track = this.midiPlan.tracks.find((item) => item.id === note.track);
      const row = Math.max(1, this.pianoRows.indexOf(note.pitch) + 1);
      return {
        gridColumn: `${note.start} / span ${note.length}`,
        gridRow: `${row}`,
        background: track?.color || "#7C8CFF",
        opacity: track?.enabled ? 0.9 : 0.24,
      };
    },
    toggleStemMute(stemId) {
      const stem = this.instrumental.stems.find((item) => item.id === stemId);
      if (!stem) return;
      stem.muted = !stem.muted;
      this.markDirty("instrumental");
    },
    toggleStemSolo(stemId) {
      const stem = this.instrumental.stems.find((item) => item.id === stemId);
      if (!stem) return;
      stem.solo = !stem.solo;
      this.markDirty("instrumental");
    },
    addInstrumentalLayer() {
      const name = `Layer ${this.instrumental.stems.length + 1}`;
      this.instrumental.stems.push({
        id: `${Date.now()}-${Math.random().toString(16).slice(2)}`,
        name,
        role: "textura",
        level: 42,
        muted: false,
        solo: false,
      });
      this.instrumental.layers = [...this.instrumental.layers, name];
      this.markDirty("instrumental");
    },
    toggleVoiceLayer(layerId) {
      const layer = this.voice.layers.find((item) => item.id === layerId);
      if (!layer) return;
      layer.enabled = !layer.enabled;
      this.markDirty("voice");
    },
    addVoiceLayer() {
      this.voice.layers.push({
        id: `${Date.now()}-${Math.random().toString(16).slice(2)}`,
        name: `Layer ${this.voice.layers.length + 1}`,
        role: "textura vocal",
        level: 32,
        enabled: true,
      });
      this.markDirty("voice");
    },
    removeVoiceLayer(layerId) {
      this.voice.layers = this.voice.layers.filter((layer) => layer.id !== layerId);
      this.markDirty("voice");
    },
    addVoiceSectionDirection() {
      this.voice.sectionDirection.push({
        id: `${Date.now()}-${Math.random().toString(16).slice(2)}`,
        section: `Seccion ${this.voice.sectionDirection.length + 1}`,
        singer: "lead",
        voices: 1,
        mode: "solo",
        harmony: false,
      });
      this.markDirty("voice");
    },
    removeVoiceSectionDirection(index) {
      this.voice.sectionDirection.splice(index, 1);
      this.markDirty("voice");
    },
    loadLyricTemplate(templateId) {
      if (this.lyricsReplacementBlocked) return this.addMessage(this.lyricsReplacementBlocked);
      const template = this.lyricTemplates.find((item) => item.id === templateId);
      if (!template) return;
      this.lyricSections = template.sections.map((section) => ({
        ...section,
        id: `${Date.now()}-${Math.random().toString(16).slice(2)}`,
      }));
      this.lyrics.placeholders = { ...template.placeholders };
      this.syncLyricStructure();
      this.addMessage(`Plantilla cargada en borrador: ${template.name}. Revisa y guarda para conservarla.`);
    },
    toggleFavorite(setId) {
      if (this.favoriteProjects[setId]) {
        const next = { ...this.favoriteProjects };
        delete next[setId];
        this.favoriteProjects = next;
      } else {
        this.favoriteProjects = {
          ...this.favoriteProjects,
          [setId]: { favorited_at: nowLabel() },
        };
      }
      this.persistLocalUiState();
    },
    archiveSet(setId) {
      this.archived = [...new Set([...this.archived, setId])];
      const nextFavorites = { ...this.favoriteProjects };
      delete nextFavorites[setId];
      this.favoriteProjects = nextFavorites;
      this.persistLocalUiState();
      this.addMessage("Proyecto archivado. Seguira disponible en busqueda.");
    },
    unarchiveSet(setId) {
      this.archived = this.archived.filter((id) => id !== setId);
      this.persistLocalUiState();
      this.addMessage("Proyecto restaurado a la biblioteca principal.");
    },
    isFavorite(setId) {
      return Boolean(this.favoriteProjects[setId]);
    },
    favoriteDate(setId) {
      return this.favoriteProjects[setId]?.favorited_at || "";
    },
    isArchived(setId) {
      return this.archived.includes(setId);
    },
    linkedProductionProject(songSet) {
      return this.productionProjectsBySet[String(songSet?.set_id || "")] || null;
    },
    projectLibraryState(songSet) {
      const setId = String(songSet?.set_id || "");
      if (this.isArchived(setId)) return { icon: "A", label: "Archivado", tone: "archived" };
      const project = this.linkedProductionProject(songSet);
      if (!project) return { icon: "♪", label: "Set listo", tone: "set" };
      const status = String(project.status || "").toLowerCase();
      const phase = String(project.current_phase || "");
      if (status.includes("running") || status.includes("loading")) return { icon: "↻", label: `Production en curso: ${phase}`, tone: "running" };
      if (status.includes("failed") || status.includes("interrupted")) return { icon: "!", label: `Production requiere revision: ${phase}`, tone: "error" };
      if (status === "completed" || phase === "EXPORT") return { icon: "✓", label: "Exportables generados", tone: "done" };
      return { icon: "P", label: `Production: ${phase || "preparado"}`, tone: "production" };
    },
    requestDeleteProject(setId) {
      const songSet = this.sets.find((item) => item.set_id === setId) || this.selectedSet || {};
      const project = this.linkedProductionProject(songSet);
      const status = String(project?.status || "").toLowerCase();
      if (status.includes("running") || status.includes("loading")) {
        this.addMessage("No se puede borrar un proyecto mientras Production esta ejecutando una fase.");
        return;
      }
      const name = songSet.project_name || setId;
      this.deleteDialog = {
        open: true,
        loading: false,
        setId,
        name,
        error: "",
      };
    },
    cancelDeleteProject() {
      if (this.deleteDialog.loading) return;
      this.deleteDialog = {
        open: false,
        loading: false,
        setId: "",
        name: "",
        error: "",
      };
    },
    async confirmDeleteProject() {
      const setId = this.deleteDialog.setId;
      const name = this.deleteDialog.name || setId;
      if (!setId || this.deleteDialog.loading) return;
      this.deleteDialog = { ...this.deleteDialog, loading: true, error: "" };
      const controller = new AbortController();
      const timeoutId = window.setTimeout(() => controller.abort(), 20000);
      try {
        const response = await fetch(apiUrl(`/api/projects/${setId}`), { method: "DELETE", signal: controller.signal });
        const payload = await this.readApiPayload(response, {});
        if (!payload.ok) {
          this.deleteDialog = {
            ...this.deleteDialog,
            loading: false,
            error: payload.detail || "No se pudo borrar el proyecto. Si acabas de actualizar el codigo, reinicia scripts\\run-local.ps1.",
          };
          this.addMessage(payload.detail || "No se pudo borrar el proyecto.");
          return;
        }

        const nextFavorites = { ...this.favoriteProjects };
        delete nextFavorites[setId];
        this.favoriteProjects = nextFavorites;
        this.archived = this.archived.filter((id) => id !== setId);
        if (this.selectedSet?.set_id === setId) this.selectedSet = null;
        if (this.activeProjectId === setId) {
          this.activeProject = null;
          this.productionProjectId = "";
          this.pendingActiveProjectId = "";
          localStorage.removeItem("song-ai:active-project-id");
        }
        this.persistLocalUiState();
        this.deleteDialog = {
          open: false,
          loading: false,
          setId: "",
          name: "",
          error: "",
        };
        this.addMessage(`Proyecto borrado: ${name}`);

        await Promise.allSettled([
          this.loadSets(),
          this.loadProfessionalProjects(),
          this.loadProjectPhases(),
        ]);
      } catch (error) {
        const message = error?.name === "AbortError"
          ? "El borrado no respondio en 20 segundos. Reinicia scripts\\run-local.ps1 y revisa si el proyecto ya desaparecio."
          : `No se pudo borrar el proyecto: ${error?.message || "error de red"}`;
        this.deleteDialog = {
          ...this.deleteDialog,
          loading: false,
          error: message,
        };
        this.addMessage(message);
      } finally {
        window.clearTimeout(timeoutId);
      }
    },
    tagsForSet(songSet) {
      const stopWords = new Set(["para", "con", "una", "este", "esta", "cancion", "proyecto", "completa", "desde"]);
      return `${songSet.project_name || ""} ${songSet.description || ""}`
        .toLowerCase()
        .split(/[^a-zA-Z0-9áéíóúñ]+/)
        .filter((token) => token.length > 3 && !stopWords.has(token))
        .slice(0, 6);
    },
    phasePayload(phase = this.activeTab) {
      const payloads = {
        intent: { intent: { ...this.intent, inspirationInput: "" } },
        lyrics: {
          lyrics: { ...this.lyrics },
          lyricSections: this.lyricSections.map((section) => ({ ...section })),
          lyricsEditor: {
            selectedAssetId: this.lyricsEditor.selectedAssetId,
            content: this.sectionsToMarkdown(),
            path: this.lyricsEditor.path,
          },
        },
        "music-plan": {
          musicPlan: {
            ...this.musicPlan,
            sections: this.musicPlan.sections.map((section) => ({ ...section })),
          },
        },
        midi: {
          midiPlan: {
            ...this.midiPlan,
            tracks: this.midiPlan.tracks.map((track) => ({ ...track })),
            notes: this.midiPlan.notes.map((note) => ({ ...note })),
          },
        },
        instrumental: {
          instrumental: {
            ...this.instrumental,
            layers: [...this.instrumental.layers],
            stems: this.instrumental.stems.map((stem) => ({ ...stem })),
          },
        },
        voice: {
          voice: {
            ...this.voice,
            layers: this.voice.layers.map((layer) => ({ ...layer })),
            sectionDirection: this.voice.sectionDirection.map((section) => ({ ...section })),
            sections: { ...this.voice.sections },
          },
        },
        production: {
          production: {
            projectSet: { ...this.projectSet },
            productionProjectId: this.productionProjectId,
            productionGlobalStatus: this.productionGlobalStatus,
          },
        },
      };
      return payloads[phase] || {};
    },
    captureProjectBaselines() {
      this.fullLyricsProposal = null;
      this.appliedFullLyricsProposal = null;
      this.lyricSectionProposals = {};
      this.unlockedLyricSectionIds = [];
      this.unlockedLyricLineIds = [];
      this.unlockedLyricDirectionIds = [];
      this.projectBaselinePayloads = Object.fromEntries(this.phaseDefinitions.map(({ id }) => [id, cloneJson(this.phasePayload(id))]));
    },
    async savePhaseData(phase = this.activeTab, options = {}) {
      if (!this.activeProjectId) {
        this.saveError = "Carga un proyecto desde Biblioteca antes de guardar esta fase.";
        this.addMessage(this.saveError);
        return false;
      }
      if (this.savingPhase) return false;
      if (phase === "intent" && !validEmotionalValues(this.intent)) {
        this.saveError = "Revisa los valores emocionales: deben ser números entre 0 y 100.";
        this.addMessage(this.saveError);
        return false;
      }
      if (!validPhaseRanges(phase, this.phasePayload(phase))) {
        this.saveError = "Revisa los valores numéricos: deben estar dentro del rango indicado junto al control.";
        this.addMessage(this.saveError);
        return false;
      }
      this.saveError = "";
      this.savingPhase = phase;
      const controller = new AbortController();
      const timeoutId = window.setTimeout(() => controller.abort(), 20000);
      try {
        const requestedSetId = this.activeProjectId;
        const response = await fetch(apiUrl(`/api/projects/${requestedSetId}/phases/${phase}`), {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ data: this.phasePayload(phase), spec_revision_id: this.activeProject?.music_spec_revision_id,
            reviewed_assistant_proposals: this.assistantAppliedPatches.filter((proposal) => proposal.phase === phase),
            reviewed_full_lyrics_proposal: phase === 'lyrics' ? this.appliedFullLyricsProposal : undefined,
            unlocked_section_ids: phase === 'lyrics' ? this.unlockedLyricSectionIds : undefined,
            unlocked_line_ids: phase === 'lyrics' ? this.unlockedLyricLineIds : undefined,
            unlocked_direction_ids: phase === 'lyrics' ? this.unlockedLyricDirectionIds : undefined }),
          signal: controller.signal,
        });
        const payload = await this.readApiPayload(response, {});
        if (!payload.ok) {
          const message = payload.detail || "No se pudo guardar la fase.";
          this.saveError = message;
          this.addMessage(message);
          return false;
        }
        if (this.activeProjectId !== requestedSetId) return false;
        this.activeProject = payload.data.project;
        this.assistantAppliedPatches = [];
        this.selectedSet = payload.data.project.set;
        this.savedPhaseData = payload.data.project.phase_data || {};
        this.applySavedPhaseData(this.savedPhaseData);
        this.outdatedPhases = this.outdatedPhases.filter((item) => item !== phase);
        this.dirty = false;
        this.dirtyPhase = "";
        this.dirtyOutdatedSnapshot = [...this.outdatedPhases];
        this.captureProjectBaselines();
        if (payload.data.export_warning) this.addMessage(payload.data.export_warning);
        if (payload.data.project.music_spec_song_id) await this.loadProfessionalSpecification(payload.data.project.music_spec_song_id);
        if (!options.quiet) this.addMessage(`${this.phaseLabel(phase)} guardado`);
        return true;
      } catch (error) {
        const message = error?.name === "AbortError"
          ? `No se pudo guardar ${this.phaseLabel(phase)}: el servidor no respondio en 20 segundos.`
          : `No se pudo guardar ${this.phaseLabel(phase)}: ${error?.message || "error de red"}`;
        this.addMessage(message);
        this.saveError = message;
        return false;
      } finally {
        window.clearTimeout(timeoutId);
        this.savingPhase = "";
      }
    },
    phaseLabel(phase) {
      return {
        intent: "Intent",
        lyrics: "Letra",
        "music-plan": "Estilo",
        midi: "MIDI",
        instrumental: "Instrumental",
        voice: "Voz",
        production: "Production",
      }[phase] || phase;
    },
    applySavedPhaseData(phaseData) {
      for (const phase of Object.keys(this.defaultPhasePayloads)) this.restorePhase(phase, false);
      this.savedPhaseData = cloneJson(phaseData);
      const read = (phase) => cloneJson(phaseData?.[phase]?.data || {});
      const intentData = read("intent").intent;
      if (intentData) this.intent = { ...this.intent, ...intentData, inspirationInput: "" };
      const lyricsData = read("lyrics");
      if (lyricsData.lyrics) this.lyrics = { ...this.lyrics, ...lyricsData.lyrics };
      if (Array.isArray(lyricsData.lyricSections)) this.lyricSections = lyricsData.lyricSections.map((section) => ({ ...section }));
      if (lyricsData.lyricsEditor) this.lyricsEditor = { ...this.lyricsEditor, ...lyricsData.lyricsEditor };
      const musicPlanData = read("music-plan").musicPlan;
      if (musicPlanData) this.musicPlan = { ...this.musicPlan, ...musicPlanData, sections: musicPlanData.sections || this.musicPlan.sections };
      const midiData = read("midi").midiPlan;
      if (midiData) this.midiPlan = { ...this.midiPlan, ...midiData, tracks: midiData.tracks || this.midiPlan.tracks, notes: midiData.notes || this.midiPlan.notes };
      const instrumentalData = read("instrumental").instrumental;
      if (instrumentalData) this.instrumental = { ...this.instrumental, ...instrumentalData, stems: instrumentalData.stems || this.instrumental.stems };
      const voiceData = read("voice").voice;
      if (voiceData) this.voice = { ...this.voice, ...voiceData, layers: voiceData.layers || this.voice.layers, sectionDirection: voiceData.sectionDirection || this.voice.sectionDirection };
      const productionData = read("production").production;
      if (productionData?.projectSet) this.projectSet = { ...this.projectSet, ...productionData.projectSet };
      if (productionData?.productionProjectId) this.productionProjectId = productionData.productionProjectId;
      this.dirty = false;
      this.dirtyPhase = "";
      this.outdatedPhases = [];
      this.dirtyOutdatedSnapshot = [];
    },
    restorePhase(phase, useSaved = true) {
      const baseline = useSaved ? this.projectBaselinePayloads?.[phase] : null;
      const defaults = cloneJson(baseline || this.defaultPhasePayloads?.[phase] || {});
      const saved = useSaved && !baseline ? cloneJson(this.savedPhaseData?.[phase]?.data || {}) : {};
      const data = Object.keys(saved).length ? saved : defaults;
      const target = {
        intent: ["intent", "intent"], lyrics: ["lyrics", "lyrics"],
        "music-plan": ["musicPlan", "musicPlan"], midi: ["midiPlan", "midiPlan"],
        instrumental: ["instrumental", "instrumental"], voice: ["voice", "voice"],
      }[phase];
      if (target) this[target[0]] = cloneJson(data[target[1]] || defaults[target[1]] || {});
      if (phase === "lyrics") {
        this.lyricSections = cloneJson(data.lyricSections || defaults.lyricSections || []);
        this.lyricsEditor = cloneJson(data.lyricsEditor || defaults.lyricsEditor || { selectedAssetId: "", content: "", path: "" });
      }
      if (phase === "production" && data.production?.projectSet) this.projectSet = cloneJson(data.production.projectSet);
    },
    async refreshSystemStatus() {
      await this.loadProviders();
      this.addMessage("Estado de componentes actualizado.");
    },
    async restartBootstrap() {
      const response = await fetch(apiUrl("/api/system/bootstrap/restart"), { method: "POST", headers: { "Content-Type": "application/json" }, body: "{}" });
      const payload = await this.readApiPayload(response, {});
      await this.loadProviders();
      this.addMessage(payload.data?.message || payload.detail || "Bootstrap iniciado.");
    },
    async upgradeBootstrap() {
      const response = await fetch(apiUrl("/api/system/bootstrap/upgrade"), { method: "POST", headers: { "Content-Type": "application/json" }, body: "{}" });
      const payload = await this.readApiPayload(response, {});
      await this.loadProviders();
      this.addMessage(payload.data?.message || payload.detail || "Actualizacion iniciada.");
    },
    async refreshLlmModel(role) {
      const response = await fetch(apiUrl(`/api/system/models/${role}/refresh`), { method: "POST", headers: { "Content-Type": "application/json" }, body: "{}" });
      const payload = await this.readApiPayload(response, {});
      await this.loadProviders();
      this.addMessage(payload.data?.message || payload.detail || `Recreacion de ${role} iniciada.`);
    },
    async askGemmaAssistant() {
      if (this.gemmaAssistant.loading) return;
      this.gemmaAssistant.loading = true;
      this.gemmaAssistant.error = "";
      const projectId = this.activeProjectId;
      const phase = this.activeTab;
      const sourceContext = proposalContext(projectId, this.activeProject?.music_spec_revision_id, phase, this.phasePayload(phase));
      const controller = new AbortController();
      const modelTimeout = Number(this.modelStatus?.local?.llama_cpp_timeout_seconds) || 240;
      const timeoutId = window.setTimeout(() => controller.abort(), (2 * modelTimeout + 30) * 1000);
      try {
      const response = await fetch(apiUrl("/api/assistant/gemma"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        signal: controller.signal,
        body: JSON.stringify({
          set_id: this.activeProjectId,
          spec_revision_id: sourceContext.revisionId,
          song_id: this.activeProfessionalProject?.id || "",
          question: this.gemmaAssistant.question,
          active_phase: this.activeTab,
          active_project_title: this.activeProjectTitle,
          active_project_description: this.activeProjectDescription,
          editor_phase_statuses: Object.fromEntries(this.phaseDefinitions.map((phase) => [phase.id, this.phaseStatus(phase.id)])),
        }),
      });
      const payload = await this.readApiPayload(response, {});
      if (!payload.ok) throw new Error(payload.detail || "Gemma no pudo revisar el proyecto.");
      if (payload.data.phase_patch?.source_revision_id != null && payload.data.phase_patch.source_revision_id !== sourceContext.revisionId) {
        this.assistantPendingPatch = null;
        throw new Error("La propuesta usa otra revisión. Recarga el proyecto y consulta de nuevo.");
      }
      if (!proposalContextMatches(sourceContext, proposalContext(this.activeProjectId, this.activeProject?.music_spec_revision_id, this.activeTab, this.phasePayload(this.activeTab)))) {
        this.assistantPendingPatch = null;
        this.addMessage("El proyecto cambió durante la consulta. Consulta de nuevo al asistente para revisar los datos actuales.");
        return;
      }
      this.gemmaAssistant.response = {
        ...payload.data,
        message: this.hideTechnicalDirectorName(String(payload.data.message || "")),
        technical_handoff_note: payload.data.technical_handoff_note,
      };
      this.assistantPendingPatch = payload.data.phase_patch?.available ? { ...payload.data.phase_patch, source_project_id: projectId, source_context: sourceContext } : null;
      await this.loadOrchestration();
      this.addMessage(`Gemma: ${this.gemmaAssistant.response.status}`);
      } catch (error) {
        this.gemmaAssistant.error = error?.name === "AbortError"
          ? "La consulta supero el tiempo disponible. Puedes reintentar con una peticion mas breve."
          : `No se pudo consultar a Gemma: ${error?.message || "error de red"}`;
        this.addMessage(this.gemmaAssistant.error);
      } finally {
        window.clearTimeout(timeoutId);
        this.gemmaAssistant.loading = false;
      }
    },
    applyAssistantPhasePatch(phasePatch) {
      if (!phasePatch?.available || !phasePatch?.phase || !phasePatch?.changes) return;
      if (phasePatch.source_project_id && phasePatch.source_project_id !== this.activeProjectId) return;
      if (!proposalContextMatches(phasePatch.source_context, proposalContext(this.activeProjectId, this.activeProject?.music_spec_revision_id, this.activeTab, this.phasePayload(this.activeTab)))) {
        this.addMessage("La propuesta corresponde a datos anteriores. Consulta de nuevo al asistente antes de aplicarla.");
        return;
      }
      const phase = String(phasePatch.phase);
      if (phase !== this.activeTab) {
        this.addMessage(`Gemma preparo cambios para ${phase}, pero no los aplique porque estas en ${this.activeTab}.`);
        return;
      }
      const changes = { ...phasePatch.changes };
      let appliedProposals;
      try {
        appliedProposals = appendAppliedProposal(this.assistantAppliedPatches, phasePatch);
      } catch (error) {
        this.addMessage(error.message);
        return;
      }
      const phaseTargets = {
        intent: this.intent,
        lyrics: this.lyrics,
        "music-plan": this.musicPlan,
        midi: this.midiPlan,
        instrumental: this.instrumental,
        voice: this.voice,
      };
      const target = phaseTargets[phase];
      if (!target) return;
      Object.entries(changes).forEach(([key, value]) => {
        if (!(key in target)) return;
        if (key === "placeholders" && typeof value === "object" && value !== null && !Array.isArray(value)) {
          target.placeholders = { ...target.placeholders, ...value };
          return;
        }
        target[key] = value;
      });
      this.markDirty(phase);
      this.assistantAppliedPatches = appliedProposals;
      this.addMessage(`Gemma ajusto ${Object.keys(changes).length} campo(s) en ${phase}. Revisa y guarda si te gusta.`);
    },
    hideTechnicalDirectorName(text) {
      return text.replaceAll("Qwen", "el director tecnico").replaceAll("qwen", "el director tecnico");
    },
    async postAction(url, body = {}, successLabel = "Accion completada") {
      try {
      const response = await fetch(apiUrl(url), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      const payload = await this.readApiPayload(response, {});
      if (!payload.ok) {
        this.addMessage(payload.detail || payload.error || "Error");
        return null;
      }
      const detail = payload.data?.summary || payload.data?.id || payload.data?.path || "";
      this.addMessage(`${successLabel}: ${detail}`);
      await this.loadJsonConfigs();
      await this.loadSets();
      await this.loadOrchestration();
      await this.loadProviders();
      return payload.data;
      } catch (error) {
        this.addMessage(error?.message || "Error de red al preparar el draft.");
        return null;
      }
    },
    help(label) {
      return this.options.help_texts?.[label] || "";
    },
    setPlaceholderPreset(name) {
      const preset = this.options.placeholder_presets?.[name];
      if (preset) {
        this.lyrics.placeholders = { ...preset };
        this.markDirty("lyrics");
      }
    },
    toggleInstrument(instrument) {
      const current = this.intent.instruments;
      this.intent.instruments = current.includes(instrument) ? current.filter((item) => item !== instrument) : [...current, instrument];
      this.markDirty("intent");
    },
    selectInstrumentFamily(familyName) {
      const family = this.options.instrument_families[familyName] || [];
      const selected = new Set(this.intent.instruments);
      family.forEach((instrument) => selected.add(instrument));
      this.intent.instruments = [...selected];
      this.markDirty("intent");
    },
    clearInstruments() {
      this.intent.instruments = [];
      this.markDirty("intent");
    },
    toggleInspiration(tag) {
      this.intent.inspirations = this.intent.inspirations.includes(tag)
        ? this.intent.inspirations.filter((item) => item !== tag)
        : [...this.intent.inspirations, tag];
      this.markDirty("intent");
    },
    addCustomInspiration() {
      const value = this.intent.inspirationInput.trim();
      if (!value) return;
      if (!this.intent.inspirations.includes(value)) {
        this.intent.inspirations = [...this.intent.inspirations, value];
      }
      this.intent.inspirationInput = "";
      this.markDirty("intent");
    },
    async saveIntentAsDrafts() {
      await this.createInstrumental();
      await this.createMelody();
      this.addMessage("Intent convertido en instrumental y melodia guia.");
    },
    exportLabel(type) {
      return {
        final_song_mp3: "MP3",
        final_song_flac: "FLAC",
        final_song_wav: "WAV",
        midi: "MIDI",
        project_zip: "ZIP proyecto completo",
        instrumental_wav: "Instrumental WAV",
        vocals_wav: "Vocals WAV",
        mix_wav: "Mix WAV",
        export_manifest_json: "Metadata JSON",
      }[type] || type;
    },
    exportNote(artifact) {
      const metadata = artifact?.metadata || {};
      if (metadata.quality_blocked) {
        return metadata.quality_message || "Bloqueado por control de calidad vocal.";
      }
      if (artifact?.type === "vocals_wav" && metadata.mode === "procedural_vocal_guide") {
        return "Guia vocal procedural: no es voz cantada real.";
      }
      if (metadata.quality_status === "preview_only") return "Preview tecnico, no final.";
      return "";
    },
    formatSize(bytes) {
      if (!bytes) return "0 B";
      if (bytes < 1024) return `${bytes} B`;
      if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
      return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
    },
    formatDuration(seconds) {
      const value = Math.max(0, Math.round(Number(seconds) || 0));
      const minutes = Math.floor(value / 60);
      const remainingSeconds = value % 60;
      if (minutes >= 60) {
        const hours = Math.floor(minutes / 60);
        const restMinutes = minutes % 60;
        return restMinutes ? `${hours}h ${restMinutes}m` : `${hours}h`;
      }
      if (minutes > 0) return remainingSeconds ? `${minutes}m ${remainingSeconds}s` : `${minutes}m`;
      return `${remainingSeconds}s`;
    },
    formatMinutes(minutes) {
      return this.formatDuration(Math.max(0, Math.round(Number(minutes) || 0)) * 60);
    },
    formatResourceTime(value) {
      if (!value) return "--";
      const parsed = new Date(value);
      if (Number.isNaN(parsed.getTime())) return String(value).replace("T", " ").slice(0, 19);
      return parsed.toLocaleString("es-CO", {
        hour12: false,
        month: "2-digit",
        day: "2-digit",
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit",
      });
    },
    formatElapsedSince(value) {
      const parsed = new Date(value);
      if (Number.isNaN(parsed.getTime())) return "";
      const seconds = Math.max(0, Math.floor((this.uiClockNow - parsed.getTime()) / 1000));
      const hours = Math.floor(seconds / 3600);
      const minutes = Math.floor((seconds % 3600) / 60);
      const remainingSeconds = seconds % 60;
      if (hours > 0) return `${hours}h ${minutes}m ${remainingSeconds}s`;
      return `${minutes}m ${remainingSeconds}s`;
    },
  },
}).mount("#app");
