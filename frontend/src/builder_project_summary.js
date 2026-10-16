export const BuilderProjectSummary = {
  props: {status:{type:Object,required:true},busy:Boolean},
  emits:['navigate','save'],
  template: `<section class="builder-project-summary" aria-label="Resumen del proyecto musical">
    <h2>Preparación de esta canción</h2>
    <ul class="builder-status-list"><li v-for="item in status.items" :key="item.label">
      <strong>{{ item.label }}</strong><span>{{ item.ready ? 'Preparado' : 'Pendiente' }}</span>
      <details v-if="item.detail"><summary>Qué significa</summary><p>{{ item.detail }}</p></details>
    </li></ul>
    <p role="status">{{ status.message }}</p>
    <button type="button" class="primary" :disabled="busy" @click="status.action.save ? $emit('save') : $emit('navigate', status.action.tab)">{{ busy ? 'Guardando…' : status.action.label }}</button>
  </section>`
};
