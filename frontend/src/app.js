import { createApp } from "vue";
import "./styles.css";

const API_BASE = window.SONG_AI_API_BASE || "";

function apiUrl(path) {
  return `${API_BASE}${path}`;
}

createApp({
  data() {
    return {
      activeTab: "instrumental",
      tabs: [
        { id: "instrumental", label: "Instrumental", hint: "Define base, BPM, tonalidad e instrumentos." },
        { id: "melody", label: "Melodia", hint: "Define voz guia, rango y estructura." },
        { id: "lyrics", label: "Letra", hint: "Define idioma, tema y placeholders." },
        { id: "production", label: "Produccion", hint: "Crea set, sample, cancion, mezcla y exports." },
        { id: "library", label: "Biblioteca", hint: "Revisa drafts, favoritos y providers." },
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
      projectSet: {
        project_name: "Cancion de cuna para Isabella",
        description: "Cancion de cuna completa, tierna y poetica con soundtrack suave y voz cantada.",
      },
      drafts: [],
      sets: [],
      selectedSet: null,
      providers: {},
      studioStatus: {},
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
        { label: "1. Crear set", hint: "Combina un instrumental, una melodia y una letra. La IA de asistencia valida que los puntos 1, 2 y 3 esten completos.", url: "/api/sets" },
        { label: "2. Crear sample", hint: "Crea un checkpoint de calidad antes de producir la cancion completa.", url: "/api/samples" },
        { label: "3. Crear cancion", hint: "Prepara pipeline completo: letra, estructura, soundtrack, voz cantada, stems, mezcla y exports.", url: "/api/songs" },
        { label: "4. Preparar mezcla", hint: "Prepara mezcla de voz cantada + instrumental y verifica ffmpeg.", url: "/api/mix" },
        { label: "5. Preparar exports", hint: "Crea manifest y rutas de formatos finales.", url: "/api/exports" },
        { label: "6. Exportar sets JSON", hint: "Regenera los set.json desde SQLite y sobrescribe archivos previos con el mismo nombre.", url: "/api/sets/export" },
        { label: "7. Guardar plantilla", hint: "Guarda el set como plantilla reutilizable.", url: "/api/templates" },
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
    async loadOptions() {
      const response = await fetch(apiUrl("/api/options"));
      const payload = await response.json();
      this.options = payload.data;
    },
    async loadProviders() {
      const [providersResponse, studioResponse, modelResponse] = await Promise.all([
        fetch(apiUrl("/api/providers")),
        fetch(apiUrl("/api/studio/status")),
        fetch(apiUrl("/api/models/status")),
      ]);
      const payload = await providersResponse.json();
      const studioPayload = await studioResponse.json();
      const modelPayload = await modelResponse.json();
      this.providers = payload.data;
      this.studioStatus = studioPayload.data;
      this.modelStatus = modelPayload.data;
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
        this.messages.unshift(payload.detail || "No se pudo cargar el set");
        return;
      }
      this.selectedSet = payload.data;
    },
    async loadJsonConfigs() {
      const response = await fetch(apiUrl("/api/json-configs"));
      const payload = await response.json();
      this.jsonConfigs = payload.data;
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
    },
    async createSet() {
      await this.postAction("/api/sets", this.projectSet, "Proyecto/set guardado");
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
      const payload = await response.json();
      if (!payload.ok) {
        this.messages.unshift(payload.detail || payload.error || "Error");
        return;
      }
      const detail = payload.data?.summary || payload.data?.id || payload.data?.path || "";
      this.messages.unshift(`${successLabel}: ${detail}`);
      await this.loadJsonConfigs();
      await this.loadSets();
      await this.loadOrchestration();
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
