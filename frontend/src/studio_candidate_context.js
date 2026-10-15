export function studioCandidateContext(job, currentRevision) {
  const report = job?.result?.fidelity_report;
  const revision = report?.spec_revision_id;
  const structure = report?.checks?.find(check => check.id === 'structure');
  return {
    created: job?.created_at || null,
    revision: revision || null,
    current: revision && currentRevision ? revision === currentRevision : null,
    expected: structure?.expected ?? null,
    observed: structure?.observed ?? null,
  };
}

function display(value) {
  return typeof value === 'string' ? value : JSON.stringify(value, null, 2);
}

export const StudioCandidateContext = {
  props:{job:{type:Object,required:true},currentRevision:String},
  computed:{context(){return studioCandidateContext(this.job,this.currentRevision);}},
  methods:{display},
  template:`<section class="studio-candidate-context" aria-label="Versión y estructura del candidato">
    <h3>Versión seleccionada</h3>
    <p v-if="context.created">Creada: {{ new Date(context.created).toLocaleString('es-CO') }}</p>
    <p v-if="context.current === true">Pertenece a la revisión actual de la definición. Esto no acredita calidad ni aprobación.</p>
    <p v-else-if="context.current === false">Pertenece a una revisión anterior. Sus resultados no acreditan los cambios actuales.</p>
    <p v-else>No hay información suficiente para comprobar a qué revisión corresponde.</p>
    <h4>Estructura prevista para esta versión</h4>
    <pre v-if="context.expected !== null">{{ display(context.expected) }}</pre>
    <p v-else>Este candidato no conserva una estructura prevista en su informe. No se sustituye por la definición actual.</p>
    <h4>Estructura observada en el audio</h4>
    <pre v-if="context.observed !== null">{{ display(context.observed) }}</pre>
    <p v-else>No hay una alineación verificada de secciones. Elige manualmente el intervalo al revisar el audio.</p>
    <details><summary>Identificadores de esta versión</summary><p>Trabajo: {{ job.task_id }}</p><p>Revisión: {{ context.revision || 'Sin registro' }}</p></details>
  </section>`
};
