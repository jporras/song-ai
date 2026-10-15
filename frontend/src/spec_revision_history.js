export function revisionChanges(current = {}, previous = {}, labels = {}) {
  const canonical = value => Array.isArray(value) ? value.map(canonical) : value && typeof value === 'object'
    ? Object.fromEntries(Object.keys(value).sort().map(key => [key, canonical(value[key])])) : value;
  return [...new Set([...Object.keys(current), ...Object.keys(previous)])]
    .filter(key => !key.startsWith('_') && !['src_audio','reference_audio'].includes(key) && JSON.stringify(canonical(current[key])) !== JSON.stringify(canonical(previous[key])))
    .map(key => ({field:key, label:labels[key] || key, current:current[key], restored:previous[key]}));
}

export const SpecRevisionHistory = {
  props: ['revisions', 'current', 'catalog', 'busy', 'blocked'],
  emits: ['restore', 'review'],
  data: () => ({selected:''}),
  computed: {
    choices() { return (this.revisions || []).filter(r => r.revision_id !== this.current?.revision?.revision_id); },
    source() { return this.choices.find(r => r.revision_id === this.selected); },
    changes() {
      const labels = Object.fromEntries((this.catalog?.groups || []).flatMap(g => g.fields.map(f => [f.id, f.label])));
      return this.source ? revisionChanges(this.current?.json_spec, this.source.json_spec, labels) : [];
    },
  },
  methods: { display(value) { return value === undefined ? 'Sin definir' : typeof value === 'string' ? value : JSON.stringify(value); } },
  template: `<details class="specification-group">
    <summary>Versiones anteriores de la definición</summary>
    <p>Recuperar crea una nueva versión pendiente de revisión. Conserva las versiones anteriores y no recupera aprobaciones de audio.</p>
    <div v-if="current?.revision?.technical_review_mode === 'restored_snapshot_requires_review'">
      <p>La versión recuperada necesita validar sus entradas actuales. Abre la configuración, revísala y guárdala antes de confirmar.</p>
      <button :disabled="busy || blocked" @click="$emit('review')">Revisar configuración recuperada</button>
    </div>
    <label>Versión que quieres recuperar
      <select v-model="selected" :disabled="busy || blocked">
        <option value="">Selecciona una versión</option>
        <option v-for="r in choices" :key="r.revision_id" :value="r.revision_id">Versión {{ r.revision_number }} · {{ r.created_at }}</option>
      </select>
    </label>
    <p v-if="!choices.length">Todavía no hay versiones anteriores.</p>
    <div v-if="source">
      <p>También se recuperan la letra, la dirección por sección y los datos de edición guardados en esa versión.</p>
      <details v-if="source.json_spec._lyrics_document?.markdown"><summary>Letra que se recuperará</summary><pre style="white-space:pre-wrap;overflow-wrap:anywhere">{{ source.json_spec._lyrics_document.markdown }}</pre></details>
      <details v-if="source.json_spec.section_direction"><summary>Dirección por sección que se recuperará</summary><pre style="white-space:pre-wrap;overflow-wrap:anywhere">{{ display(source.json_spec.section_direction) }}</pre></details>
      <ul><li v-for="change in changes" :key="change.field"><strong>{{ change.label }}</strong>: {{ display(change.current) }} → {{ display(change.restored) }}</li></ul>
      <p v-if="!changes.length">No hay diferencias en los campos principales. Los datos de edición pueden ser distintos.</p>
      <button :disabled="busy || blocked" @click="$emit('restore', {source_revision_id:source.revision_id, revision_id:current.revision.revision_id})">{{ busy ? 'Recuperando…' : 'Recuperar como nueva definición' }}</button>
    </div>
    <p v-if="blocked">Guarda o descarta los cambios abiertos antes de recuperar una versión.</p>
  </details>`,
};
