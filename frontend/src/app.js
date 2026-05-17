import { createApp } from "vue";
import "./styles.css";

const API_BASE = window.SONG_AI_API_BASE || "";

function apiUrl(path) {
  return `${API_BASE}${path}`;
}

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

createApp({
  data() {
    return {
      activeTab: "library",
      pendingTab: "",
      showUnsavedModal: false,
      dirty: false,
      dirtyPhase: "",
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
      productionMetadata: {
        editingName: false,
        tagsInput: "suave, warm, piano, cinematografico",
      },
      productionSummaryOpen: true,
      drafts: [],
      sets: [],
      selectedSet: null,
      activeProject: null,
      professionalProjects: [],
      productionProjectId: "",
      exportManifest: { artifacts: [] },
      favoriteProjects: {},
      archived: [],
      librarySearch: "",
      tagSearch: "",
      gemmaAssistant: {
        question: "Que sigue para terminar esta cancion?",
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
      messages: [],
      downloadStatus: "",
    };
  },
  computed: {
    currentTab() {
      return this.tabs.find((tab) => tab.id === this.activeTab) || this.tabs[0];
    },
    activeProjectTitle() {
      return this.activeProject?.project?.project_name || this.selectedSet?.project_name || this.projectSet.project_name || "Sin proyecto activo";
    },
    activeProjectDescription() {
      return this.activeProject?.project?.description || this.selectedSet?.description || this.projectSet.description || "";
    },
    activeProjectId() {
      return this.activeProject?.set?.set_id || this.selectedSet?.set_id || "";
    },
    activeProfessionalProject() {
      return this.professionalProjects.find((project) => project.id === this.productionProjectId) || this.professionalProjects[0] || null;
    },
    productionGlobalStatus() {
      if (this.exportManifest?.artifacts?.length) return "Export listo";
      if (this.activeProfessionalProject?.current_phase) return `${this.activeProfessionalProject.current_phase} / ${this.activeProfessionalProject.status}`;
      if (this.activeProjectId) return "Set cargado, pendiente de proyecto profesional";
      return "Sin proyecto activo";
    },
    productionTags() {
      return this.productionMetadata.tagsInput
        .split(",")
        .map((tag) => tag.trim())
        .filter(Boolean);
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
      return this.draftReadiness.every((item) => item.count > 0);
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
          .filter((artifact) => ["final_song_mp3", "final_song_wav", "midi", "instrumental_wav", "vocals_wav", "mix_wav", "export_manifest_json"].includes(artifact.type))
          .map((artifact) => ({
            name: this.exportLabel(artifact.type),
            type: artifact.type,
            size: this.formatSize(artifact.size_bytes || 0),
            url: artifact.download_url,
          }));
      }
      return [
        { name: "MP3", type: "final_song_mp3", size: "pendiente", url: "" },
        { name: "FLAC", type: "final_song_flac", size: "pendiente", url: "" },
        { name: "WAV", type: "final_song_wav", size: "pendiente", url: "" },
        { name: "MIDI", type: "midi", size: "pendiente", url: "" },
        { name: "ZIP proyecto completo", type: "project_zip", size: "pendiente", url: "" },
      ];
    },
    productionPipelineSteps() {
      const songId = this.activeProfessionalProject?.id || "";
      return [
        { phase: "SONG_SPEC_COLLECTION", label: "Spec", action: "Enviar intent", method: "POST", url: `/api/pro/projects/${songId}/spec/messages`, requires: songId },
        { phase: "LYRICS_GENERATION", label: "Lyrics", action: "Generar lyrics", method: "POST", url: `/api/pro/projects/${songId}/lyrics`, requires: songId },
        { phase: "LYRICS_TECHNICAL_REVIEW", label: "Revision lyrics", action: "Aprobar lyrics", method: "POST", url: `/api/pro/projects/${songId}/lyrics/review`, requires: songId },
        { phase: "MUSIC_PLAN_GENERATION", label: "Music Plan", action: "Generar plan", method: "POST", url: `/api/pro/projects/${songId}/music-plan`, requires: songId },
        { phase: "MIDI_GENERATION", label: "MIDI", action: "Crear MIDI", method: "POST", url: `/api/pro/projects/${songId}/midi`, requires: songId },
        { phase: "INSTRUMENTAL_GENERATION", label: "Instrumental", action: "Generar instrumental", method: "POST", url: `/api/pro/projects/${songId}/instrumental`, requires: songId },
        { phase: "VOCAL_SYNTHESIS", label: "Voice", action: "Generar voz", method: "POST", url: `/api/pro/projects/${songId}/vocals`, requires: songId },
        { phase: "VOICE_CONVERSION", label: "Conversion", action: "Resolver conversion", method: "POST", url: `/api/pro/projects/${songId}/voice-conversion`, requires: songId },
        { phase: "MIXING", label: "Mixing", action: "Mezclar", method: "POST", url: `/api/pro/projects/${songId}/mix`, requires: songId },
        { phase: "MASTERING", label: "Mastering", action: "Masterizar", method: "POST", url: `/api/pro/projects/${songId}/master`, requires: songId },
        { phase: "EXPORT", label: "Export", action: "Preparar export", method: "POST", url: `/api/pro/projects/${songId}/export`, requires: songId },
      ];
    },
    productionSpecMessage() {
      return [
        this.intent.description,
        `Tipo: ${this.intent.songType}`,
        `Destinatario: ${this.intent.recipient}`,
        `Idioma: ${this.intent.language}`,
        `Duracion 120 segundos`,
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
    canGenerateLocalFinalSong() {
      return Boolean(this.localPipeline.ready) && !this.bootstrapRunning;
    },
    localFinalStatusMessage() {
      if (this.bootstrapRunning) return "Bootstrap preparando dependencias locales. Consulta estado en unos minutos.";
      if (this.localPipeline.ready) return "Pipeline local listo para generar final.";
      return `Falta configurar: ${this.localPipeline.missing?.join(", ") || "requisitos locales"}.`;
    },
  },
  async mounted() {
    this.restoreLocalUiState();
    this.activateFromPath(window.location.pathname);
    window.addEventListener("popstate", () => this.activateFromPath(window.location.pathname, false));
    await this.loadOptions();
    await this.refreshDrafts();
    await this.loadSets();
    await this.loadProfessionalProjects();
    await this.loadProviders();
    await this.loadOrchestration();
    await this.loadJsonConfigs();
  },
  methods: {
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
    },
    persistLocalUiState() {
      localStorage.setItem("song-ai:favorites", JSON.stringify(this.favoriteProjects));
      localStorage.setItem("song-ai:archived", JSON.stringify(this.archived));
      localStorage.setItem("song-ai:lyric-templates", JSON.stringify(this.lyricTemplates));
    },
    activateFromPath(path, push = false) {
      const tab = TAB_BY_ROUTE[path] || "library";
      this.activeTab = tab;
      if (push) window.history.pushState({}, "", ROUTE_BY_TAB[tab]);
    },
    requestNavigation(tab) {
      if (tab === this.activeTab) return;
      if (this.dirty) {
        this.pendingTab = tab;
        this.showUnsavedModal = true;
        return;
      }
      this.activateFromPath(ROUTE_BY_TAB[tab], true);
    },
    discardAndContinue() {
      this.dirty = false;
      this.dirtyPhase = "";
      this.showUnsavedModal = false;
      this.activateFromPath(ROUTE_BY_TAB[this.pendingTab || "library"], true);
      this.pendingTab = "";
    },
    cancelNavigation() {
      this.pendingTab = "";
      this.showUnsavedModal = false;
    },
    async saveAndContinue() {
      await this.saveCurrentPhase();
      this.showUnsavedModal = false;
      this.activateFromPath(ROUTE_BY_TAB[this.pendingTab || this.activeTab], true);
      this.pendingTab = "";
    },
    markDirty(phase = this.activeTab) {
      this.dirty = true;
      this.dirtyPhase = phase;
      this.outdatedPhases = [...new Set([...(this.outdatedPhases || []), ...(DEPENDENCIES[phase] || [])])];
    },
    phaseStatus(phaseId) {
      if (this.dirty && this.dirtyPhase === phaseId) return "DIRTY";
      if (this.outdatedPhases.includes(phaseId)) return "OUTDATED";
      if (phaseId === "intent") return this.activeProjectId || this.intent.description ? "READY" : "EMPTY";
      if (phaseId === "lyrics") return this.lyricSections.length > 0 || this.lyricsEditor.selectedAssetId ? "READY" : "EMPTY";
      if (phaseId === "production" && this.exportManifest?.artifacts?.length) return "READY";
      const legacy = {
        instrumental: "instrumental",
        lyrics: "lyrics",
      }[phaseId];
      if (legacy && this.draftReadiness.find((item) => item.type === legacy)?.count > 0) return "READY";
      return "EMPTY";
    },
    phaseUi(phaseId) {
      return PHASE_STATUS[this.phaseStatus(phaseId)] || PHASE_STATUS.EMPTY;
    },
    async saveCurrentPhase() {
      if (this.activeTab === "lyrics" && this.lyricsEditor.selectedAssetId) {
        await this.saveLyricsDraft();
      } else if (this.activeTab === "production") {
        this.saveProductionMetadata();
      } else {
        this.dirty = false;
        this.dirtyPhase = "";
        this.addMessage(`${this.currentTab.label} guardado localmente.`);
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
    },
    async loadSets() {
      const response = await fetch(apiUrl("/api/sets"));
      const payload = await response.json();
      this.sets = payload.data;
    },
    async loadProfessionalProjects() {
      const response = await fetch(apiUrl("/api/pro/projects"));
      const payload = await this.readApiPayload(response, { projects: [] });
      this.professionalProjects = payload.data.projects || [];
      if (!this.productionProjectId && this.professionalProjects.length > 0) {
        this.productionProjectId = this.professionalProjects[0].id;
        await this.loadProfessionalExport(this.productionProjectId);
      }
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
      if (!response.ok || payload.ok === false) return { ok: false, data: fallbackData, detail: payload.detail || "API no disponible" };
      return payload;
    },
    async loadProject(setId) {
      const response = await fetch(apiUrl(`/api/projects/${setId}`));
      const payload = await this.readApiPayload(response, {});
      if (!payload.ok) {
        this.addMessage(payload.detail || "No se pudo cargar el proyecto.");
        return;
      }
      this.activeProject = payload.data;
      this.selectedSet = payload.data.set;
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
      this.projectEvents = payload.data.events;
      this.addMessage(`Proyecto cargado: ${payload.data.project.project_name}`);
      await this.loadProviders();
      this.requestNavigation("production");
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
    },
    async createInstrumental() {
      await this.postAction(
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
    },
    async createMelody() {
      await this.postAction(
        "/api/melodies",
        {
          vocal_style: this.voice.mainVoice || this.melody.vocal_style,
          range_hint: this.melody.range_hint,
          structure: this.lyrics.structure || this.melody.structure,
          mood: this.voice.emotion || this.melody.mood,
          energy: this.intent.energy > 55 ? "medium" : "low",
        },
        "Melodia guia guardada",
      );
      await this.refreshDrafts();
    },
    async createLyrics() {
      await this.postAction("/api/lyrics", this.lyrics, "Letra guardada");
      await this.refreshDrafts();
      const latestLyrics = this.lyricsDrafts[this.lyricsDrafts.length - 1];
      if (latestLyrics) await this.loadLyricsDraft(latestLyrics.asset_id);
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
      this.lyricsEditor = { selectedAssetId: payload.data.asset_id, content: payload.data.content, path: payload.data.path };
      this.parseLyricsToSections();
      this.dirty = false;
      this.dirtyPhase = "";
    },
    async saveLyricsDraft() {
      if (!this.lyricsEditor.selectedAssetId) {
        await this.createLyrics();
        return;
      }
      this.lyricsEditor.content = this.sectionsToMarkdown();
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
      this.dirty = false;
      this.dirtyPhase = "";
      this.addMessage(`Lyrics guardado: ${payload.data.asset_id}`);
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
      this.markDirty("lyrics");
    },
    moveSection(index, direction) {
      const target = index + direction;
      if (target < 0 || target >= this.lyricSections.length) return;
      const sections = [...this.lyricSections];
      [sections[index], sections[target]] = [sections[target], sections[index]];
      this.lyricSections = sections;
      this.markDirty("lyrics");
    },
    duplicateSection(index) {
      const original = this.lyricSections[index];
      this.lyricSections.splice(index + 1, 0, { ...original, id: `${Date.now()}-${Math.random().toString(16).slice(2)}` });
      this.markDirty("lyrics");
    },
    removeSection(index) {
      this.lyricSections.splice(index, 1);
      this.markDirty("lyrics");
    },
    transformSection(index, mode) {
      const section = this.lyricSections[index];
      const suffix = {
        mejorar: "Mas claro, mas cantable, conservando la esencia.",
        recrear: "Nueva mirada con la misma emocion central.",
        expandir: "Agrega una imagen sensorial y una linea de respuesta.",
        acortar: "Version mas directa para entrar mejor en compas.",
        variantes: "Variante A / Variante B para elegir interpretacion.",
      }[mode];
      section.text = `${section.text.trim()}\n${suffix}`;
      this.markDirty("lyrics");
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
          sections: this.lyricSections.map((section) => ({ type: section.type, text: section.text })),
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
      const template = this.lyricTemplates.find((item) => item.id === templateId);
      if (!template) return;
      this.lyricSections = template.sections.map((section) => ({
        ...section,
        id: `${Date.now()}-${Math.random().toString(16).slice(2)}`,
      }));
      this.lyrics.placeholders = { ...template.placeholders };
      this.markDirty("lyrics");
      this.addMessage(`Plantilla cargada: ${template.name}`);
    },
    addTag(tag) {
      const tags = new Set(this.productionTags);
      tags.add(tag);
      this.productionMetadata.tagsInput = [...tags].join(", ");
      this.markDirty("production");
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
    tagsForSet(songSet) {
      const stopWords = new Set(["para", "con", "una", "este", "esta", "cancion", "proyecto", "completa", "desde"]);
      return `${songSet.project_name || ""} ${songSet.description || ""}`
        .toLowerCase()
        .split(/[^a-zA-Z0-9áéíóúñ]+/)
        .filter((token) => token.length > 3 && !stopWords.has(token))
        .slice(0, 6);
    },
    saveProductionMetadata() {
      this.projectSet.project_name = this.activeProjectTitle;
      this.projectSet.description = this.activeProjectDescription;
      this.dirty = false;
      this.dirtyPhase = "";
      this.addMessage("Metadata de production guardada localmente.");
    },
    async createProfessionalProjectFromProduction() {
      const response = await fetch(apiUrl("/api/pro/projects"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          title: this.projectSet.project_name || this.activeProjectTitle,
          description: this.projectSet.description || this.activeProjectDescription,
        }),
      });
      const payload = await this.readApiPayload(response, {});
      if (!payload.ok) {
        this.addMessage(payload.detail || "No se pudo crear el proyecto profesional.");
        return;
      }
      this.productionProjectId = payload.data.project.id;
      await this.loadProfessionalProjects();
      this.addMessage(`Proyecto profesional creado: ${this.productionProjectId}`);
    },
    async runProductionStep(step) {
      if (!step.requires) {
        this.addMessage("Crea o selecciona un proyecto profesional primero.");
        return;
      }
      const response = await fetch(apiUrl(step.url), {
        method: step.method,
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(step.phase === "SONG_SPEC_COLLECTION" ? { message: this.productionSpecMessage } : {}),
      });
      const payload = await this.readApiPayload(response, {});
      if (!payload.ok) {
        this.addMessage(payload.detail || `No se pudo ejecutar ${step.label}.`);
        return;
      }
      await this.loadProfessionalProjects();
      if (step.phase === "EXPORT") await this.loadProfessionalExport(step.requires);
      this.addMessage(`${step.label}: ${payload.data?.project?.current_phase || "completado"}`);
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
    async generateLocalFinalSong() {
      if (!this.canGenerateLocalFinalSong) {
        this.addMessage(this.localFinalStatusMessage);
        await this.loadProviders();
        return;
      }
      const response = await fetch(apiUrl("/api/local-final-song"), { method: "POST", headers: { "Content-Type": "application/json" }, body: "{}" });
      const payload = await this.readApiPayload(response, {});
      await this.loadProviders();
      this.addMessage(payload.data?.summary || payload.detail || "Generacion final solicitada.");
    },
    async loadProfessionalExport(songId) {
      if (!songId) return;
      const response = await fetch(apiUrl(`/api/pro/projects/${songId}/export`));
      const payload = await this.readApiPayload(response, { artifacts: [] });
      this.exportManifest = payload.data;
    },
    async saveLatestMp3() {
      this.downloadStatus = "Preparando descarga...";
      const response = await fetch(apiUrl("/api/audio-exports/latest/download?format=mp3"));
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
    async askGemmaAssistant() {
      this.gemmaAssistant.loading = true;
      const response = await fetch(apiUrl("/api/assistant/gemma"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ set_id: this.activeProjectId, question: this.gemmaAssistant.question, active_phase: this.activeTab }),
      });
      const payload = await response.json();
      this.gemmaAssistant.loading = false;
      if (!payload.ok) {
        this.addMessage(payload.detail || "Gemma no pudo revisar el proyecto.");
        return;
      }
      this.gemmaAssistant.response = {
        ...payload.data,
        message: this.hideTechnicalDirectorName(String(payload.data.message || "")),
        technical_handoff_note: "Gemma coordino internamente la revision tecnica.",
      };
      await this.loadOrchestration();
      this.addMessage(`Gemma: ${this.gemmaAssistant.response.status}`);
    },
    hideTechnicalDirectorName(text) {
      return text.replaceAll("Qwen", "el director tecnico").replaceAll("qwen", "el director tecnico");
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
        instrumental_wav: "Instrumental WAV",
        vocals_wav: "Vocals WAV",
        mix_wav: "Mix WAV",
        export_manifest_json: "Metadata JSON",
      }[type] || type;
    },
    formatSize(bytes) {
      if (!bytes) return "0 B";
      if (bytes < 1024) return `${bytes} B`;
      if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
      return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
    },
  },
}).mount("#app");
