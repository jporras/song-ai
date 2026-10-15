export function generationStatus(job) {
  const states={pending:['En espera','La solicitud está registrada. Puedes cancelarla antes de continuar.'],running:['Generando audio','ACE-Step está trabajando. Puedes cancelar y conservar las decisiones guardadas.'],cancelling:['Cancelación solicitada','Espera a que termine la cancelación antes de iniciar otra generación.'],cancelled:['Generación cancelada','El trabajo anterior sigue en el historial. Revisa el plan y autoriza una nueva generación si quieres reintentar.'],failed:['No se pudo generar','Revisa el mensaje técnico y el plan. Corrige el bloqueo y autoriza un nuevo intento.'],completed:['Candidato creado','Escucha el archivo completo y registra tu opinión. Crear el archivo no acredita calidad ni aceptación.']};
  const [title,help]=states[job?.status] || ['Estado sin confirmar','Actualiza el estado antes de continuar; no se supone que haya audio terminado.'];
  const progress=typeof job?.progress==='number' && Number.isFinite(job.progress) && job.progress>=0 && job.progress<=100 ? job.progress : null;
  return {title,help,progress,cancellable:['pending','running'].includes(job?.status)};
}

export const GenerationStatus={
  props:{job:{type:Object,required:true},busy:Boolean},emits:['cancel','refresh'],
  computed:{state(){return generationStatus(this.job);}},
  template:`<section class="panel" aria-label="Estado de generación de audio">
    <h3>{{ state.title }}</h3><p role="status" aria-live="polite">{{ state.help }}</p>
    <p>{{ job.message }}</p>
    <div v-if="state.progress !== null"><label>Progreso del trabajo (no calidad del audio)<progress max="100" :value="state.progress">{{ state.progress }}%</progress></label><span>{{ state.progress }}%</span></div>
    <p v-else>El motor no reportó un porcentaje de progreso.</p>
    <button v-if="state.cancellable" type="button" :disabled="busy" @click="$emit('cancel')">Cancelar generación</button>
    <button type="button" :disabled="busy" @click="$emit('refresh')">Actualizar estado</button>
    <details v-if="job.result?.error || job.error"><summary>Detalle del error</summary><pre>{{ job.result?.error || job.error }}</pre></details>
  </section>`
};
