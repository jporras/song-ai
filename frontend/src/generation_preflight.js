export function generationPreflight(project, review, resources, dirty) {
  const revision=project?.music_spec_revision_id;
  const current=Boolean(revision && project.music_spec?.revision?.revision_id===revision
    && project.music_spec.revision.user_confirmation_status==='confirmed'
    && review?.effective_status==='approved' && review.inputs_current===true
    && review.plan?.spec_revision_id===revision);
  return {
    creative:dirty ? 'Hay cambios sin guardar. Guarda y revisa la nueva configuración antes de generar.'
      : current ? 'Ficha y plan aprobados para la revisión guardada.' : 'Confirma la ficha y aprueba un plan vigente.',
    creativeReady:current && !dirty,
    technical:resources?.readiness?.ready===false
      ? resources?.settings?.release_llm_before_audio && resources?.settings?.stop_llm_command_configured
        ? 'La lectura actual es previa al cierre de Gemma/Qwen. Al generar, se liberarán los modelos y se comprobará la memoria otra vez.'
        : 'El diagnóstico de recursos indica un bloqueo. Revisa las recomendaciones antes de continuar.'
      : 'La carga del modelo y su ejecución aún deben comprobarse. Un plan aprobado no acredita disponibilidad del motor.',
    recommendations:resources?.readiness?.recommendations || [],
    limits:'Al iniciar, el backend vuelve a validar revisión, archivos, fuentes y recursos. Un candidato creado requiere escucha y evaluación; no es audio aceptado.'
  };
}

export const GenerationPreflight = {
  props:{state:{type:Object,required:true}},
  template:`<section class="panel generation-preflight-panel" aria-label="Revisión previa a generar">
    <h3>Antes de generar</h3>
    <div class="grid two"><section><h4>Tu canción está definida</h4><p>{{ state.creative }}</p></section>
    <section><h4>El motor puede ejecutarla</h4><p>{{ state.technical }}</p><ul v-if="state.recommendations.length"><li v-for="(item,index) in state.recommendations" :key="index">{{ item }}</li></ul></section></div>
    <p>{{ state.limits }}</p>
  </section>`
};
