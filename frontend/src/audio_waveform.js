// Peaks describe decoded samples, not musical structure or perceived quality.
export function audioPeaks(channels, count = 240) {
  const length = channels[0]?.length || 0;
  if (!length || channels.some(channel => channel.length !== length)) throw new Error('Audio sin muestras válidas.');
  const bins = Math.min(length, count);
  return Array.from({length: bins}, (_, bin) => {
    let peak = 0;
    const start = Math.floor(bin * length / bins), end = Math.floor((bin + 1) * length / bins);
    for (const channel of channels) for (let i = start; i < end; i++) peak = Math.max(peak, Math.abs(channel[i]));
    return peak;
  });
}

export function validAudioInterval(start, end, duration) {
  return [start, end, duration].every(value => typeof value === 'number' && Number.isFinite(value))
    && start >= 0 && end > start && end <= duration;
}

export const AudioWaveform = {
  props: {src: {type:String, required:true}, busy:Boolean},
  emits: ['select-interval'],
  data() { return {peaks:[], duration:0, start:0, end:0, loading:false, error:'', controller:null, context:null, request:0}; },
  computed: {
    valid() { return validAudioInterval(this.start, this.end, this.duration); },
    selection() { return this.valid ? {x:this.start / this.duration * 1000, width:(this.end-this.start) / this.duration * 1000} : null; },
  },
  watch: {src() { this.reset(); }},
  beforeUnmount() { this.reset(); },
  methods: {
    reset() {
      this.request++; this.controller?.abort(); this.context?.close().catch(() => {});
      this.controller=null; this.context=null; this.peaks=[]; this.duration=0;
      this.start=0; this.end=0; this.loading=false; this.error='';
    },
    async analyze() {
      this.reset(); const request=this.request; this.loading=true;
      const controller=new AbortController(); this.controller=controller;
      let context;
      try {
        const Context=window.AudioContext || window.webkitAudioContext;
        if (!Context) throw new Error('Este navegador no permite analizar el audio. Puedes escucharlo con el reproductor.');
        const response=await fetch(this.src, {signal:controller.signal});
        if (!response.ok) throw new Error('No se pudo descargar el audio. Intenta nuevamente.');
        const bytes=await response.arrayBuffer();
        if (request !== this.request) return;
        context=new Context(); this.context=context;
        let audio;
        try { audio=await context.decodeAudioData(bytes); }
        catch { throw new Error('No se pudo leer este formato de audio. Prueba con un archivo WAV o MP3 válido; puedes seguir usando el reproductor si el navegador lo admite.'); }
        if (request !== this.request) return;
        this.peaks=audioPeaks(Array.from({length:audio.numberOfChannels}, (_, index)=>audio.getChannelData(index)));
        this.duration=audio.duration; this.end=audio.duration;
      } catch (error) {
        if (request === this.request && error.name !== 'AbortError') this.error=error.message || 'No se pudo analizar este archivo.';
      } finally {
        if (context && context.state !== 'closed') await context.close().catch(() => {});
        if (request === this.request) { this.loading=false; this.context=null; this.controller=null; }
      }
    },
  },
  template:`<section class="audio-waveform" :aria-busy="loading" aria-label="Forma de onda y selección de fragmento">
    <h3>Ver el audio y elegir un fragmento</h3>
    <p>La forma de onda muestra la amplitud del archivo. No identifica versos, instrumentos ni calidad.</p>
    <button type="button" :disabled="loading || busy" @click="analyze">{{ loading ? 'Analizando el archivo…' : peaks.length ? 'Volver a analizar el audio' : 'Mostrar forma de onda' }}</button>
    <p role="status" aria-live="polite">{{ loading ? 'Descargando y calculando la señal del audio seleccionado.' : error }}</p>
    <template v-if="peaks.length">
      <svg viewBox="0 0 1000 120" preserveAspectRatio="none" role="img" :aria-label="'Amplitud del audio, duración ' + duration.toFixed(2) + ' segundos'">
        <line x1="0" x2="1000" y1="60" y2="60" class="waveform-axis" />
        <rect v-if="selection" :x="selection.x" y="0" :width="selection.width" height="120" class="waveform-selection" />
        <line v-for="(peak,index) in peaks" :key="index" :x1="(index + .5) * 1000 / peaks.length" :x2="(index + .5) * 1000 / peaks.length" :y1="60 - Math.min(peak,1) * 56" :y2="60 + Math.min(peak,1) * 56" class="waveform-peak" />
      </svg>
      <p>Duración del archivo: {{ duration.toFixed(2) }} segundos. Selección manual; no se deduce de la estructura prevista.</p>
      <div class="waveform-interval">
        <label>Inicio del fragmento (segundos)<input type="number" min="0" :max="duration" step="any" v-model.number="start"></label>
        <label>Final del fragmento (segundos)<input type="number" min="0" :max="duration" step="any" v-model.number="end"></label>
      </div>
      <p v-if="!valid" role="status">El final debe ser mayor que el inicio y estar dentro de la duración del archivo.</p>
      <button type="button" :disabled="!valid || busy" @click="$emit('select-interval', {start,end})">Usar este fragmento en la corrección</button>
      <p>Solo prepara los controles. Revisa y guarda tu opinión antes de solicitar una corrección; no corta ni genera audio.</p>
    </template>
  </section>`
};
