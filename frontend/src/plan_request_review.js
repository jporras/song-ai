import {decisionValue} from './decision_card.js';
export function planRequestFields(payload = {}) {
  const labels={bpm:'Velocidad (BPM)',key_scale:'Tonalidad',time_signature:'Compás',vocal_language:'Idioma vocal',audio_duration:'Duración (segundos)',repainting_start:'Inicio del fragmento (segundos)',repainting_end:'Final del fragmento (segundos)',instruction:'Instrucción de la operación'};
  return Object.entries(labels).filter(([key])=>payload[key]!==undefined && payload[key]!==null && payload[key]!=='')
    .map(([key,label])=>({key,label,value:decisionValue(payload[key])}));
}
export const PlanRequestReview={
  props:{plan:{type:Object,required:true}},
  computed:{fields(){return planRequestFields(this.plan.payload);},operation(){return {text2music:'Crear desde la idea',cover:'Cambiar estilo o timbre',repaint:'Corregir un fragmento',lego:'Añadir una pista',extract:'Aislar una pista',complete:'Completar el arreglo'}[this.plan.payload?.task_type] || 'Operación sin identificar';}},
  template:`<section class="panel" aria-label="Lo que recibirá ACE-Step"><h3>Lo que recibirá ACE-Step</h3>
    <p>{{ operation }}</p><dl class="plan-request-fields"><div v-for="field in fields" :key="field.key" class="plan-request-field"><dt>{{ field.label }}</dt><dd>{{ field.value }}</dd></div></dl>
    <details open><summary>Descripción musical enviada</summary><p class="decision-value">{{ plan.payload?.captions || 'Sin descripción enviada para esta operación.' }}</p></details>
    <details><summary>Letra exacta del plan</summary><pre class="decision-value">{{ plan.payload?.lyrics || 'Sin letra para esta operación.' }}</pre></details>
    <p>Esta es la solicitud de la revisión del plan; no demuestra que el motor haya ejecutado esos valores ni que el resultado sea fiel.</p>
  </section>`
};
