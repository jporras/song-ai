import { createApp } from "vue";
import "./styles.css";

const API_BASE = window.SONG_AI_API_BASE || "";

function apiUrl(path) {
  return `${API_BASE}${path}`;
}

createApp({
  data() {
    return {
      activeTab: "library",
      tabs: [
        { id: "library", label: "Biblioteca", hint: "Carga un proyecto existente o crea un nuevo set." },
        { id: "instrumental", label: "Instrumental", hint: "Define base, BPM, tonalidad e instrumentos." },
        { id: "melody", label: "Melodia", hint: "Define voz guia, rango y estructura." },
        { id: "lyrics", label: "Letra", hint: "Define idioma, tema y placeholders." },
        { id: "production", label: "Produccion", hint: "Genera sample, cancion, mezcla y exports del set activo." },
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
      instrumental: {
        genre: "lullaby",
        mood: "tender",
        bpm: 72,
        key: "C major",
        instruments: ["piano", "music box", "soft pad", "strings"],
        energy: "low",
      },
      melody: {
        vocal_style: "soft lullaby singing",
        range_hint: "medium",
        structure: "intro, verse 1, chorus, verse 2, final chorus, outro",
        mood: "tender",
        energy: "low",
      },
      lyrics: {
        language: "Spanish",
        tone: "tender",
        theme: "lullaby for {name}",
        structure: "intro, verse 1, chorus, verse 2, bridge, final chorus, outro",
        placeholders: { name: "Isabella", image: "estrellita", promise: "siempre cuidarte" },
      },
      lyricsEditor: {
        selectedAssetId: "",
        content: "",
        path: "",
        dirty: false,
      },
      projectSet: {
        project_name: "Cancion de cuna para Isabella",
        description: "Cancion de cuna completa, tierna y poetica con soundtrack suave y voz cantada.",
      },
      drafts: [],
      sets: [],
      selectedSet: null,
      activeProject: null,
      gemmaAssistant: {
        question: "Que sigue para terminar esta cancion?",
        response: null,
        loading: false,
      },
      qwenAssistant: {
        question: "Que ajuste tecnico necesita el pipeline para llegar al MP3 final?",
        response: null,
        loading: false,
      },
      providers: {},
      studioStatus: {},
      localPipeline: {},
      systemStatus: { components: [], bootstrap: {} },
      projectPhases: { phases: [] },
      modelStatus: {},
      orchestrationStatus: {},
      tasks: [],
      modelRuns: [],
      projectEvents: [],
      jsonConfigs: [],
      custom: {
        instrumental: {},
        melody: {},
        lyrics: {},
      },
      messages: [],
      downloadStatus: "",
    };
  },
  computed: {
    currentTab() {
      return this.tabs.find((tab) => tab.id === this.activeTab);
    },
    flatInstruments() {
      return Object.values(this.options.instrument_families).flat();
    },
    productionSteps() {
      return [
        { label: "1. Crear sample", hint: "Crea un checkpoint de calidad desde el set activo antes de producir la cancion completa.", url: "/api/samples" },
        { label: "2. Crear cancion", hint: "Prepara pipeline completo: letra, estructura, soundtrack, voz cantada, stems, mezcla y exports.", url: "/api/songs" },
        { label: "3. Preparar mezcla", hint: "Prepara mezcla de voz cantada + instrumental y verifica ffmpeg.", url: "/api/mix" },
        { label: "4. Preparar exports", hint: "Crea manifest y rutas de formatos finales.", url: "/api/exports" },
        { label: "5. Generar maqueta WAV/MP3", hint: "Solo valida el flujo con guia vocal sintetica. No es la cancion final.", url: "/api/audio-exports" },
      ];
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
        { label: "1. Instrumental", type: "instrumental", count: counts.instrumental || 0 },
        { label: "2. Melodia", type: "melody", count: counts.melody || 0 },
        { label: "3. Letra", type: "lyrics", count: counts.lyrics || 0 },
      ];
    },
    canCreateSet() {
      return this.draftReadiness.every((item) => item.count > 0);
    },
    lyricsDrafts() {
      return this.drafts.filter((draft) => draft.asset_type === "lyrics");
    },
    activeProjectId() {
      return this.activeProject?.set?.set_id || this.selectedSet?.set_id || "";
    },
    assistantReminder() {
      if (this.canCreateSet) {
        return "Listo para crear el proyecto/set: ya existe al menos un instrumental, una melodia y una letra.";
      }
      const missing = this.draftReadiness
        .filter((item) => item.count === 0)
        .map((item) => item.label)
        .join(", ");
      return `Antes de crear la cancion completa debes terminar estos puntos: ${missing}.`;
    },
    footerAssistant() {
      const missing = this.draftReadiness.filter((item) => item.count === 0);
      if (missing.length > 0) {
        const nextMissing = missing[0];
        const targetTab = {
          instrumental: "instrumental",
          melody: "melody",
          lyrics: "lyrics",
        }[nextMissing.type];
        return {
          title: "Siguiente paso sugerido",
          message: `Completa ${nextMissing.label.toLowerCase()} antes de crear el proyecto/set. La cancion necesita instrumental, melodia y letra para conservar la intencion musical.`,
          actions: [{ label: `Ir a ${nextMissing.label}`, tab: targetTab }],
          checks: this.draftReadiness,
        };
      }
      if (this.sets.length === 0) {
        return {
          title: "Listo para ensamblar",
          message: "Ya estan los tres drafts base. Ahora crea el proyecto/set para agruparlos y poder generar un sample.",
          actions: [{ label: "Ir a Produccion", tab: "production" }],
          checks: this.draftReadiness,
        };
      }
      return {
        title: "Proyecto preparado",
        message: "Ya existe al menos un set. El procedimiento recomendado es revisar configuracion, generar sample y luego avanzar a cancion completa.",
        actions: [
          { label: "Ver Biblioteca", tab: "library" },
          { label: "Ir a Produccion", tab: "production" },
        ],
        checks: this.draftReadiness,
      };
    },
    bootstrapRunning() {
      return this.systemStatus.bootstrap?.status === "running";
    },
    canGenerateLocalFinalSong() {
      return Boolean(this.localPipeline.ready) && !this.bootstrapRunning;
    },
    localFinalStatusMessage() {
      if (this.bootstrapRunning) {
        return "Bootstrap preparando dependencias locales. Consulta estado en unos minutos.";
      }
      if (this.localPipeline.ready) {
        return "Pipeline local listo para generar final.";
      }
      return `Falta configurar: ${this.localPipeline.missing?.join(", ") || "requisitos locales"}.`;
    },
  },
  async mounted() {
    await this.loadOptions();
    await this.refreshDrafts();
    await this.loadSets();
    await this.loadProviders();
    await this.loadOrchestration();
    await this.loadJsonConfigs();
  },
  methods: {
    addMessage(text) {
      const now = new Date();
      this.messages.unshift({
        id: `${now.getTime()}-${Math.random().toString(16).slice(2)}`,
        time: now.toLocaleString("es-CO", {
          hour12: false,
          year: "numeric",
          month: "2-digit",
          day: "2-digit",
          hour: "2-digit",
          minute: "2-digit",
          second: "2-digit",
        }),
        text,
      });
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
      const payload = await this.readApiPayload(providersResponse, {});
      const studioPayload = await this.readApiPayload(studioResponse, {});
      const modelPayload = await this.readApiPayload(modelResponse, {});
      const localPipelinePayload = await this.readApiPayload(localPipelineResponse, {});
      const systemPayload = await this.readApiPayload(systemResponse, {});
      const phasesPayload = await this.readApiPayload(phasesResponse, { phases: [] });
      this.providers = payload.data;
      this.studioStatus = studioPayload.data;
      this.modelStatus = modelPayload.data;
      this.localPipeline = localPipelinePayload.data;
      this.systemStatus = systemPayload.data;
      this.projectPhases = phasesPayload.data;
    },
    async loadOrchestration() {
      const [statusResponse, tasksResponse, runsResponse] = await Promise.all([
        fetch(apiUrl("/api/orchestration/status")),
        fetch(apiUrl("/api/tasks")),
        fetch(apiUrl("/api/model-runs")),
      ]);
      const eventsResponse = await fetch(apiUrl("/api/project-events"));
      const statusPayload = await statusResponse.json();
      const tasksPayload = await tasksResponse.json();
      const runsPayload = await runsResponse.json();
      const eventsPayload = await eventsResponse.json();
      this.orchestrationStatus = statusPayload.data;
      this.tasks = tasksPayload.data;
      this.modelRuns = runsPayload.data;
      this.projectEvents = eventsPayload.data;
    },
    async refreshDrafts() {
      const response = await fetch(apiUrl("/api/drafts"));
      const payload = await response.json();
      this.drafts = payload.data;
    },
    async loadSets() {
      const response = await fetch(apiUrl("/api/sets"));
      const payload = await response.json();
      this.sets = payload.data;
    },
    async showSet(setId) {
      const response = await fetch(apiUrl(`/api/sets/${setId}`));
      const payload = await response.json();
      if (!payload.ok) {
        this.addMessage(payload.detail || "No se pudo cargar el set");
        return;
      }
      this.selectedSet = payload.data;
    },
    async loadProject(setId) {
      const response = await fetch(apiUrl(`/api/projects/${setId}`));
      const payload = await response.json();
      if (!payload.ok) {
        this.addMessage(payload.detail || "No se pudo cargar el proyecto.");
        return;
      }

      this.activeProject = payload.data;
      this.selectedSet = payload.data.set;
      this.projectSet.project_name = payload.data.project.project_name;
      this.projectSet.description = payload.data.project.description;

      const lyricsAsset = payload.data.assets.lyrics;
      this.lyricsEditor = {
        selectedAssetId: lyricsAsset.asset_id,
        content: lyricsAsset.content || "",
        path: lyricsAsset.content_path || "",
        dirty: false,
      };
      this.projectEvents = payload.data.events;
      this.addMessage(`Proyecto cargado: ${payload.data.project.project_name}`);
      await this.loadProviders();
    },
    async loadJsonConfigs() {
      const response = await fetch(apiUrl("/api/json-configs"));
      const payload = await response.json();
      this.jsonConfigs = payload.data;
    },
    async readApiPayload(response, fallbackData = {}) {
      const raw = await response.text().catch(() => "");
      let payload = { ok: false, data: fallbackData, detail: raw || "API no disponible" };
      if (raw) {
        try {
          payload = JSON.parse(raw);
        } catch (_) {
          payload.detail = raw;
        }
      }
      if (!response.ok || payload.ok === false) {
        return { ok: false, data: fallbackData, detail: payload.detail || "API no disponible" };
      }
      return payload;
    },
    async createInstrumental() {
      await this.postAction("/api/instrumentals", this.instrumental, "Instrumental guardado");
      await this.refreshDrafts();
    },
    async createMelody() {
      await this.postAction("/api/melodies", this.melody, "Melodia guardada");
      await this.refreshDrafts();
    },
    async createLyrics() {
      await this.postAction("/api/lyrics", this.lyrics, "Letra guardada");
      await this.refreshDrafts();
      const latestLyrics = this.lyricsDrafts[this.lyricsDrafts.length - 1];
      if (latestLyrics) {
        await this.loadLyricsDraft(latestLyrics.asset_id);
      }
    },
    async loadLyricsDraft(assetId = this.lyricsEditor.selectedAssetId) {
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
      this.lyricsEditor = {
        selectedAssetId: payload.data.asset_id,
        content: payload.data.content,
        path: payload.data.path,
        dirty: false,
      };
    },
    async saveLyricsDraft() {
      if (!this.lyricsEditor.selectedAssetId) {
        this.addMessage("Selecciona una letra para guardar.");
        return;
      }
      const response = await fetch(apiUrl(`/api/lyrics/${this.lyricsEditor.selectedAssetId}`), {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ content: this.lyricsEditor.content }),
      });
      const payload = await response.json();
      if (!payload.ok) {
        this.addMessage(payload.detail || "No se pudo guardar la letra.");
        return;
      }
      this.lyricsEditor.content = payload.data.content;
      this.lyricsEditor.path = payload.data.path;
      this.lyricsEditor.dirty = false;
      this.addMessage(`Letra actualizada: ${payload.data.asset_id}`);
    },
    async createSet() {
      const response = await fetch(apiUrl("/api/sets"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(this.projectSet),
      });
      const payload = await this.readApiPayload(response, {});
      if (!payload.ok) {
        this.addMessage(payload.detail || "No se pudo crear el proyecto/set.");
        return;
      }
      await this.loadSets();
      await this.loadProject(payload.data.id);
      await this.loadJsonConfigs();
      this.addMessage(`Proyecto/set creado y cargado: ${payload.data.id}`);
    },
    async createPresetMp3() {
      const response = await fetch(apiUrl("/api/presets/lullaby/mp3"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({}),
      });
      const payload = await response.json();
      if (!payload.ok) {
        this.addMessage(payload.detail || "No se pudo crear el MP3 predefinido.");
        return;
      }
      this.activeProject = payload.data.project;
      this.selectedSet = payload.data.project.set;
      this.projectSet.project_name = payload.data.project.project.project_name;
      this.projectSet.description = payload.data.project.project.description;
      await this.refreshDrafts();
      await this.loadSets();
      await this.loadOrchestration();
      await this.loadJsonConfigs();
      await this.loadProviders();
      const mp3Detail = payload.data.mp3 || "MP3 pendiente";
      this.addMessage(`${payload.data.summary} ${mp3Detail}`);
    },
    async refreshSystemStatus() {
      await this.loadProviders();
      this.addMessage("Estado de componentes actualizado.");
    },
    async restartBootstrap() {
      const response = await fetch(apiUrl("/api/system/bootstrap/restart"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({}),
      });
      const payload = await this.readApiPayload(response, {});
      if (!payload.ok) {
        this.addMessage(payload.detail || "No se pudo iniciar el bootstrap.");
        return;
      }
      await this.loadProviders();
      this.addMessage(payload.data.message || "Bootstrap iniciado. Consulta el estado en unos minutos.");
    },
    async upgradeBootstrap() {
      const response = await fetch(apiUrl("/api/system/bootstrap/upgrade"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({}),
      });
      const payload = await this.readApiPayload(response, {});
      if (!payload.ok) {
        this.addMessage(payload.detail || "No se pudo actualizar el bootstrap.");
        return;
      }
      await this.loadProviders();
      this.addMessage(payload.data.message || "Actualizacion iniciada. Consulta el estado en unos minutos.");
    },
    async generateLocalFinalSong() {
      if (!this.canGenerateLocalFinalSong) {
        this.addMessage(this.localFinalStatusMessage);
        await this.loadProviders();
        return;
      }
      const response = await fetch(apiUrl("/api/local-final-song"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({}),
      });
      const payload = await this.readApiPayload(response, {});
      if (!payload.ok) {
        this.addMessage(payload.detail || "No se pudo generar la cancion final local.");
        await this.loadProviders();
        return;
      }
      await this.loadProviders();
      await this.loadJsonConfigs();
      this.addMessage(`${payload.data.summary} ${payload.data.mp3 || ""}`);
    },
    async saveLatestMp3() {
      this.downloadStatus = "Preparando descarga...";
      const downloadUrl = apiUrl("/api/audio-exports/latest/download?format=mp3");
      const response = await fetch(downloadUrl);
      if (!response.ok) {
        const payload = await response.json().catch(() => ({}));
        const message = payload.detail || "No se pudo descargar el MP3. Genera WAV/MP3 primero.";
        this.downloadStatus = message;
        this.addMessage(message);
        return;
      }

      const blob = await response.blob();
      const filename = this.filenameFromDisposition(response.headers.get("content-disposition")) || "song-ai-final-mix.mp3";
      if ("showSaveFilePicker" in window) {
        const handle = await window.showSaveFilePicker({
          suggestedName: filename,
          types: [{ description: "MP3", accept: { "audio/mpeg": [".mp3"] } }],
        });
        const writable = await handle.createWritable();
        await writable.write(blob);
        await writable.close();
        this.downloadStatus = `MP3 guardado: ${filename}`;
        this.addMessage(this.downloadStatus);
        return;
      }

      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(url);
      this.downloadStatus = "Descarga iniciada. El navegador decide la carpeta o pregunta donde guardarlo segun su configuracion.";
      this.addMessage(this.downloadStatus);
    },
    filenameFromDisposition(disposition) {
      const match = disposition?.match(/filename="?([^"]+)"?/i);
      return match ? match[1] : "";
    },
    async askGemmaAssistant() {
      this.gemmaAssistant.loading = true;
      const response = await fetch(apiUrl("/api/assistant/gemma"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          set_id: this.activeProjectId,
          question: this.gemmaAssistant.question,
        }),
      });
      const payload = await response.json();
      this.gemmaAssistant.loading = false;
      if (!payload.ok) {
        this.addMessage(payload.detail || "Gemma no pudo revisar el proyecto.");
        return;
      }
      this.gemmaAssistant.response = payload.data;
      await this.loadOrchestration();
      this.addMessage(`Gemma transversal: ${payload.data.status}`);
    },
    async askQwenAssistant() {
      this.qwenAssistant.loading = true;
      const response = await fetch(apiUrl("/api/assistant/qwen"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          set_id: this.activeProjectId,
          question: this.qwenAssistant.question,
        }),
      });
      const payload = await response.json();
      this.qwenAssistant.loading = false;
      if (!payload.ok) {
        this.addMessage(payload.detail || "Qwen no pudo revisar el ajuste tecnico.");
        return;
      }
      this.qwenAssistant.response = payload.data;
      await this.loadOrchestration();
      this.addMessage(`Qwen tecnico: ${payload.data.status}`);
    },
    async simulateHandoff(modelRole = "intent_extractor", taskType = "extract_intent") {
      await this.postAction(
        "/api/orchestration/handoff",
        {
          model_role: modelRole,
          task_type: taskType,
          phase: taskType,
          project_id: this.projectSet.project_name,
          project_name: this.projectSet.project_name,
          description: this.projectSet.description,
        },
        "Handoff IA completado",
      );
    },
    async favorite(assetId) {
      await this.postAction("/api/favorites", { asset_id: assetId }, "Favorito actualizado");
    },
    async postAction(url, body = {}, successLabel = "Accion completada") {
      const response = await fetch(apiUrl(url), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      const payload = await this.readApiPayload(response, {});
      if (!payload.ok) {
        this.addMessage(payload.detail || payload.error || "Error");
        return;
      }
      const detail = payload.data?.summary || payload.data?.id || payload.data?.path || "";
      this.addMessage(`${successLabel}: ${detail}`);
      await this.loadJsonConfigs();
      await this.loadSets();
      await this.loadOrchestration();
      await this.loadProviders();
    },
    help(label) {
      return this.options.help_texts?.[label] || "";
    },
    applyCustom(section, field) {
      const value = this.custom[section]?.[field]?.trim();
      if (!value) return;
      this[section][field] = field === "bpm" ? Number(value) || this[section][field] : value;
      this.custom[section][field] = "";
    },
    setPlaceholderPreset(name) {
      const preset = this.options.placeholder_presets?.[name];
      if (preset) {
        this.lyrics.placeholders = { ...preset };
      }
    },
    toggleInstrument(instrument) {
      const current = this.instrumental.instruments;
      if (current.includes(instrument)) {
        this.instrumental.instruments = current.filter((item) => item !== instrument);
        return;
      }
      this.instrumental.instruments = [...current, instrument];
    },
    selectInstrumentFamily(familyName) {
      const family = this.options.instrument_families[familyName] || [];
      const selected = new Set(this.instrumental.instruments);
      family.forEach((instrument) => selected.add(instrument));
      this.instrumental.instruments = [...selected];
    },
    clearInstruments() {
      this.instrumental.instruments = [];
    },
  },
}).mount("#app");
