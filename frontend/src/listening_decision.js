export function listeningReviewStatus(review) {
  if (!review) return 'Sin opinión guardada para este candidato.';
  if (review.audio_current === false) return 'Opinión histórica: el audio cambió o ya no está disponible. Genera otro candidato para revisarlo.';
  if (review.inputs_current === false) return 'Opinión histórica: la configuración cambió. Revisa el candidato de la nueva revisión.';
  if (review.audio_current === true && review.inputs_current === true) return 'Opinión vigente para el audio y la configuración revisados.';
  return 'Opinión guardada; falta confirmar la vigencia del audio o de la configuración.';
}

export const ListeningDecision={
  props:{confirmed:Boolean,decision:String,notes:String,busy:Boolean},
  emits:['update:confirmed','update:decision','update:notes'],
  template:`<section aria-label="Tu opinión de este candidato">
    <h3>Escucha y decide</h3>
    <p>Escucha el archivo completo con el reproductor. Registrar esta opinión no aprueba el sample ni la canción final.</p>
    <label><input type="checkbox" :checked="confirmed" :disabled="busy" @change="$emit('update:confirmed',$event.target.checked)"> Declaro que escuché este candidato y quiero registrar mi opinión.</label>
    <label>Cómo corresponde a tu idea<select :value="decision" :disabled="busy" required @change="$emit('update:decision',$event.target.value)"><option value="" disabled>Elige después de escuchar</option><option value="accepted">Este borrador corresponde a mi idea</option><option value="changes_requested">Quiero corregir aspectos del borrador</option></select></label>
    <label>Qué conservar o corregir<textarea :value="notes" :disabled="busy" maxlength="2000" :required="decision==='changes_requested'" @input="$emit('update:notes',$event.target.value)"></textarea></label>
  </section>`
};

export const ListeningReviewSummary={
  props:{review:Object},methods:{listeningReviewStatus},
  template:`<section aria-label="Vigencia de la opinión guardada"><p>{{ listeningReviewStatus(review) }}</p>
    <template v-if="review"><p>Decisión registrada: {{ review.decision==='accepted' ? 'Corresponde a mi idea' : review.decision==='changes_requested' ? 'Necesita cambios' : 'Sin decisión reconocida' }}. No aprueba sample ni canción final.</p>
    <p>{{ review.context_message }}</p><p v-if="review.notes">Tus notas: {{ review.notes }}</p></template>
  </section>`
};
